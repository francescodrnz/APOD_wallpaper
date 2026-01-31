# Space & Nature Wallpaper Manager

Automated wallpaper switcher for Windows 10/11. Fetches high-res imagery from **NASA** and **Unsplash**, adapts them to your screen using **Ambient Blur** (no black bars), and dynamically syncs the **Windows UI accent color**.

## Key Features
* **Smart Resize:** Automatically applies a cinematic "Ambient Blur" to fill the screen, preserving the original aspect ratio without cropping.
* **DWM Color Sync:** Extracts the dominant color from the wallpaper and applies it to the Windows interface (Dark Mode safe).
* **Multi-Source:** Cycles through NASA APOD, NASA Library, and Unsplash (Nature/Space).
* **Auto-Config:** Automatically handles Python dependencies and configuration files.

## Windows Requirements
For the features to work correctly, set these Windows settings:
1. **Background:** Set fit to **Fill** (Riempi).
2. **Colors:** Set "Accent color" to **Automatic**.

## API Keys (Free)
Before installing, get your free keys:
* **NASA:** [api.nasa.gov](https://api.nasa.gov/)
* **Unsplash:** [unsplash.com/developers](https://unsplash.com/developers) (Create a new App -> Copy Access Key)

## Installation & Setup

1. **Clone the repo:**
   ```sh
   git clone https://github.com/francescodrnz/APOD_wallpaper
   cd APOD_wallpaper
   ```
2. **First Run (Generate Config):**
   Double-click `apod.pyw`. 
   * It will show a popup creating `config.json`.
   * The script will exit automatically.

3. **Add Keys:**
   Open the newly created `config.json` with a text editor and paste your API keys:
   ```json
   {
       "NASA_API_KEY": "DEMO_KEY",
       "UNSPLASH_API_KEY": "your_unsplash_key_here"
   }
   ```
   
4. **Run Again:**
   Double-click `apod.pyw`. It will now download your first wallpaper.

## Auto-Start
To run silently at login:
1. Right-click the `apod.pyw` file -> **Create Shortcut**.
2. Press `Win + R`, type `shell:startup`, and Enter.
3. Move the shortcut into the opened folder.

## Troubleshooting
* **Windows Color is Blue/Default:** Ensure "Accent Color" is set to **Automatic**. If the image is pure black (e.g., deep space), the script forces a Dark Grey to prevent Windows from resetting to blue.
* **Black Bars/Cropped Image:** Ensure Windows Background fit is set to **Fill**. The script handles the aspect ratio internally.
* **Missing Config Popup:** Check that `config.json` is not excluded by your antivirus or file permissions.

## License
MIT License. Created by **Francesco Doronzo**.