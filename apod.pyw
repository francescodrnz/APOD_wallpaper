import subprocess
import importlib
import os
import ctypes
import random
from datetime import datetime, timedelta, UTC
import winreg
from pathlib import Path
import textwrap

# Controlla e installa le librerie mancanti
def install_dependencies():
    required_packages = {"requests": "requests", "pillow": "PIL"}
    for pip_name, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            print(f"[INFO] Installazione di {pip_name}...")
            subprocess.check_call(["python", "-m", "pip", "install", pip_name])

install_dependencies()

import requests
from PIL import Image

# Costanti
NASA_API_KEY = "uSEGw3fuem0zi1Ks76NsilpRUtxXcTi1lEseL8P2"
UNSPLASH_API_KEY = "dNenSdAjlYgw74XkzItswjs46jqWs8T0XcwSV5ocKDU"
START_DATE = datetime(1995, 6, 16)
MAX_RETRIES = 3
TIMEOUT = 10

def random_date(start_date, end_date):
    """Genera una data casuale nel range specificato."""
    delta = (end_date - start_date).days
    random_days = random.randint(0, delta)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

def get_current_wallpaper():
    """Legge il percorso dello sfondo corrente dal registro."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Control Panel\Desktop",
            0,
            winreg.KEY_READ
        ) as key:
            wallpaper_path = winreg.QueryValueEx(key, "Wallpaper")[0]
            return Path(wallpaper_path) if wallpaper_path else None
    except Exception as e:
        print(f"[WARN] Impossibile leggere wallpaper corrente: {e}")
        return None

def get_apod_data(date=None):
    """Ottiene i dati APOD da NASA API."""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&hd=True"
    if date:
        url += f"&date={date}"
    
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # Verifica immediata se è un'immagine valida
        if data.get("media_type") != "image" or "hdurl" not in data:
            return None
        
        return {
            "url": data["hdurl"],
            "title": data.get("title", "NASA APOD"),
            "description": data.get("explanation", ""),
            "date": data.get("date", "unknown"),
            "source": "NASA APOD"
        }
    except requests.exceptions.RequestException:
        return None

def get_unsplash_image():
    """Ottiene un'immagine casuale da Unsplash."""
    themes = ["nature", "landscape", "space", "mountain", "ocean", "sky", "forest", "desert", "aurora", "milkyway"]
    theme = random.choice(themes)
    
    try:
        if UNSPLASH_API_KEY:
            url = f"https://api.unsplash.com/photos/random?query={theme}&orientation=landscape"
            headers = {"Authorization": f"Client-ID {UNSPLASH_API_KEY}"}
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            return {
                "url": data["urls"]["raw"] + "&w=2560&h=1440&fit=max&q=85",
                "title": data.get("description") or data.get("alt_description") or f"Unsplash - {theme.capitalize()}",
                "description": data.get("description") or f"Photo by {data['user']['name']} on Unsplash",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "source": "Unsplash",
                "query": theme
            }
        else:
            url = f"https://source.unsplash.com/1920x1080/?{theme}"
            response = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            
            return {
                "url": response.url,
                "title": f"Unsplash - {theme.capitalize()}",
                "description": f"Random {theme} photo from Unsplash",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "source": "Unsplash",
                "query": theme
            }
        
    except Exception:
        return None

def get_nasa_image_library():
    """Ottiene un'immagine dalla NASA Image Library."""
    queries = ["galaxy", "nebula", "planet", "earth from space", "space station", "astronaut", "mars", "moon", "jupiter", "saturn"]
    query = random.choice(queries)
    
    try:
        search_url = f"https://images-api.nasa.gov/search?q={query}&media_type=image&year_start=2015"
        response = requests.get(search_url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("collection", {}).get("items", [])
        if not items:
            return None
        
        # Prendi dalle prime 30 per qualità migliore
        item = random.choice(items[:30])
        
        asset_url = item["href"]
        asset_response = requests.get(asset_url, timeout=TIMEOUT)
        asset_response.raise_for_status()
        asset_data = asset_response.json()
        
        # Cerca l'immagine più grande disponibile
        image_urls = [url for url in asset_data if url.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not image_urls:
            return None
        
        # Priorità: orig > large > medium
        best_image = None
        for priority in ['~orig', '~large', '~medium']:
            for url in image_urls:
                if priority in url.lower():
                    best_image = url
                    break
            if best_image:
                break
        
        if not best_image:
            best_image = image_urls[0]
        
        metadata = item["data"][0]
        return {
            "url": best_image,
            "title": metadata.get("title", "NASA Image"),
            "description": metadata.get("description", "")[:500],
            "date": metadata.get("date_created", datetime.now().strftime('%Y-%m-%d'))[:10],
            "source": "NASA Image Library",
            "query": query
        }
        
    except Exception:
        return None

def try_api_with_retries(api_func, max_retries=MAX_RETRIES):
    """Prova un'API con retry automatici."""
    api_name = api_func.__name__.replace('get_', '').replace('_', ' ').title()
    
    for attempt in range(1, max_retries + 1):
        # Per APOD, usa date casuali dopo il primo tentativo
        if api_func == get_apod_data:
            if attempt == 1:
                image_data = api_func()  # Oggi
            else:
                end_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
                date = random_date(START_DATE, end_date)
                image_data = api_func(date)
        else:
            image_data = api_func()
        
        if image_data:
            print(f"[SUCCESS] {api_name} → immagine ottenuta (tentativo {attempt}/{max_retries})")
            return image_data
    
    print(f"[FAIL] {api_name} → tutti i {max_retries} tentativi falliti")
    return None

def download_image(url, save_path):
    """Download ottimizzato dell'immagine con validazione."""
    try:
        response = requests.get(url, stream=True, timeout=20)
        response.raise_for_status()
        
        # Verifica che sia un'immagine
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type:
            print(f"[WARN] Content-Type non valido: {content_type}")
            return False
        
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        
        # Valida l'immagine immediatamente
        try:
            with Image.open(save_path) as img:
                img.verify()
                # Riapri per ottenere dimensioni (verify() chiude il file)
                with Image.open(save_path) as img2:
                    width, height = img2.size
                    print(f"[INFO] Immagine valida: {width}x{height} - {save_path.name}")
        except Exception as e:
            print(f"[ERRORE] Immagine corrotta: {e}")
            save_path.unlink(missing_ok=True)
            return False
        
        return True
    except Exception as e:
        print(f"[ERRORE] Download fallito: {e}")
        if save_path.exists():
            save_path.unlink(missing_ok=True)
        return False

def set_wallpaper(image_path):
    """Imposta lo sfondo su Windows."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Control Panel\Desktop",
            0,
            winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, "Wallpaper", 0, winreg.REG_SZ, str(image_path))
        
        SPI_SETDESKWALLPAPER = 20
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, str(image_path),
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        
        print("[INFO] Wallpaper applicato ✅")
        return True
    except Exception as e:
        print(f"[ERRORE] Impossibile impostare wallpaper: {e}")
        return False

def cleanup_old_files(folder_path, current_wallpaper, new_image_path, new_txt_path):
    """Pulisce i vecchi file preservando quello in uso e gli ultimi N."""
    files_to_keep = {new_image_path, new_txt_path}
    
    # Preserva wallpaper corrente se nella nostra cartella
    if current_wallpaper and current_wallpaper.parent == folder_path:
        files_to_keep.add(current_wallpaper)
        # Trova e preserva anche il suo .txt associato
        txt_equivalent = current_wallpaper.with_suffix('.txt')
        if txt_equivalent.exists():
            files_to_keep.add(txt_equivalent)
    
    # Ottieni tutti i file wallpaper ordinati per data (più recenti prima)
    all_files = sorted(
        folder_path.glob("wallpaper_*"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    # Mantieni gli ultimi 3 wallpaper (oltre a quello corrente)
    keep_recent = 3
    kept_recent = 0
    for file in all_files:
        if file not in files_to_keep and kept_recent < keep_recent:
            files_to_keep.add(file)
            kept_recent += 1
    
    # Elimina i vecchi
    deleted_count = 0
    for old_file in all_files:
        if old_file not in files_to_keep:
            try:
                old_file.unlink()
                deleted_count += 1
            except Exception:
                pass
    
    if deleted_count > 0:
        print(f"[INFO] Puliti {deleted_count} file vecchi (mantenuti ultimi {keep_recent})")

def main():
    print("[INFO] Avvio script wallpaper...")
    
    # Setup directory
    folder_path = Path(__file__).parent / "apod_images"
    folder_path.mkdir(exist_ok=True)
    
    # Leggi quale wallpaper è attualmente impostato
    current_wallpaper = get_current_wallpaper()
    if current_wallpaper:
        print(f"[INFO] Wallpaper corrente: {current_wallpaper.name}")
    
    # Lista di tutte le API disponibili
    all_apis = [get_apod_data, get_unsplash_image, get_nasa_image_library]
    
    # Mescola l'ordine casualmente
    random.shuffle(all_apis)
    api_names = [f.__name__.replace('get_', '').replace('_data', '').replace('_image', '').replace('_library', '').upper() for f in all_apis]
    print(f"[INFO] Ordine API: {' → '.join(api_names)}\n")
    
    image_data = None
    
    # Prova ogni API in ordine casuale con retry
    for api_func in all_apis:
        image_data = try_api_with_retries(api_func)
        
        if image_data:
            break
        print()  # Spaziatura tra API diverse
    
    # Se tutte le API falliscono
    if not image_data:
        print("[ERRORE CRITICO] Impossibile ottenere alcuna immagine da tutte le API disponibili.")
        return
    
    # Procedi con download e impostazione
    print(f"[INFO] Fonte: {image_data['source']}")
    print(f"[INFO] Titolo: {image_data['title'][:60]}{'...' if len(image_data['title']) > 60 else ''}")
    
    # Crea nome file univoco
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    source_prefix = image_data['source'].lower().replace(' ', '_')
    image_path = folder_path / f"wallpaper_{source_prefix}_{timestamp}.jpg"
    txt_path = folder_path / f"wallpaper_{source_prefix}_{timestamp}.txt"
    
    # Download e validazione immagine
    if not download_image(image_data["url"], image_path):
        print("[ERRORE] Download o validazione immagine falliti")
        return
    
    # Imposta wallpaper
    if set_wallpaper(image_path):
        print("[SUCCESS] ✅ Wallpaper cambiato con successo!\n")
        
        # Salva informazioni
        try:
            wrapped_description = textwrap.fill(
                image_data['description'], 
                width=80,
                break_long_words=False,
                break_on_hyphens=False
            )
            txt_path.write_text(
                f"Fonte: {image_data['source']}\n"
                f"Titolo: {image_data['title']}\n"
                f"Data: {image_data['date']}\n"
                f"File: {image_path.name}\n\n"
                f"{wrapped_description}",
                encoding='utf-8'
            )
        except Exception:
            pass
        
        # Pulisci vecchi file
        cleanup_old_files(folder_path, current_wallpaper, image_path, txt_path)
    else:
        print("[ERRORE] Impossibile impostare il wallpaper")
        image_path.unlink(missing_ok=True)
        txt_path.unlink(missing_ok=True)

if __name__ == "__main__":
    main()