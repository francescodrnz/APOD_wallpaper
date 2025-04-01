# NASA APOD Wallpaper Downloader

This script downloads NASA's Astronomy Picture of the Day (APOD) and sets it as the desktop wallpaper on Windows.
If the image of the day is not available, it randomly selects a date between June 16, 1995, and yesterday.

## Requirements
- **Windows** (required to set the wallpaper automatically)
- **Python 3.7+**
- Active internet connection

## Installation
1. **Download or clone the GitHub repository:**
   ```sh
   git clone https://github.com/francescodrnz/APOD_wallpaper
   cd APOD_wallpaper
   ```
2. **Run the script:**
   ```sh
   python apod.pyw
   ```
   The script will automatically install the required dependencies (**requests, pillow, keyboard**).

## How It Works
- Downloads the latest APOD image (or a random one if needed)
- Saves it in the `apod_images` folder inside the script directory
- Rotates the image if necessary
- Sets the image as the desktop wallpaper

## Running the Script Automatically at Windows Startup
To run the script automatically every time Windows starts, follow these steps:

1. **Create a batch file:**
   - Open Notepad and paste the following:
     ```sh
     @echo off
     python "C:\path\to\apod.pyw"
     ```
   - Replace `C:\path\to\apod.pyw` with the actual script path.
   - Save it as `apod_wallpaper.bat` in a convenient location.

2. **Add the batch file to Windows Startup:**
   - Press `Win + R`, type `shell:startup`, and press `Enter`.
   - Copy the `apod_wallpaper.bat` file into the Startup folder.

Now, the script will run automatically every time you log into Windows.

## Customization
If you want to use a custom NASA API key, modify the `api_key` variable in `apod.pyw`.
You can get a free API key here: [https://api.nasa.gov](https://api.nasa.gov)

## License
This project is released under the MIT License.

## Author
Created by **Francesco Doronzo**

---

If you have any questions or suggestions, feel free to open an **Issue** on GitHub!

