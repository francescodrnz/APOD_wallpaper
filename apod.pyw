import subprocess
import importlib
import os
import ctypes
import random
import json
import sys
from datetime import datetime, timedelta, timezone
import winreg
from pathlib import Path
import textwrap

# --- GESTIONE DIPENDENZE ---
def install_dependencies():
    required_packages = {"requests": "requests", "pillow": "PIL"}
    for pip_name, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            try:
                # Installazione silenziosa
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass

install_dependencies()

import requests
from PIL import Image, ImageFilter, ImageEnhance

# --- COSTANTI & CONFIGURAZIONE ---
CONFIG_FILE = Path(__file__).parent / "config.json"
MAX_RETRIES = 3
TIMEOUT = 10
START_DATE = datetime(1995, 6, 16)

def show_popup(title, message, style=0x40):
    """
    Mostra un popup nativo e ritorna l'ID del tasto premuto.
    style: combina icona e tasti (es. 0x04=YesNo, 0x40=Info)
    Return: 6 (Yes), 7 (No), 1 (OK)
    """
    return ctypes.windll.user32.MessageBoxW(0, message, title, style | 0x1000)

def load_config():
    default_config = {
        "NASA_API_KEY": "DEMO_KEY",
        "UNSPLASH_API_KEY": "your_unsplash_key_here"
    }
    
    if not CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(default_config, f, indent=4)
            
            # Popup con scelta Sì/No (0x04 = MB_YESNO)
            response = show_popup(
                "Configurazione Richiesta", 
                f"Il file config.json è stato creato.\n\nVuoi aprirlo ora per inserire le tue chiavi?",
                0x04 | 0x40 
            )
            
            # Se l'utente preme Sì (ID 6), apre il file
            if response == 6:
                os.startfile(CONFIG_FILE)
                
            sys.exit(0)
        except Exception as e:
            show_popup("Errore Critico", f"Impossibile creare config.json: {e}", 0x10)
            return default_config

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        
        nasa_key = config.get("NASA_API_KEY", "")
        unsplash_key = config.get("UNSPLASH_API_KEY", "")
        
        if "INSERISCI" in nasa_key or "INSERISCI" in unsplash_key:
            show_popup("Configurazione Incompleta", "Chiavi API non impostate in config.json.", 0x30)
            
        return config
    except Exception as e:
        show_popup("Errore Config", f"File config.json corrotto: {e}", 0x10)
        return default_config

config = load_config()
NASA_API_KEY = config.get("NASA_API_KEY", "")
UNSPLASH_API_KEY = config.get("UNSPLASH_API_KEY", "")

# --- CORE FUNCTIONS ---

def random_date(start_date, end_date):
    delta = (end_date - start_date).days
    random_days = random.randint(0, delta)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

def get_current_wallpaper():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_READ) as key:
            wallpaper_path = winreg.QueryValueEx(key, "Wallpaper")[0]
            return Path(wallpaper_path) if wallpaper_path else None
    except:
        return None

def smart_resize_wallpaper(image_path):
    try:
        user32 = ctypes.windll.user32
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        target_ratio = screen_w / screen_h
        
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            orig_w, orig_h = img.size
            img_ratio = orig_w / orig_h
            
            if abs(img_ratio - target_ratio) < 0.05:
                return

            base_width = max(screen_w, orig_w)
            base_height = int(base_width / target_ratio)
            canvas = Image.new('RGB', (base_width, base_height))

            bg_layer = img.copy()
            scale = max(base_width / orig_w, base_height / orig_h)
            bg_w, bg_h = int(orig_w * scale), int(orig_h * scale)
            bg_layer = bg_layer.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
            
            left = (bg_w - base_width) // 2
            top = (bg_h - base_height) // 2
            bg_layer = bg_layer.crop((left, top, left + base_width, top + base_height))
            bg_layer = bg_layer.filter(ImageFilter.GaussianBlur(radius=50))
            bg_layer = ImageEnhance.Brightness(bg_layer).enhance(0.6)
            
            scale_fit = min(base_width / orig_w, base_height / orig_h)
            fg_w, fg_h = int(orig_w * scale_fit), int(orig_h * scale_fit)
            fg_layer = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)
            
            pos_x = (base_width - fg_w) // 2
            pos_y = (base_height - fg_h) // 2
            
            canvas.paste(bg_layer, (0, 0))
            canvas.paste(fg_layer, (pos_x, pos_y))
            canvas.save(image_path, quality=95)
    except Exception as e:
        print(f"[ERRORE] Resize: {e}")

def update_windows_accent(image_path):
    try:
        with Image.open(image_path) as img:
            img = img.resize((100, 100)).convert("RGB")
            colors = img.getcolors(10000)
            if not colors: return False
            
            colors.sort(key=lambda x: x[0], reverse=True)
            r, g, b = colors[0][1]

            if (r + g + b) < 80:
                r, g, b = 40, 40, 40

            accent_color_dword = (0 << 24) | (b << 16) | (g << 8) | r
            
            key_path = r"Software\Microsoft\Windows\DWM"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "AccentColor", 0, winreg.REG_DWORD, accent_color_dword)
                winreg.SetValueEx(key, "ColorPrevalence", 0, winreg.REG_DWORD, 1)
                
            ctypes.windll.user32.SystemParametersInfoW(20, 0, str(image_path), 3)
            return True
    except:
        return False

# --- API FUNCTIONS ---

def get_apod_data(date=None):
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&hd=True"
    if date: url += f"&date={date}"
    try:
        res = requests.get(url, timeout=TIMEOUT)
        res.raise_for_status()
        data = res.json()
        if data.get("media_type") != "image": return None
        return {
            "url": data["hdurl"], "title": data.get("title", "APOD"),
            "description": data.get("explanation", ""), "date": data.get("date"),
            "source": "NASA APOD"
        }
    except: return None

def get_unsplash_image():
    themes = ["nature", "landscape", "space", "mountain", "ocean", "sky", "forest", "desert", "aurora", "milkyway"]
    theme = random.choice(themes)
    try:
        if UNSPLASH_API_KEY and "INSERISCI" not in UNSPLASH_API_KEY:
            url = f"https://api.unsplash.com/photos/random?query={theme}&orientation=landscape"
            headers = {"Authorization": f"Client-ID {UNSPLASH_API_KEY}"}
            res = requests.get(url, headers=headers, timeout=TIMEOUT)
            res.raise_for_status()
            data = res.json()
            return {
                "url": data["urls"]["raw"] + "&w=2560&h=1440&fit=max&q=85",
                "title": data.get("description") or f"Unsplash {theme}",
                "description": f"Photo by {data['user']['name']}", "date": datetime.now().strftime('%Y-%m-%d'),
                "source": "Unsplash"
            }
        else:
            final_url = f"https://source.unsplash.com/2560x1440/?{theme}"
            res = requests.get(final_url, timeout=TIMEOUT)
            if res.status_code == 200:
                return {
                    "url": res.url, "title": f"Unsplash {theme}",
                    "description": "Random Unsplash Image", "date": datetime.now().strftime('%Y-%m-%d'),
                    "source": "Unsplash (Public)"
                }
    except: pass
    return None

def get_nasa_image_library():
    queries = ["galaxy", "nebula", "planet", "earth from space", "space station", "mars", "moon", "jupiter", "saturn"]
    try:
        res = requests.get(f"https://images-api.nasa.gov/search?q={random.choice(queries)}&media_type=image&year_start=2015", timeout=TIMEOUT)
        res.raise_for_status()
        items = res.json().get("collection", {}).get("items", [])
        if not items: return None
        
        item = random.choice(items[:30])
        
        asset_res = requests.get(item["href"], timeout=TIMEOUT)
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
            "source": "NASA Library"
        }
    except: return None

# --- MAIN LOOP ---

def download_image(url, save_path):
    try:
        res = requests.get(url, stream=True, timeout=20)
        res.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in res.iter_content(8192): f.write(chunk)
        with Image.open(save_path) as img: img.verify()
        return True
    except:
        if save_path.exists(): save_path.unlink()
        return False

def set_wallpaper(path):
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, str(path), 3)
        return True
    except: return False

def cleanup(folder, current, new_img, new_txt):
    keep = {new_img, new_txt}
    if current and current.parent == folder:
        keep.add(current)
        keep.add(current.with_suffix('.txt'))
    
    files = sorted(folder.glob("wallpaper_*"), key=lambda x: x.stat().st_mtime, reverse=True)
    for f in files:
        if f not in keep and len(keep) < 6:
             keep.add(f)
        elif f not in keep:
            try: f.unlink()
            except: pass

def main():
    folder = Path(__file__).parent / "apod_images"
    folder.mkdir(exist_ok=True)
    current_wp = get_current_wallpaper()
    
    apis = [get_apod_data, get_unsplash_image, get_nasa_image_library]
    random.shuffle(apis)
    
    img_data = None
    for api in apis:
        for i in range(MAX_RETRIES):
            try:
                if api == get_apod_data:
                    date = random_date(START_DATE, datetime.now() - timedelta(days=1)) if i > 0 else None
                    res = api(date)
                else:
                    res = api()
                
                if res:
                    img_data = res
                    break
            except: pass
        if img_data: break
    
    if not img_data: return

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    src = img_data['source'].lower().replace(' ', '_')
    img_path = folder / f"wallpaper_{src}_{ts}.jpg"
    txt_path = folder / f"wallpaper_{src}_{ts}.txt"
    
    if download_image(img_data['url'], img_path):
        smart_resize_wallpaper(img_path)
        
        if set_wallpaper(img_path):
            update_windows_accent(img_path)
            
            try:
                desc = textwrap.fill(img_data['description'], 80)
                txt_path.write_text(f"Title: {img_data['title']}\nDate: {img_data['date']}\nSource: {img_data['source']}\n\n{desc}", encoding='utf-8')
            except: pass
            
            cleanup(folder, current_wp, img_path, txt_path)

if __name__ == "__main__":
    main()