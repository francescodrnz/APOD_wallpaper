import subprocess
import os
import io
import ctypes
import random
import re
import html
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# comune installa requests e pillow se mancano, quindi va importato prima di loro
from comune import (IS_WINDOWS, BG_PROCESS, IMAGES_DIR, get_current_wallpaper, set_wallpaper,
                    update_windows_accent, load_stats, is_excluded, write_info, read_info, load_config, unsplash_key)

import requests
from PIL import Image, ImageFilter, ImageEnhance

# --- COSTANTI & CONFIGURAZIONE ---
MAX_RETRIES = 3
TIMEOUT = 10
START_DATE = datetime(1995, 6, 16)
# Le immagini con il lato lungo sotto questa soglia si vedrebbero sgranate a tutto schermo
MIN_LATO_LUNGO = 1280
# Sfondo preparato in anticipo dal processo --prefetch, pronto per il prossimo cambio
PREFETCH_DIR = IMAGES_DIR / "prossimo"

# Una sola sessione: riusa le connessioni HTTPS invece di rifare ogni volta l'handshake
SESSION = requests.Session()

config = load_config()
UNSPLASH_API_KEY = unsplash_key(config)

# --- CORE FUNCTIONS ---

def random_date(start_date, end_date):
    delta = (end_date - start_date).days
    random_days = random.randint(0, delta)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

def screen_size():
    if not IS_WINDOWS:
        # Linux. Su X11 xrandr da' la risoluzione in uso del monitor primario (o del primo collegato).
        # Su Wayland xrandr puo' rispondere con una misura scalata, quindi si salta.
        if os.environ.get("XDG_SESSION_TYPE") != "wayland":
            try:
                out = subprocess.run(["xrandr", "--current"], capture_output=True, text=True, timeout=10).stdout
                found = (re.search(r" connected primary (\d+)x(\d+)\+", out)
                         or re.search(r" connected (\d+)x(\d+)\+", out))
                if found:
                    return int(found.group(1)), int(found.group(2))
            except: pass
        # Altrimenti la risoluzione nativa del primo schermo collegato, letta dal kernel
        # (vale su qualsiasi distribuzione e anche su Wayland; la prima modalita' e' quella preferita)
        try:
            for status in sorted(Path("/sys/class/drm").glob("card*-*/status")):
                if status.read_text().strip() == "connected":
                    found = re.match(r"(\d+)x(\d+)", (status.parent / "modes").read_text())
                    if found:
                        return int(found.group(1)), int(found.group(2))
        except: pass
        return 1920, 1080
    # Risoluzione fisica. GetSystemMetrics in un processo non DPI-aware restituisce
    # quella scalata (es. 1536x864 invece di 1920x1080 con il ridimensionamento al 125%).
    user32 = ctypes.windll.user32
    try:
        hdc = user32.GetDC(0)
        try:
            w = ctypes.windll.gdi32.GetDeviceCaps(hdc, 118)  # DESKTOPHORZRES
            h = ctypes.windll.gdi32.GetDeviceCaps(hdc, 117)  # DESKTOPVERTRES
        finally:
            user32.ReleaseDC(0, hdc)
        if w > 0 and h > 0:
            return w, h
    except:
        pass
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

def fetch_image(url, screen):
    # Scarica in memoria e restituisce l'immagine RGB, oppure None se non e' valida o e' troppo piccola
    try:
        res = SESSION.get(url, timeout=20)
        res.raise_for_status()
        img = Image.open(io.BytesIO(res.content))
        if max(img.size) < MIN_LATO_LUNGO:
            return None
        # Solo per i JPEG: decodifica direttamente a 1/2, 1/4 o 1/8, senza scendere sotto lo schermo
        img.draft("RGB", screen)
        return img.convert("RGB")
    except:
        return None

def smart_resize_wallpaper(img, screen):
    # Restituisce l'immagine adattata allo schermo, oppure None in caso di errore
    try:
        screen_w, screen_h = screen
        orig_w, orig_h = img.size

        # Proporzioni gia' giuste: niente sfocatura, basta non tenerla piu' grande dello schermo
        if abs(orig_w / orig_h - screen_w / screen_h) < 0.05:
            scale = max(screen_w / orig_w, screen_h / orig_h)
            if scale >= 1:
                return img
            return img.resize((round(orig_w * scale), round(orig_h * scale)), Image.Resampling.LANCZOS)

        canvas = Image.new('RGB', (screen_w, screen_h))

        # Estraiamo direttamente il riquadro centrale proporzionale allo schermo
        scale = max(screen_w / orig_w, screen_h / orig_h)
        crop_w, crop_h = int(screen_w / scale), int(screen_h / scale)
        left = (orig_w - crop_w) // 2
        top = (orig_h - crop_h) // 2
        bg_layer = img.crop((left, top, left + crop_w, top + crop_h))

        # Riduciamo drasticamente la risoluzione per velocizzare il GaussianBlur
        tiny_w, tiny_h = max(1, screen_w // 10), max(1, screen_h // 10)
        bg_layer = bg_layer.resize((tiny_w, tiny_h), Image.Resampling.BILINEAR)
        bg_layer = bg_layer.filter(ImageFilter.GaussianBlur(radius=5))

        # Riportiamo a grandezza schermo
        bg_layer = bg_layer.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
        bg_layer = ImageEnhance.Brightness(bg_layer).enhance(0.6)

        scale_fit = min(screen_w / orig_w, screen_h / orig_h)
        fg_w, fg_h = int(orig_w * scale_fit), int(orig_h * scale_fit)
        fg_layer = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)

        canvas.paste(bg_layer, (0, 0))
        canvas.paste(fg_layer, ((screen_w - fg_w) // 2, (screen_h - fg_h) // 2))
        return canvas
    except:
        return None

# --- API FUNCTIONS ---

def get_valid_categories(source_list):
    stats = load_stats()
    return [c for c in source_list if not is_excluded(stats.get(c, {}))]

def _strip_tags(fragment):
    text = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()

def get_apod_data(date=None):
    # APOD e' migrato su science.nasa.gov: la vecchia api.nasa.gov/planetary/apod restituisce
    # il logo NASA. Nuova API (APOD Basic JSON), le date sono nel formato legacy YYMMDD.
    url = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"
    url += f"/{datetime.strptime(date, '%Y-%m-%d'):%y%m%d}" if date else "?per_page=1"
    try:
        res = SESSION.get(url, timeout=TIMEOUT)
        res.raise_for_status()
        data = res.json()
        if isinstance(data, list): data = data[0]
        if data.get("media_type") != "image" or not data.get("hdurl"): return None
        # Il percorso content/dam senza parametri restituisce l'originale a piena risoluzione
        img_url = data["hdurl"].split("?")[0].replace("/dynamicimage/assets/", "/content/dam/")
        # Alcune date vecchie hanno un'immagine segnaposto generica al posto della foto APOD
        if "/apod/" not in img_url: return None
        description = re.sub(r"^(Explanation\s*:\s*)+", "", _strip_tags(data.get("explanation", "")))
        return {
            "url": img_url, "title": _strip_tags(data.get("title", "APOD")),
            "description": description, "date": data.get("date"),
            "source": "NASA APOD"
        }
    except: return None

def get_unsplash_image():
    # Fonte opzionale: senza chiave viene saltata (il vecchio source.unsplash.com e' stato chiuso)
    if not UNSPLASH_API_KEY: return None
    themes = config.get("unsplash_categories", ["space"])
    valid_themes = get_valid_categories(themes)
    if not valid_themes: return None
    theme = random.choice(valid_themes)
    try:
        url = f"https://api.unsplash.com/photos/random?query={theme}&orientation=landscape"
        headers = {"Authorization": f"Client-ID {UNSPLASH_API_KEY}"}
        res = SESSION.get(url, headers=headers, timeout=TIMEOUT)
        res.raise_for_status()
        data = res.json()

        # Unsplash spesso ha 'alt_description' o 'description'
        raw_title = data.get("alt_description") or data.get("description") or f"Unsplash {theme}"
        raw_desc = data.get("description") or data.get("alt_description") or "Nessuna descrizione disponibile."

        # Costruiamo i metadati
        full_desc = f"Photo by {data.get('user', {}).get('name', 'Unknown')}.\n{raw_desc}"
        created_date = data.get("created_at", datetime.now().strftime('%Y-%m-%d'))[:10]

        # Unsplash ridimensiona lato server: chiediamo direttamente la risoluzione dello schermo
        w, h = screen_size()
        return {
            "url": data["urls"]["raw"] + f"&w={w}&h={h}&fit=max&q=85",
            "title": raw_title.capitalize(),
            "description": full_desc,
            "date": created_date,
            "source": "Unsplash", "category": theme
        }
    except: return None

def get_nasa_image_library():
    queries = config.get("nasa_categories", ["galaxy"])
    valid_queries = get_valid_categories(queries)
    if not valid_queries: return None
    query = random.choice(valid_queries)
    try:
        base_url = f"https://images-api.nasa.gov/search?q={query}&media_type=image&year_start=2010"
        res = SESSION.get(base_url, timeout=TIMEOUT)
        res.raise_for_status()
        data = res.json().get("collection", {})
        total_hits = data.get("metadata", {}).get("total_hits", 0)
        items = data.get("items", [])

        # Se ci sono più di 100 risultati, peschiamo da una pagina casuale (max 10 pagine per mantenere pertinenza)
        if total_hits > 100:
            max_pages = min(10, (total_hits // 100) + 1)
            random_page = random.randint(1, max_pages)
            if random_page > 1:
                try:
                    res2 = SESSION.get(f"{base_url}&page={random_page}", timeout=TIMEOUT)
                    if res2.status_code == 200:
                        new_items = res2.json().get("collection", {}).get("items", [])
                        if new_items: items = new_items
                except: pass

        if not items: return None

        item = random.choice(items)

        asset_res = SESSION.get(item["href"], timeout=TIMEOUT)
        asset_res.raise_for_status()
        asset_data = asset_res.json()

        best_image = None
        image_urls = [url for url in asset_data if url.lower().endswith(('.jpg', '.jpeg', '.png'))]

        for priority in ['~orig', '~large', '~medium']:
            for url in image_urls:
                if priority in url.lower():
                    best_image = url
                    break
            if best_image: break

        if not best_image and image_urls:
            best_image = image_urls[0]

        if not best_image: return None

        meta = item["data"][0]
        return {
            "url": best_image, "title": meta.get("title"),
            "description": meta.get("description", "")[:500], "date": meta.get("date_created")[:10],
            "source": "NASA Library", "category": query
        }
    except: return None

# --- MAIN LOOP ---

def recent_images():
    # (titolo, data) degli sfondi in cache e di quello preparato in anticipo
    files = list(IMAGES_DIR.glob("wallpaper_*.txt")) + list(PREFETCH_DIR.glob("wallpaper_*.txt"))
    return {(info["title"], info["date"]) for info in map(read_info, files)}

def find_image(screen):
    # Prova le fonti in ordine casuale; un download fallito, un'immagine troppo piccola o gia' in cache
    # contano come tentativo fallito. Restituisce (metadati, immagine adattata) o (None, None).
    apis = [get_apod_data, get_unsplash_image, get_nasa_image_library]
    random.shuffle(apis)
    # Senza questo controllo l'APOD di oggi tornerebbe a ogni cambio, anche nel prefetch subito dopo lo sfondo
    seen = recent_images()

    for api in apis:
        for i in range(MAX_RETRIES):
            try:
                if api == get_apod_data:
                    date = random_date(START_DATE, datetime.now() - timedelta(days=1)) if i > 0 else None
                    data = api(date)
                else:
                    data = api()
                if not data: continue
                if (str(data['title']).strip(), str(data['date']).strip()) in seen: continue

                img = fetch_image(data['url'], screen)
                wallpaper = smart_resize_wallpaper(img, screen) if img else None
                if wallpaper: return data, wallpaper
            except: pass
    return None, None

def prepare_image(folder):
    # Cerca, scarica e adatta un'immagine, poi la salva in folder insieme al .txt.
    # Il .jpg viene scritto per ultimo e con un rename: se esiste, la coppia e' completa.
    data, wallpaper = find_image(screen_size())
    if not data: return None

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    src = data['source'].lower().replace(' ', '_')
    img_path = folder / f"wallpaper_{src}_{ts}.jpg"
    txt_path = img_path.with_suffix('.txt')
    tmp_path = img_path.with_suffix('.tmp')

    try: write_info(txt_path, data)
    except: pass
    try:
        wallpaper.save(tmp_path, "JPEG", quality=95)
        os.replace(tmp_path, img_path)
        return img_path
    except:
        for p in (tmp_path, txt_path):
            try: p.unlink()
            except: pass
        return None

def _mtime(path):
    try: return path.stat().st_mtime
    except: return 0

def take_prefetched():
    # Sposta nello storico lo sfondo preparato in anticipo, se c'e'
    for jpg in sorted(PREFETCH_DIR.glob("wallpaper_*.jpg"), key=_mtime):
        dest = IMAGES_DIR / jpg.name
        try:
            os.replace(jpg, dest)
        except OSError:
            continue  # preso nel frattempo da un altro processo
        try: os.replace(jpg.with_suffix('.txt'), dest.with_suffix('.txt'))
        except OSError: pass
        # Lo storico e' ordinato per data di modifica: conta il momento in cui diventa sfondo
        for p in (dest, dest.with_suffix('.txt')):
            try: os.utime(p)
            except OSError: pass
        return dest
    return None

def start_prefetch():
    try:
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--prefetch"],
                         cwd=str(IMAGES_DIR.parent), **BG_PROCESS)
    except: pass

def prefetch():
    # Elimina gli avanzi di prefetch interrotti (file temporanei, .txt senza immagine)
    for f in PREFETCH_DIR.iterdir():
        orphan = f.suffix == '.tmp' or (f.suffix == '.txt' and not f.with_suffix('.jpg').exists())
        if orphan and time.time() - _mtime(f) > 3600:
            try: f.unlink()
            except: pass

    if any(PREFETCH_DIR.glob("wallpaper_*.jpg")): return
    prepare_image(PREFETCH_DIR)

def cleanup(folder, current, new_img, new_txt):
    keep = {new_img, new_txt}
    if current and current.parent == folder:
        keep.add(current)
        keep.add(current.with_suffix('.txt'))

    files = sorted(folder.glob("wallpaper_*"), key=lambda x: x.stat().st_mtime, reverse=True)
    for f in files:
        if f not in keep and len(keep) < 12:
             keep.add(f)
        elif f not in keep:
            try: f.unlink()
            except: pass

def main():
    PREFETCH_DIR.mkdir(parents=True, exist_ok=True)

    if "--prefetch" in sys.argv:
        prefetch()
        return

    current_wp = get_current_wallpaper()
    img_path = take_prefetched() or prepare_image(IMAGES_DIR)
    # Il prossimo sfondo si prepara in un processo separato, cosi' chi aspetta questo non attende
    start_prefetch()
    if not img_path: return

    if set_wallpaper(img_path):
        update_windows_accent(img_path)
        cleanup(IMAGES_DIR, current_wp, img_path, img_path.with_suffix('.txt'))

if __name__ == "__main__":
    main()
