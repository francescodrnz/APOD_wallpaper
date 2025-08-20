import subprocess
import importlib

# Controlla e installa le librerie mancanti
def install_dependencies():
    required_packages = {
        "requests": "requests",
        "pillow": "PIL"
    }
    for pip_name, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            print(f"[INFO] Installazione di {pip_name}...")
            subprocess.check_call(["python", "-m", "pip", "install", pip_name])
            importlib.import_module(import_name)

# Esegui subito il controllo
install_dependencies()

# Import standard library
import os
import ctypes
import random
from datetime import datetime, timedelta, UTC
import winreg

# Import librerie esterne
import requests
from PIL import Image

# Funzione per scaricare e impostare lo sfondo
def download_and_set_wallpaper(image_url, folder_path):
    print(f"[INFO] Download dell'immagine da {image_url}")
    image_path = os.path.join(folder_path, "apod_wallpaper.jpg")

    try:
        response = requests.get(image_url, stream=True, timeout=15)
        response.raise_for_status()
        with open(image_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=4096):
                file.write(chunk)
        print(f"[INFO] Immagine salvata in {image_path}")
    except Exception as e:
        print(f"[ERRORE] Download fallito: {e}")
        return

    # Apri e ruota l'immagine se necessario
    try:
        image = Image.open(image_path)
        #if image.height > image.width:
        #    print("[INFO] Immagine verticale: ruoto di 90°")
        #    image = image.transpose(Image.ROTATE_90)
        #    image.save(image_path)
    except Exception as e:
        print(f"[ERRORE] Problema con l'immagine: {e}")
        return

    # Aggiorna il registro di Windows
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Control Panel\Desktop",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "Wallpaper", 0, winreg.REG_SZ, image_path)
        winreg.CloseKey(key)
        print("[INFO] Registro aggiornato con il nuovo wallpaper")
    except Exception as e:
        print(f"[ERRORE] Impossibile aggiornare il registro: {e}")

    # Imposta come sfondo e notifica Explorer
    try:
        SPI_SETDESKWALLPAPER = 20
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, image_path,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        print("[INFO] Wallpaper applicato con successo ✅")
    except Exception as e:
        print(f"[ERRORE] Impossibile impostare lo sfondo: {e}")

# Funzione per ottenere i dati APOD
def get_apod_image(api_key, date=None):
    url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}&hd=True"
    if date:
        url += f"&date={date}"
        print(f"[INFO] Richiesta immagine APOD per la data {date}")
    else:
        print("[INFO] Richiesta immagine APOD per oggi")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("[INFO] Risposta ricevuta correttamente da NASA API")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERRORE] Richiesta a NASA API fallita: {e}")
        return {}

# Funzione per generare una data casuale
def random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

# Main
def main():
    api_key = "uSEGw3fuem0zi1Ks76NsilpRUtxXcTi1lEseL8P2"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(script_dir, "apod_images")
    os.makedirs(folder_path, exist_ok=True)

    print("[INFO] Avvio script APOD wallpaper...")
    start_date = datetime(1995, 6, 16)
    end_date = datetime.now(UTC) - timedelta(days=1)

    max_retries = 5
    attempt = 0
    data = {}

    while attempt < max_retries:
        date = random_date(start_date, end_date) if attempt > 0 else None
        data = get_apod_image(api_key, date)
        if "hdurl" in data:
            break
        attempt += 1
        print(f"[WARN] Tentativo {attempt} fallito, riprovo...")

    if "hdurl" in data:
        print(f"[INFO] Titolo: {data.get('title', 'Sconosciuto')}")
        download_and_set_wallpaper(data["hdurl"], folder_path)
    else:
        print("[ERRORE] Impossibile ottenere l'immagine APOD dopo 5 tentativi.")

if __name__ == "__main__":
    main()
