"""Funzioni condivise da apod.pyw e cambia_sfondo.pyw."""
import subprocess
import importlib.util
import ctypes
import json
import os
import shlex
import shutil
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
APOD_SCRIPT = BASE_DIR / "apod.pyw"
UI_SCRIPT = BASE_DIR / "cambia_sfondo.pyw"
ICON_PNG = BASE_DIR / "icona.png"
ICON_ICO = BASE_DIR / "icona.ico"
# Scritto dagli installer e dall'aggiornamento: commit, ramo e data della versione installata
VERSION_FILE = BASE_DIR / "versione.json"
XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
XDG_DATA = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
# Cartella in cui installano installa.ps1 e installa.sh (chi usa un clone resta dove ha clonato)
if IS_WINDOWS:
    INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "APOD_wallpaper"
else:
    INSTALL_DIR = XDG_DATA / "apod_wallpaper"

# --- POPUP E CONFIGURAZIONE ---
UNSPLASH_KEY_PLACEHOLDER = "your_unsplash_key_here"
DEFAULT_CONFIG = {
    "UNSPLASH_API_KEY": UNSPLASH_KEY_PLACEHOLDER,
    "colore_accento": True,
    "unsplash_categories": [
        "nature", "landscape", "space", "mountain", "ocean", "sky", "forest", "desert", "aurora", "milkyway",
        "astrophotography", "stars", "night sky", "cosmos", "observatory", "telescope",
        "volcano", "canyon", "glacier", "waterfall", "sunset", "abstract", "cityscape", "minimalism"
    ],
    "nasa_categories": [
        "galaxy", "nebula", "planet", "earth from space", "space station", "mars", "moon", "jupiter", "saturn",
        "astronaut", "hubble", "james webb", "supernova", "black hole", "solar eclipse", "aurora borealis"
    ]
}

def show_popup(title, message, style=0x40):
    """
    Mostra un popup nativo e ritorna l'ID del tasto premuto.
    style: combina icona e tasti (es. 0x04=YesNo, 0x40=Info)
    Return: 6 (Yes), 7 (No), 1 (OK)
    """
    if not IS_WINDOWS:
        # Su Linux usa zenity con gli stessi codici di ritorno; se manca la risposta vale "No"
        kind = "--question" if style & 0x04 else "--error" if style & 0x10 else "--info"
        try:
            res = subprocess.run(["zenity", kind, "--no-markup", "--width=400",
                                  f"--title={title}", f"--text={message}"])
            if res.returncode == 0:
                return 6 if kind == "--question" else 1
        except: pass
        return 7
    return ctypes.windll.user32.MessageBoxW(0, message, title, style | 0x1000)

def read_config():
    # Lettura silenziosa: {} se il file manca o e' illeggibile
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except: return False

def load_config():
    # Al primo avvio crea config.json in silenzio: la chiave Unsplash e' facoltativa
    # e si inserisce dalla finestra Impostazioni
    if not CONFIG_FILE.exists():
        if not save_config(DEFAULT_CONFIG):
            show_popup("Errore Critico", f"Impossibile creare {CONFIG_FILE}", 0x10)
        return dict(DEFAULT_CONFIG)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        show_popup("Errore Config", f"File config.json corrotto: {e}", 0x10)
        return dict(DEFAULT_CONFIG)

    # Le chiavi aggiunte nelle versioni successive prendono il valore predefinito
    missing = [k for k in DEFAULT_CONFIG if k not in config]
    for k in missing:
        config[k] = DEFAULT_CONFIG[k]
    if missing:
        save_config(config)
    return config

def unsplash_key(config):
    # Chiave assente o ancora segnaposto: Unsplash viene saltato e restano le fonti NASA
    key = (config.get("UNSPLASH_API_KEY") or "").strip()
    return "" if key == UNSPLASH_KEY_PLACEHOLDER or "INSERISCI" in key else key

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
KDE_APPLETSRC = XDG_CONFIG / "plasma-org.kde.plasma.desktop-appletsrc"
# Plasma non salva subito la sua configurazione su disco: qui si annota l'ultimo sfondo impostato
KDE_LAST = IMAGES_DIR / "sfondo_impostato_kde"
KDE_SCRIPT = ('var d = desktops(); for (var i = 0; i < d.length; i++) {'
              ' d[i].wallpaperPlugin = "org.kde.image";'
              ' d[i].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];'
              ' d[i].writeConfig("Image", %s);'
              ' d[i].writeConfig("FillMode", 2); }')  # 2 = Ridimensionata e ritagliata

def _linux_desktop():
    desktop = (os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or "").lower()
    if "cinnamon" in desktop: return "cinnamon"
    if "mate" in desktop: return "mate"
    if "xfce" in desktop: return "xfce"
    if "kde" in desktop or "plasma" in desktop: return "kde"
    if any(d in desktop for d in ("gnome", "unity", "budgie")): return "gnome"
    return None

def _run(cmd, timeout=20, **kwargs):
    if IS_WINDOWS:
        # Lanciato da pythonw: senza questa opzione ogni comando aprirebbe una console
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)

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
            # Stile "Ingrandita" (5): l'immagine e' gia' della misura dello schermo
            try: _xfconf("-p", prop.rsplit("/", 1)[0] + "/image-style", "-n", "-t", "int", "-s", "5")
            except: pass
        return ok
    for schema, key, kind in GSETTINGS_KEYS.get(desktop, []):
        value = path.as_uri() if kind == "uri" else str(path)
        try: ok = _run(["gsettings", "set", schema, key, value]).returncode == 0 or ok
        except: pass
    if ok:
        # Modalita' "Zoom": con un'altra modalita' scelta a mano comparirebbero bande o ritagli
        try: _run(["gsettings", "set", GSETTINGS_KEYS[desktop][0][0], "picture-options", "zoom"])
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
        # Modalita' "Riempi" (WallpaperStyle 10): viene letta dal registro al momento del cambio
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
            winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "10")
            winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
    except: pass
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
    # Disattivato dalla finestra Impostazioni
    if not read_config().get("colore_accento", True): return False
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

# --- INTEGRAZIONE COL SISTEMA: AVVIO AUTOMATICO, COLLEGAMENTI, DISINSTALLAZIONE ---
# Lo stato si legge dal sistema e non dal config, cosi' le Impostazioni mostrano quello che c'e' davvero
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "APOD_wallpaper"
AUTOSTART_FILE = XDG_CONFIG / "autostart" / "apod.desktop"

def pythonw_path():
    # Su Windows gli script vanno lanciati con pythonw, che non apre la console
    exe = Path(sys.executable)
    if IS_WINDOWS and exe.name.lower() == "python.exe" and exe.with_name("pythonw.exe").exists():
        return exe.with_name("pythonw.exe")
    return exe

def open_path(path):
    # Apre un file o una cartella con il programma predefinito del sistema
    try:
        if IS_WINDOWS: os.startfile(path)
        else: subprocess.Popen(["xdg-open", str(path)], **BG_PROCESS)
        return True
    except: return False

def _windows_folder(csidl):
    # Cartelle speciali dell'utente (anche se spostate, ad esempio il Desktop su OneDrive)
    buf = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(0, csidl, 0, 0, buf)
    return Path(buf.value)

def _legacy_startup_links():
    # Collegamenti ad apod.pyw messi a mano in Esecuzione automatica seguendo il vecchio ReadMe:
    # vanno tolti, altrimenti all'accesso lo sfondo cambierebbe due volte
    try:
        links = []
        for lnk in _windows_folder(0x0007).glob("*.lnk"):  # CSIDL_STARTUP
            data = lnk.read_bytes().lower()
            if b"apod.pyw" in data or "apod.pyw".encode("utf-16-le") in data:
                links.append(lnk)
        return links
    except: return []

def _desktop_exec(*args):
    # Riga Exec di un file .desktop: ogni argomento tra virgolette con i caratteri speciali protetti,
    # poi le barre rovesciate raddoppiate perche' il valore e' anche una stringa del formato .desktop
    def quote(arg):
        arg = str(arg).replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
        return f'"{arg}"'
    return " ".join(quote(a) for a in args).replace("\\", "\\\\").replace("%", "%%")

def _write_desktop_file(path, name, comment, args, extra=()):
    lines = ["[Desktop Entry]", "Type=Application", f"Name={name}", f"Comment={comment}",
             "Exec=" + _desktop_exec(*args), f"Icon={ICON_PNG}", "Terminal=false", *extra]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def autostart_enabled():
    if not IS_WINDOWS:
        return AUTOSTART_FILE.exists()
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, RUN_VALUE)
        return True
    except OSError:
        return bool(_legacy_startup_links())

def set_autostart(on):
    # Cambia sfondo a ogni accesso. Restituisce False se non e' stato possibile.
    if not IS_WINDOWS:
        try:
            if on:
                # Il ritardo da' tempo alla rete di collegarsi dopo l'accesso
                cmd = f"sleep 15 && exec {shlex.quote(str(sys.executable))} {shlex.quote(str(APOD_SCRIPT))}"
                _write_desktop_file(AUTOSTART_FILE, "APOD Wallpaper", "Cambia lo sfondo all'accesso",
                                    ["sh", "-c", cmd], ["X-GNOME-Autostart-enabled=true"])
            else:
                AUTOSTART_FILE.unlink(missing_ok=True)
            return True
        except: return False
    try:
        for lnk in _legacy_startup_links():
            lnk.unlink(missing_ok=True)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            if on:
                winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, f'"{pythonw_path()}" "{APOD_SCRIPT}"')
            else:
                try: winreg.DeleteValue(key, RUN_VALUE)
                except FileNotFoundError: pass
        return True
    except: return False

def shortcut_path(where):
    # Collegamento alla finestra cambia_sfondo: where e' "menu" (Start/applicazioni) o "desktop"
    if IS_WINDOWS:
        return _windows_folder(0x0002 if where == "menu" else 0x0010) / "Cambia Sfondo.lnk"
    if where == "menu":
        return XDG_DATA / "applications" / "cambia_sfondo.desktop"
    try: desktop = _run(["xdg-user-dir", "DESKTOP"]).stdout.strip()
    except: desktop = ""
    # Se la cartella Scrivania non e' configurata xdg-user-dir risponde con la home
    if not desktop or Path(desktop) == Path.home():
        desktop = Path.home() / "Desktop"
    return Path(desktop) / "cambia_sfondo.desktop"

def shortcut_exists(where):
    try: return shortcut_path(where).exists()
    except: return False

def set_shortcut(where, on):
    # Crea (o ricrea, aggiornando i percorsi) oppure toglie il collegamento. False se non riesce.
    try:
        path = shortcut_path(where)
        if not on:
            path.unlink(missing_ok=True)
            return True
        if not path.parent.is_dir() and where == "desktop":
            return False
        if not IS_WINDOWS:
            _write_desktop_file(path, "Cambia Sfondo", "Valuta e cambia lo sfondo",
                                [sys.executable, UI_SCRIPT], ["Categories=Utility;"])
            if where == "desktop":
                # Sul desktop di GNOME l'icona si avvia solo se e' eseguibile e segnata come fidata
                path.chmod(0o755)
                try: _run(["gio", "set", str(path), "metadata::trusted", "true"])
                except: pass
            return True
        # I file .lnk si creano solo via COM: lo fa PowerShell, con i valori passati
        # nelle variabili d'ambiente per non doverli proteggere nella riga di comando
        env = dict(os.environ, APOD_LNK=str(path), APOD_TARGET=str(pythonw_path()),
                   APOD_ARGS=f'"{UI_SCRIPT}"', APOD_DIR=str(BASE_DIR), APOD_ICON=str(ICON_ICO))
        script = ("$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:APOD_LNK); "
                  "$s.TargetPath = $env:APOD_TARGET; $s.Arguments = $env:APOD_ARGS; "
                  "$s.WorkingDirectory = $env:APOD_DIR; $s.IconLocation = $env:APOD_ICON; "
                  "$s.Description = 'Valuta e cambia lo sfondo'; $s.Save()")
        res = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], timeout=30, env=env)
        return res.returncode == 0 and path.exists()
    except: return False

def is_install_dir():
    # True se il programma gira dalla cartella degli installer e non da un clone
    try: return BASE_DIR.resolve() == INSTALL_DIR.resolve()
    except: return False

def uninstall(delete_folder=False):
    # Toglie avvio automatico e collegamenti; la cartella si cancella solo se e' quella degli installer
    ok = set_autostart(False)
    for where in ("menu", "desktop"):
        ok = set_shortcut(where, False) and ok
    if delete_folder and is_install_dir():
        if IS_WINDOWS:
            # Il processo che chiama tiene occupata la cartella finche' non esce, anche dopo minuti se il messaggio
            # finale resta aperto: PowerShell aspetta la sua uscita e poi riprova per qualche secondo
            env = dict(os.environ, APOD_PID=str(os.getpid()), APOD_DIR=str(BASE_DIR))
            script = ("Wait-Process -Id $env:APOD_PID -ErrorAction SilentlyContinue; "
                      "for ($i = 0; $i -lt 30 -and (Test-Path -LiteralPath $env:APOD_DIR); $i++) { "
                      "Start-Sleep 1; Remove-Item -LiteralPath $env:APOD_DIR -Recurse -Force -ErrorAction SilentlyContinue }")
            subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                             cwd=os.environ.get("TEMP") or None, env=env, **BG_PROCESS)
        else:
            shutil.rmtree(BASE_DIR, ignore_errors=True)
    return ok

# --- VERSIONE E AGGIORNAMENTI ---
REPO = "francescodrnz/APOD_wallpaper"
GITHUB_API = f"https://api.github.com/repos/{REPO}"

def local_version():
    # {"commit", "ramo", "data"[, "git"]} della versione in uso, oppure None se non si sa
    try:
        version = json.loads(VERSION_FILE.read_text(encoding="utf-8-sig"))
        if version.get("commit"):
            return version
    except: pass
    if (BASE_DIR / ".git").exists():
        # Clone: la versione e' il commit attuale, l'aggiornamento si fa con git pull
        try:
            git = ["git", "-C", str(BASE_DIR)]
            sha = _run(git + ["rev-parse", "HEAD"]).stdout.strip()
            ramo = _run(git + ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
            data = _run(git + ["log", "-1", "--format=%cs"]).stdout.strip()
            if sha:
                return {"commit": sha, "ramo": ramo or "master", "data": data, "git": True}
        except: pass
    return None

def check_update():
    # Confronta la versione in uso con il ramo su GitHub. Restituisce None se e' aggiornata,
    # altrimenti {"commit", "data", "novita"}. In caso di errore (rete, limite API) solleva l'eccezione.
    import requests
    version = local_version()
    if not version:
        raise RuntimeError("versione installata sconosciuta")
    res = requests.get(f"{GITHUB_API}/compare/{version['commit']}...{version['ramo']}", timeout=5,
                       headers={"Accept": "application/vnd.github+json"})
    res.raise_for_status()
    data = res.json()
    commits = data.get("commits") or []
    if data.get("ahead_by", 0) <= 0 or not commits:
        return None
    return {"commit": commits[-1]["sha"],
            "data": commits[-1]["commit"]["committer"]["date"][:10],
            "novita": [c["commit"]["message"].splitlines()[0] for c in commits]}

def apply_update(update):
    # Porta il programma alla versione update["commit"]. Config, statistiche e immagini
    # non fanno parte della repo e restano intatti. Restituisce None se va tutto bene,
    # altrimenti il messaggio d'errore da mostrare.
    version = local_version() or {}
    if version.get("git"):
        try: res = _run(["git", "-C", str(BASE_DIR), "pull", "--ff-only"], timeout=60)
        except Exception as e: return f"git pull non riuscito: {e}"
        return None if res.returncode == 0 else (res.stderr.strip() or "git pull non riuscito")
    try:
        import io, requests, zipfile
        res = requests.get(f"https://github.com/{REPO}/archive/{update['commit']}.zip", timeout=60)
        res.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(res.content)) as archive:
            for item in archive.infolist():
                # Solo i file nella radice dell'archivio, che sta tutto in una cartella "REPO-commit/"
                parts = item.filename.split("/")
                if len(parts) != 2 or not parts[1] or parts[1] == ".gitignore":
                    continue
                tmp = BASE_DIR / (parts[1] + ".nuovo")
                tmp.write_bytes(archive.read(item))
                os.replace(tmp, BASE_DIR / parts[1])
        VERSION_FILE.write_text(json.dumps({"commit": update["commit"], "ramo": version.get("ramo", "master"),
                                            "data": update.get("data", "")}, indent=4), encoding="utf-8")
        return None
    except Exception as e:
        return f"Aggiornamento non riuscito: {e}"
