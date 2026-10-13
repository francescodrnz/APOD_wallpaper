"""Funzioni condivise da apod.pyw e cambia_sfondo.pyw."""
import subprocess
import importlib.util
import ctypes
import json
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

# Stesso codice su Windows e Linux: le parti che parlano col sistema scelgono il ramo da qui
IS_WINDOWS = sys.platform == "win32"
if IS_WINDOWS:
    import winreg

# Opzioni per i processi lanciati in background: su Windows niente finestra di console,
# su Linux il figlio non viene chiuso insieme al processo che l'ha avviato
BG_PROCESS = {"creationflags": subprocess.CREATE_NO_WINDOW} if IS_WINDOWS else {"start_new_session": True}

# --- GESTIONE DIPENDENZE ---
def install_dependencies():
    required_packages = {"requests": "requests", "pillow": "PIL"}
    for pip_name, import_name in required_packages.items():
        # find_spec controlla la presenza senza importare il modulo
        if importlib.util.find_spec(import_name) is None:
            try:
                # Installazione silenziosa
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass

install_dependencies()

from PIL import Image

# --- PERCORSI ---
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
STATS_FILE = BASE_DIR / "statistiche.json"
IMAGES_DIR = BASE_DIR / "apod_images"

# --- SFONDO E COLORE D'ACCENTO ---
SPI_GETDESKWALLPAPER = 0x0073

def _gsettings_keys():
    # Linux: chiavi gsettings dello sfondo per il desktop in uso, come (schema, chiave, tipo).
    # Il tipo "uri" vuole un file://, "path" il percorso semplice. KDE e XFCE non sono gestiti.
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if "cinnamon" in desktop:
        return [("org.cinnamon.desktop.background", "picture-uri", "uri")]
    if "mate" in desktop:
        return [("org.mate.background", "picture-filename", "path")]
    if any(d in desktop for d in ("gnome", "unity", "budgie")):
        # Da GNOME 42 il tema scuro usa una chiave a parte
        return [("org.gnome.desktop.background", "picture-uri", "uri"),
                ("org.gnome.desktop.background", "picture-uri-dark", "uri")]
    return []

def _gsettings(*args):
    return subprocess.run(["gsettings", *args], capture_output=True, text=True, timeout=10)

def get_current_wallpaper():
    if not IS_WINDOWS:
        try:
            schema, key, kind = _gsettings_keys()[0]
            value = _gsettings("get", schema, key).stdout.strip().strip("'")
            if not value: return None
            return Path(unquote(urlparse(value).path) if kind == "uri" else value)
        except:
            return None
    # Fonte primaria: l'API di sistema. Su alcune installazioni Windows il valore
    # nel registro non viene piu' aggiornato e resta fermo a uno sfondo vecchio.
    try:
        buf = ctypes.create_unicode_buffer(520)
        if ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 520, buf, 0) and buf.value:
            path = Path(buf.value)
            if path.exists():
                return path
    except:
        pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_READ) as key:
            wallpaper_path = winreg.QueryValueEx(key, "Wallpaper")[0]
            return Path(wallpaper_path) if wallpaper_path else None
    except:
        return None

def set_wallpaper(path):
    if not IS_WINDOWS:
        # absolute() e non resolve(): il percorso deve restare confrontabile con IMAGES_DIR
        path = Path(path).absolute()
        ok = False
        for schema, key, kind in _gsettings_keys():
            try:
                value = path.as_uri() if kind == "uri" else str(path)
                ok = _gsettings("set", schema, key, value).returncode == 0 or ok
            except: pass
        return ok
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, str(path), 3)
        return True
    except: return False

def _accent_shade(rgb, factor):
    # factor > 0 schiarisce verso il bianco, factor < 0 scurisce verso il nero
    target = 255 if factor > 0 else 0
    return tuple(int(c + (target - c) * abs(factor)) for c in rgb)

def update_windows_accent(image_path):
    # Su Linux non c'e' un'API comune per il colore d'accento: dipende dal tema del desktop
    if not IS_WINDOWS: return False
    try:
        with Image.open(image_path) as img:
            img.thumbnail((100, 100))
            img = img.convert("RGB")
            colors = img.getcolors(10000)
            if not colors: return False

            colors.sort(key=lambda x: x[0], reverse=True)
            r, g, b = colors[0][1]

        if (r + g + b) < 80:
            r, g, b = 40, 40, 40

        base = (r, g, b)
        # Ordine della AccentPalette: tre tonalita' chiare, la base, tre scure e una extra
        shades = [_accent_shade(base, f) for f in (0.75, 0.5, 0.25, 0, -0.2, -0.4, -0.6, -0.4)]
        palette = bytes(v for sr, sg, sb in shades for v in (sr, sg, sb, 0))
        abgr = lambda c: 0xFF000000 | (c[2] << 16) | (c[1] << 8) | c[0]
        argb = 0xC4000000 | (r << 16) | (g << 8) | b

        # Windows usa la AccentPalette, non DWM\AccentColor. Con la scelta automatica attiva
        # la ricalcola lui dallo sfondo e su quelli molto scuri ripiega sul blu predefinito.
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
            winreg.SetValueEx(key, "AutoColorization", 0, winreg.REG_DWORD, 0)

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent") as key:
            winreg.SetValueEx(key, "AccentPalette", 0, winreg.REG_BINARY, palette)
            winreg.SetValueEx(key, "AccentColorMenu", 0, winreg.REG_DWORD, abgr(base))
            winreg.SetValueEx(key, "StartColorMenu", 0, winreg.REG_DWORD, abgr(shades[4]))

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM") as key:
            winreg.SetValueEx(key, "AccentColor", 0, winreg.REG_DWORD, abgr(base))
            winreg.SetValueEx(key, "ColorizationColor", 0, winreg.REG_DWORD, argb)
            winreg.SetValueEx(key, "ColorizationAfterglow", 0, winreg.REG_DWORD, argb)
            winreg.SetValueEx(key, "ColorPrevalence", 0, winreg.REG_DWORD, 1)

        # Avvisa la shell del cambio colore (WM_SETTINGCHANGE "ImmersiveColorSet")
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "ImmersiveColorSet", 0x0002, 5000, None)
        return True
    except:
        return False

# --- STATISTICHE ---
def load_stats():
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def is_excluded(counts):
    # Una categoria con piu' di 15 voti e piu' dell'80% di scarti non viene piu' usata
    p = counts.get("positivi", 0)
    s = counts.get("scarti", 0)
    tot = p + s
    return tot > 15 and (s / tot) > 0.8

# --- FILE .txt ACCANTO ALL'IMMAGINE ---
def write_info(txt_path, img_data):
    desc = img_data.get('description', '').replace('\n', ' ').replace('\r', '')
    txt_content = f"Title: {img_data['title']}\nDate: {img_data['date']}\nSource: {img_data['source']}\n"
    if 'category' in img_data:
        txt_content += f"Category/Theme: {img_data['category']}\n"
    txt_content += f"\n{desc}"
    txt_path.write_text(txt_content, encoding='utf-8')

def read_info(txt_path):
    info = {"title": "Sfondo Sconosciuto", "source": "Sconosciuto", "category": None, "content": "Nessuna informazione disponibile per questo sfondo.", "cat_or_source": None, "rated": False}
    if txt_path and txt_path.exists():
        try:
            content = txt_path.read_text(encoding="utf-8")
            info["content"] = content
            for line in content.splitlines():
                if line.startswith("Category/Theme:"):
                    info["category"] = line.replace("Category/Theme:", "").strip()
                elif line.startswith("Source:"):
                    info["source"] = line.replace("Source:", "").strip()
                elif line.startswith("Title:"):
                    info["title"] = line.replace("Title:", "").strip()
                elif line.startswith("Valutato:"):
                    info["rated"] = line.replace("Valutato:", "").strip().lower() == "si"

            info["cat_or_source"] = info["category"] if info["category"] else info["source"]
        except:
            pass
    return info

def mark_rated(txt_path):
    if txt_path and txt_path.exists():
        try:
            with open(txt_path, "a", encoding="utf-8") as f:
                f.write("\nValutato: Si\n")
        except: pass

# --- STORICO ---
def list_history():
    # Solo la cartella principale: gli sfondi preparati in anticipo stanno in una sottocartella
    return sorted(IMAGES_DIR.glob("wallpaper_*.jpg"), key=lambda f: f.stat().st_mtime)

def current_index(files, curr):
    # Posizione dello sfondo attivo nello storico; se non c'e' si considera l'ultimo
    return next((i for i, f in enumerate(files) if curr and f.name == curr.name), len(files) - 1)
