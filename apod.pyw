import subprocess
import importlib

# Controlla e installa le librerie mancanti
def install_dependencies():
    required_packages = ["requests", "pillow"]
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            print(f"Installazione di {package}...")
            subprocess.check_call(["python", "-m", "pip", "install", package])
            importlib.import_module(package)  # re-importa dopo l’installazione

# Esegui subito il controllo
install_dependencies()

# Import standard library (non serve installarle)
import os
import ctypes
import shutil
import random
from datetime import datetime, timedelta

# Import librerie esterne (già garantite dall'install_dependencies)
import requests
from PIL import Image

def get_apod_image(api_key, date=None):
    url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}&hd=True"
    if date:
        url += f"&date={date}"
    response = requests.get(url)
    data = response.json()
    return data

def download_and_set_wallpaper(image_url, folder_path):
    image_name = os.path.basename(image_url)
    image_path = os.path.join(folder_path, image_name)
    
    # Rimuovi vecchie immagini nella cartella
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        os.remove(file_path)
    
    # Scarica la nuova immagine
    response = requests.get(image_url, stream=True)
    with open(image_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=4096):
            file.write(chunk)
    
    # Apri e ruota l'immagine se necessario
    image = Image.open(image_path)
    if image.height > image.width:
        image = image.transpose(Image.ROTATE_90)
        image.save(image_path)
    
    # Imposta come sfondo
    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)

def random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

def main():
    api_key = "uSEGw3fuem0zi1Ks76NsilpRUtxXcTi1lEseL8P2"
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Cartella dello script
    folder_path = os.path.join(script_dir, "apod_images")  # Sottocartella per le immagini
    os.makedirs(folder_path, exist_ok=True)
    
    max_retries = 5
    attempt = 0
    data = {}
    
    start_date = datetime(1995, 6, 16)
    end_date = datetime.utcnow() - timedelta(days=1)
    
    while attempt < max_retries:
        date = random_date(start_date, end_date) if attempt > 0 else None
        data = get_apod_image(api_key, date)
        if "hdurl" in data:
            break
        attempt += 1
    
    if "hdurl" in data:
        download_and_set_wallpaper(data["hdurl"], folder_path)
    else:
        print("Impossibile ottenere l'immagine APOD dopo 5 tentativi.")

if __name__ == "__main__":
    main()
