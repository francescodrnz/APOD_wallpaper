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
API_KEY = "uSEGw3fuem0zi1Ks76NsilpRUtxXcTi1lEseL8P2" # "DEMO_KEY" # INSERIRE LA PROPRIA API KEY, OTTENIBILE DA https://api.nasa.gov/
START_DATE = datetime(1995, 6, 16)
MAX_RETRIES = 5
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
    url = f"https://api.nasa.gov/planetary/apod?api_key={API_KEY}&hd=True"
    if date:
        url += f"&date={date}"
        print(f"[INFO] Richiesta APOD per {date}")
    else:
        print("[INFO] Richiesta APOD per oggi")
    
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # Verifica immediata se è un'immagine valida
        if data.get("media_type") != "image" or "hdurl" not in data:
            print(f"[WARN] APOD non valido (media_type: {data.get('media_type')})")
            return None
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"[ERRORE] Richiesta fallita: {e}")
        return None

def download_image(url, save_path):
    """Download ottimizzato dell'immagine."""
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        
        print(f"[INFO] Immagine salvata: {save_path}")
        return True
    except Exception as e:
        print(f"[ERRORE] Download fallito: {e}")
        return False

def set_wallpaper(image_path):
    """Imposta lo sfondo su Windows."""
    try:
        # Aggiorna registro
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Control Panel\Desktop",
            0,
            winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, "Wallpaper", 0, winreg.REG_SZ, str(image_path))
        
        # Applica wallpaper
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
    """Pulisce i vecchi file APOD, preservando quello attualmente in uso."""
    files_to_keep = {new_image_path, new_txt_path}
    
    # Se lo sfondo corrente è nella nostra cartella, preservalo temporaneamente
    if current_wallpaper and current_wallpaper.parent == folder_path:
        files_to_keep.add(current_wallpaper)
        print(f"[INFO] Preservo wallpaper corrente: {current_wallpaper.name}")
    
    deleted_count = 0
    for old_file in folder_path.glob("apod_*"):
        if old_file not in files_to_keep:
            try:
                old_file.unlink()
                deleted_count += 1
                print(f"[INFO] Eliminato: {old_file.name}")
            except Exception as e:
                print(f"[WARN] Impossibile eliminare {old_file.name}: {e}")
    
    if deleted_count > 0:
        print(f"[INFO] Puliti {deleted_count} file vecchi")

def main():
    print("[INFO] Avvio script APOD wallpaper...")
    
    # Setup directory
    folder_path = Path(__file__).parent / "apod_images"
    folder_path.mkdir(exist_ok=True)
    
    # Leggi quale wallpaper è attualmente impostato
    current_wallpaper = get_current_wallpaper()
    if current_wallpaper:
        print(f"[INFO] Wallpaper corrente: {current_wallpaper.name}")
    
    # Calcola range date
    end_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
    
    # Tenta di ottenere un'immagine valida
    for attempt in range(1, MAX_RETRIES + 1):
        date = random_date(START_DATE, end_date) # if attempt > 0 else None
        data = get_apod_data(date)
        
        if data and "hdurl" in data:
            print(f"[INFO] Titolo: {data.get('title', 'Sconosciuto')}")
            
            # Crea nome file con la data
            apod_date = data.get('date', 'unknown')
            image_path = folder_path / f"apod_{apod_date}.jpg"
            txt_path = folder_path / f"apod_{apod_date}.txt"
            
            # Download e imposta wallpaper
            if download_image(data["hdurl"], image_path):
                # Validazione base immagine
                try:
                    with Image.open(image_path) as img:
                        img.verify()
                except Exception as e:
                    print(f"[WARN] Immagine corrotta: {e}")
                    continue
                
                if set_wallpaper(image_path):
                    print(f"[SUCCESS] Completato in {attempt} tentativ{'o' if attempt == 1 else 'i'}")
                    
                    # Salva spiegazione
                    try:
                        explanation = data.get('explanation', 'Nessuna spiegazione disponibile')
                        wrapped_explanation = textwrap.fill(explanation, width=80)
                        txt_path.write_text(
                            f"Titolo: {data.get('title', 'Sconosciuto')}\n"
                            f"Data: {apod_date}\n\n"
                            f"{wrapped_explanation}",
                            encoding='utf-8'
                        )
                    except Exception:
                        pass
                    
                    # PULISCI I VECCHI FILE SOLO DOPO AVER IMPOSTATO IL NUOVO
                    cleanup_old_files(folder_path, current_wallpaper, image_path, txt_path)
                    
                    return
        
        if attempt < MAX_RETRIES:
            print(f"[WARN] Tentativo {attempt}/{MAX_RETRIES} fallito, riprovo...")
    
    print("[ERRORE] Impossibile ottenere un'immagine APOD valida dopo 5 tentativi.")

if __name__ == "__main__":
    main()