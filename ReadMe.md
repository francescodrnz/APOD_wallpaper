# Space & Nature Wallpaper Manager

Automated wallpaper switcher for Windows 10/11 and Linux (GNOME, KDE Plasma, XFCE, Cinnamon, MATE, Budgie). The same scripts detect the system on their own. Fetches high-res imagery from **NASA** and **Unsplash**, adapts them to your screen using **Ambient Blur** (no black bars), and dynamically syncs the **Windows UI accent color** (Windows only).

## Key Features
* **Smart Resize:** Automatically applies a cinematic "Ambient Blur" to fill the screen, preserving the original aspect ratio without cropping.
* **DWM Color Sync:** Extracts the dominant color from the wallpaper and applies it to the Windows interface (Dark Mode safe).
* **Multi-Source:** Cycles through NASA APOD, NASA Library, and Unsplash (Nature/Space).
* **Auto-Config:** Automatically handles Python dependencies and configuration files.
* **Instant Change:** After each change, the next wallpaper is downloaded and prepared in the background (`apod_images/prossimo/`), so the next change is almost instant.
* **No Blurry Images:** Images smaller than 1280 px on the long side are skipped.

## Windows Requirements
For the features to work correctly, set these Windows settings:
1. **Background:** Set fit to **Fill** (Riempi).
2. **Colors:** Enable "Show accent color on Start and taskbar" if you want to see it there. The script picks the accent color itself and turns off Windows' "Automatic" option.

## API Keys
* **NASA (APOD & Image Library):** no key needed.
* **Unsplash (optional):** without a key the script only uses NASA sources. To add Unsplash images, get a free key at [unsplash.com/developers](https://unsplash.com/developers) (Register -> Create a new App -> Copy Access Key).

## Installation & Setup

1. **Clone the repo:**
   ```sh
   git clone https://github.com/francescodrnz/APOD_wallpaper
   cd APOD_wallpaper
   ```
2. **First Run:**
   Double-click `apod.pyw`. It creates `config.json` and asks if you want to open it to add an Unsplash key.
   * **No:** it continues and sets your first wallpaper using NASA sources only.
   * **Yes:** it opens `config.json` and exits, so you can paste your key.

3. **Add the Unsplash Key (optional):**
   In `config.json`, replace the placeholder with your Access Key, then run `apod.pyw` again:
   ```json
   {
       "UNSPLASH_API_KEY": "your_unsplash_key_here"
   }
   ```

## UI & Statistics (`cambia_sfondo.pyw`)
You can evaluate and manage your wallpapers using the interactive UI. **💡 Recommended use:** Create a shortcut to `cambia_sfondo.pyw` on your Desktop for quick access!
1. Double-click `cambia_sfondo.pyw` (or its shortcut) to open the evaluation window.
2. View the **Title, Source, and Category** of the current image.
3. Read the image description directly via the **Apri info** button.
4. **Rate** the wallpaper (Like/Dislike) to track your preferences (the script prevents duplicate votes).
5. View your past ratings and category stats with the **Mostra Statistiche** button.

## Auto-Start
To run silently at login:
1. Right-click the `apod.pyw` file -> **Create Shortcut**.
2. Press `Win + R`, type `shell:startup`, and Enter.
3. Move the shortcut into the opened folder.

## Troubleshooting
* **Windows Color is Blue/Default:** The script writes the full accent palette and turns off Windows' "Automatic" accent option, which falls back to blue on very dark images. If the image is near-black (e.g., deep space), the script uses a dark grey. Some apps only pick up the new color after a restart or a sign-out.
* **Black Bars/Cropped Image:** Ensure Windows Background fit is set to **Fill**. The script handles the aspect ratio internally.
* **Missing Config Popup:** Check that `config.json` is not excluded by your antivirus or file permissions.

## Linux
The same files work on Linux and detect the system automatically, on any distribution. What matters is the desktop environment. Supported: **GNOME** (Ubuntu, Fedora, Debian, Pop!_OS...), **KDE Plasma** (Kubuntu, Fedora KDE, openSUSE...), **XFCE** (Xubuntu, Linux Mint XFCE...), **Cinnamon** (Linux Mint), **MATE** and **Budgie**. On other environments (i3, Sway, Hyprland, LXQt...) the image is downloaded but the wallpaper is not changed.

KDE Plasma and XFCE support has not been tested on a real system yet: if it does not work for you, please open an issue.

Differences from Windows:
* The accent color is not changed (on Linux it depends on the desktop theme).
* Dependencies are not installed automatically, because the system Python does not allow `pip install`. Install them once:
  ```sh
  sudo apt install python3-requests python3-pil python3-tk zenity          # Debian, Ubuntu, Mint
  sudo dnf install python3-requests python3-pillow python3-tkinter zenity  # Fedora
  sudo pacman -S python-requests python-pillow tk zenity                   # Arch, Manjaro
  ```
  (`python3-tk` is only needed for `cambia_sfondo.pyw`, `zenity` for the first-run popup.)
* Run the scripts with `python3` (double-clicking a `.pyw` file opens it in a text editor):
  ```sh
  python3 apod.pyw            # change wallpaper
  python3 cambia_sfondo.pyw   # rating window
  ```

**Auto-start at login:** create `~/.config/autostart/apod.desktop` (replace the path with your clone):
```ini
[Desktop Entry]
Type=Application
Name=APOD Wallpaper
Exec=sh -c "sleep 15 && exec python3 /home/USER/APOD_wallpaper/apod.pyw"
X-GNOME-Autostart-enabled=true
```
The 15-second wait gives the network time to come up after login. This works the same way on every desktop listed above.

**Menu launcher for the rating window:** create `~/.local/share/applications/cambia_sfondo.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=Cambia Sfondo
Exec=python3 /home/USER/APOD_wallpaper/cambia_sfondo.pyw
Icon=preferences-desktop-wallpaper
Terminal=false
```
The image is already sized to your screen. If you see bars or a cropped image, set the background style to **Zoom** (GNOME, Cinnamon, XFCE, MATE) or **Scaled and Cropped** (KDE).

## License
MIT License. Created by **Francesco Doronzo**.