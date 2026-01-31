# Space & Nature Wallpaper Manager

Automated wallpaper switcher for Windows 11/10. Fetches high-res imagery from NASA and Unsplash, intelligently resizes them to fit your monitor using "Ambient Blur" padding, and syncs the Windows UI accent color to match the image atmosphere.

## Core Features
* **Multi-Source Fallback:** Cycles through **NASA APOD**, **NASA Image Library**, and **Unsplash** (Nature/Space themes). Automatically retries on failure.
* **Smart Aspect Ratio:** No more cropping or black bars. Uses a Gaussian Blur algorithm to extend the background, preserving 100% of the original image composition (ideal for vertical/4:3 images on 16:9 screens).
* **DWM Color Sync:** Extracts the dominant color palette from the wallpaper and injects it into the Windows Desktop Window Manager (DWM).
    * *Dark Mode Safe:* Automatically normalizes near-black colors to Dark Grey to prevent Windows from resetting to default blue.
* **Auto-Maintenance:** Self-installs dependencies, manages file rotation, and cleans up old wallpapers.

## Setup & API Keys

### 1. Get API Keys
You need keys to access high-res streams. Both are free.

* **NASA API:**
    1. Go to [api.nasa.gov](https://api.nasa.gov/).
    2. Fill in your name/email.
    3. Copy the generated **API Key**.

* **Unsplash API:**
    1. Register at [unsplash.com/developers](https://unsplash.com/developers).
    2. Click "New Application" -> Accept terms.
    3. Name it (e.g., "WallpaperScript").
    4. Scroll down to "Keys" and copy the **Access Key**.

### 2. Configure Script
Open `wallpaper_script.pyw` with a text editor and paste your keys in the configuration section:

```python
NASA_API_KEY = "DEMO_KEY"
UNSPLASH_API_KEY = "your_unsplash_key_here"
```

## Windows Configuration (Important)
For the best experience, ensure your Windows settings are correct:

1. **Wallpaper Fit:** Go to *Personalization > Background* and set "Choose a fit for your desktop image" to **Fill** (or **Riempi** in Italian). 
   * *Reason:* The script generates an image that matches your screen resolution exactly. Other settings might distort the "Ambient Blur" effect.
2. **Accent Color:** Go to *Personalization > Colors* and set "Accent color" to **Automatic**.
   * *Reason:* This allows the script to dynamically update the system color scheme.

## Installation

1. **Clone/Download:**
   ```sh
   git clone https://github.com/francescodrnz/APOD_wallpaper
   cd APOD_wallpaper
   ```
2. **First Run:**
   Double-click the script. It will automatically:
   * Install missing Python libraries (`requests`, `pillow`).
   * Create the `apod_images` directory.
   * Download and set the first wallpaper.

## Auto-Start
1. **Create Shortcut:** Right-click the script file -> *Create Shortcut*.
2. **Open Startup Folder:** Press `Win + R`, type `shell:startup`, and hit Enter.
3. **Move Shortcut:** Drag the newly created shortcut into the Startup folder.

*Done. The script will now trigger silently on every login.*

## Requirements
* **OS:** Windows 10 or 11 (Windows 11 recommended for DWM color features).
* **Python:** 3.8+ recommended.

## Troubleshooting
* **Windows Color remains Blue:** 1. Ensure your "Accent color" setting is set to Automatic in Windows Personalization settings. 2. The image might be too dark (pure black). The script has a safety override to set it to Dark Grey (`#282828`) to ensure visibility, but if it fails, check if "Accent Color on Start and Taskbar" is enabled in Windows Settings.
* **Script doesn't run:** Check if `pythonw.exe` is associated with `.pyw` files.

## License
MIT License.

## Author
**Francesco Doronzo**