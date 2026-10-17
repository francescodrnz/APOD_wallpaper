# Space & Nature Wallpaper Manager

*[Leggi in italiano](LeggiMi.md)*

Automated wallpaper switcher for Windows 10/11 and Linux (GNOME, KDE Plasma, XFCE, Cinnamon, MATE, Budgie). The same scripts detect the system on their own. Fetches high-res imagery from **NASA** and **Unsplash**, adapts them to your screen using **Ambient Blur** (no black bars), and dynamically syncs the **Windows UI accent color** (Windows only).

## Key Features
* **One-Line Install:** no git, no manual setup. The installer also installs Python (Windows) or the dependencies (Linux) when they are missing.
* **Smart Resize:** Automatically applies a cinematic "Ambient Blur" to fill the screen, preserving the original aspect ratio without cropping. The wallpaper fit mode is set automatically.
* **DWM Color Sync:** Extracts the dominant color from the wallpaper and applies it to the Windows interface (Dark Mode safe). Can be turned off in the settings.
* **Multi-Source:** Cycles through NASA APOD, NASA Library, and Unsplash (Nature/Space).
* **Settings Window:** language, auto-start, shortcuts, Unsplash key, folders, updates and uninstall, all in one place.
* **English and Italian:** the language follows the system and can be changed at install time or in the settings.
* **Update Notice:** the window tells you when a new version is on GitHub and updates with one click.
* **Instant Change:** After each change, the next wallpaper is downloaded and prepared in the background (`apod_images/prossimo/`), so the next change is almost instant.
* **No Blurry Images:** Images smaller than 1280 px on the long side are skipped.

## Installation

**Windows** — open PowerShell (Start → type `powershell`) and paste:
```powershell
irm https://raw.githubusercontent.com/francescodrnz/APOD_wallpaper/master/installa.ps1 | iex
```

**Linux** — open a terminal and paste:
```sh
curl -fsSL https://raw.githubusercontent.com/francescodrnz/APOD_wallpaper/master/installa.sh | sh
```

The installer downloads the program, installs what is missing and opens the setup window. Pick what you want (all on by default) and press **Install**:
* language (English or Italian; the window switches right away);
* change wallpaper at every login;
* shortcut to the rating window in the Start menu / applications menu;
* shortcut on the desktop;
* Unsplash key (optional).

The first wallpaper is downloaded right away. Everything can be changed later from **⚙️ Settings** in the rating window.

The program lives in `%LOCALAPPDATA%\APOD_wallpaper` (Windows) or `~/.local/share/apod_wallpaper` (Linux). The settings window has a button to open that folder.

**Updating:** when a new version is available the rating window shows a yellow bar with an **Update** button. You can also check from the settings, or simply run the install line again. Your settings, statistics and images are kept.

**Uninstalling:** **⚙️ Settings → Uninstall**. It removes auto-start and shortcuts, and optionally the program folder.

**Coming from an older git clone?** Just run the install line: the installer replaces the clone. If the clone was started at login or from a shortcut, as the old instructions said, the installer finds it and brings over your Unsplash key, categories and statistics (the setup window shows where it took them from). Otherwise copy `config.json` and `statistiche.json` from the clone into the new folder after installing. The old auto-start and the old `Cambia sfondo` shortcut are replaced, so the wallpaper does not change twice at login. You can then delete the clone.

## API Keys
* **NASA (APOD & Image Library):** no key needed.
* **Unsplash (optional):** without a key the script only uses NASA sources. To add Unsplash images, get a free key at [unsplash.com/developers](https://unsplash.com/developers) (Register -> Create a new App -> Copy Access Key) and paste it in **⚙️ Settings**.

## UI & Statistics (`cambia_sfondo.pyw`)
Open **Change Wallpaper** (**Cambia Sfondo** in Italian) from the Start menu, the applications menu or the desktop shortcut.
1. View the **Title, Source, and Category** of the current image.
2. Read the image description directly via the **Open info** button.
3. **Rate** the wallpaper (Like/Dislike) to track your preferences (the script prevents duplicate votes).
4. Browse the previous wallpapers with **Previous / Next**.
5. Manage categories and view your ratings with **Statistics**.
6. Change the setup, including the language, with **Settings**.

## Troubleshooting
* **Windows Color is Blue/Default:** The script writes the full accent palette and turns off Windows' "Automatic" accent option, which falls back to blue on very dark images. If the image is near-black (e.g., deep space), the script uses a dark grey. Some apps only pick up the new color after a restart or a sign-out.
* **Black Bars/Cropped Image:** the script sets the fit mode to **Fill** (Windows), **Zoom** (GNOME, Cinnamon, MATE, XFCE) or **Scaled and Cropped** (KDE) at every change. If you changed it by hand, the next wallpaper puts it back.
* **The installer says Python is missing (Windows):** when it cannot install Python by itself (no `winget`), it opens the [python.org download page](https://www.python.org/downloads/) and prints the steps: download, **Install Now**, then run the install line again.

## Linux
Supported desktops: **GNOME** (Ubuntu, Fedora, Debian, Pop!_OS...), **KDE Plasma** (Kubuntu, Fedora KDE, openSUSE...), **XFCE** (Xubuntu, Linux Mint XFCE...), **Cinnamon** (Linux Mint), **MATE** and **Budgie**. On other environments (i3, Sway, Hyprland, LXQt...) the image is downloaded but the wallpaper is not changed.

KDE Plasma and XFCE support has not been tested on a real system yet: if it does not work for you, please open an issue.

Differences from Windows:
* The accent color is not changed (on Linux it depends on the desktop theme).
* The system Python does not allow `pip install`, so the installer gets the dependencies from the distribution (apt, dnf, pacman or zypper) and asks for your password once.

## Manual Installation (git)
If you prefer a clone:
```sh
git clone https://github.com/francescodrnz/APOD_wallpaper
cd APOD_wallpaper
python cambia_sfondo.pyw --installa     # python3 on Linux
```
On Linux install the dependencies first:
```sh
sudo apt install python3-requests python3-pil python3-tk            # Debian, Ubuntu, Mint
sudo dnf install python3-requests python3-pillow python3-tkinter    # Fedora
sudo pacman -S python-requests python-pillow tk                     # Arch, Manjaro
sudo zypper install python3-requests python3-Pillow python3-tk      # openSUSE
```
Auto-start and shortcuts then point to the clone, and **Update** runs `git pull`.

## License
MIT License. Created by **Francesco Doronzo**.
