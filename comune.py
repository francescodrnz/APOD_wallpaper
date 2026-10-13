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

# --- SFONDO SU LINUX ---
# Ogni ambiente desktop salva lo sfondo in un posto diverso:
# - Cinnamon, GNOME (anche Budgie e Unity) e MATE: gsettings
# - XFCE: xfconf-query, con una proprieta' last-image per ogni monitor e area di lavoro
# - KDE Plasma: plasma-apply-wallpaperimage, o uno script inviato via D-Bus sulle versioni vecchie
GSETTINGS_KEYS = {
    # (schema, chiave, tipo): il tipo "uri" vuole un file://, "path" il percorso semplice
    "cinnamon": [("org.cinnamon.desktop.background", "picture-uri", "uri")],
    "mate": [("org.mate.background", "picture-filename", "path")],
    # Da GNOME 42 il tema scuro usa una chiave a parte
    "gnome": [("org.gnome.desktop.background", "picture-uri", "uri"),
              ("org.gnome.desktop.background", "picture-uri-dark", "uri")],
}
KDE_APPLETSRC = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "plasma-org.kde.plasma.desktop-appletsrc"
# Plasma non salva subito la sua configurazione su disco: qui si annota l'ultimo sfondo impostato
KDE_LAST = IMAGES_DIR / "sfondo_impostato_kde"
KDE_SCRIPT = ('var d = desktops(); for (var i = 0; i < d.length; i++) {'
              ' d[i].wallpaperPlugin = "org.kde.image";'
              ' d[i].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];'
              ' d[i].writeConfig("Image", %s); }')

def _linux_desktop():
    desktop = (os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or "").lower()
    if "cinnamon" in desktop: return "cinnamon"
    if "mate" in desktop: return "mate"
    if "xfce" in desktop: return "xfce"
    if "kde" in desktop or "plasma" in desktop: return "kde"
    if any(d in desktop for d in ("gnome", "unity", "budgie")): return "gnome"
    return None

def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=20)

def _to_path(value):
    # Accetta sia un URI file:// sia un percorso semplice
    return Path(unquote(urlparse(value).path)) if value.startswith("file://") else Path(value)

def _xfconf(*args):
    return _run(["xfconf-query", "-c", "xfce4-desktop", *args])

def _xfce_image_props():
    return sorted(p for p in _xfconf("-l").stdout.split() if p.endswith("/last-image"))

def _kde_get_wallpaper():
    # Immagini che Plasma ha salvato per i suoi desktop
    images, in_section = [], False
    try:
        for line in KDE_APPLETSRC.read_text(encoding="utf-8").splitlines():
            if line.startswith("["):
                in_section = line.strip().endswith("[Wallpaper][org.kde.image][General]")
            elif in_section and line.startswith("Image="):
                images.append(_to_path(line[len("Image="):].strip()))
    except: pass
    try:
        last = Path(KDE_LAST.read_text(encoding="utf-8").strip())
        try: newer = KDE_APPLETSRC.stat().st_mtime > KDE_LAST.stat().st_mtime
        except OSError: newer = False
        # L'ultimo sfondo impostato da qui vale finche' Plasma non salva una configurazione
        # piu' recente che non lo contiene, cioe' finche' lo sfondo non viene cambiato a mano
        if last in images or not newer:
            return last
    except: pass
    return images[0] if images else None

def _kde_set_wallpaper(path):
    commands = [["plasma-apply-wallpaperimage", str(path)]]
    script = KDE_SCRIPT % json.dumps(path.as_uri())
    commands += [[qdbus, "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script]
                 for qdbus in ("qdbus6", "qdbus-qt6", "qdbus", "qdbus-qt5")]
    for cmd in commands:
        try:
            if _run(cmd).returncode == 0:
                try: KDE_LAST.write_text(str(path), encoding="utf-8")
                except: pass
                return True
        except: pass  # comando non installato, si prova il successivo
    return False

def _linux_get_wallpaper():
    desktop = _linux_desktop()
    if desktop == "kde":
        return _kde_get_wallpaper()
    if desktop == "xfce":
        props = _xfce_image_props()
        value = _xfconf("-p", props[0]).stdout.strip() if props else ""
        return Path(value) if value else None
    if desktop in GSETTINGS_KEYS:
        schema, key, _ = GSETTINGS_KEYS[desktop][0]
        value = _run(["gsettings", "get", schema, key]).stdout.strip().strip("'")
        return _to_path(value) if value else None
    return None

def _linux_set_wallpaper(path):
    desktop = _linux_desktop()
    if desktop == "kde":
        return _kde_set_wallpaper(path)
    ok = False
    if desktop == "xfce":
        for prop in _xfce_image_props():
            ok = _xfconf("-p", prop, "-s", str(path)).returncode == 0 or ok
        return ok
    for schema, key, kind in GSETTINGS_KEYS.get(desktop, []):
        value = path.as_uri() if kind == "uri" else str(path)
        try: ok = _run(["gsettings", "set", schema, key, value]).returncode == 0 or ok
        except: pass
    return ok

def get_current_wallpaper():
    if not IS_WINDOWS:
        try: return _linux_get_wallpaper()
        except: return None
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
        try: return _linux_set_wallpaper(Path(path).absolute())
        except: return False
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
