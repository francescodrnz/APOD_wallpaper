import subprocess
import winreg
import json
import sys
import os
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# --- CONFIGURAZIONI ---
BASE_DIR = Path(__file__).parent
STATS_FILE = BASE_DIR / "statistiche.json"
APOD_SCRIPT = BASE_DIR / "apod.pyw"

def get_current_wallpaper():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_READ) as key:
            wallpaper_path = winreg.QueryValueEx(key, "Wallpaper")[0]
            return Path(wallpaper_path) if wallpaper_path else None
    except:
        return None

def get_current_category():
    wp_path = get_current_wallpaper()
    if wp_path and wp_path.exists():
        txt_path = wp_path.with_suffix(".txt")
        if txt_path.exists():
            try:
                content = txt_path.read_text(encoding="utf-8")
                lines = content.splitlines()
                category = None
                source = None
                for line in lines:
                    if line.startswith("Category/Theme:"):
                        category = line.replace("Category/Theme:", "").strip()
                    elif line.startswith("Source:"):
                        source = line.replace("Source:", "").strip()
                return category if category else source
            except:
                pass
    return None

def update_stats(category, is_positive):
    stats = {}
    
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                stats = json.load(f)
        except: pass
        
    if category not in stats:
        stats[category] = {"scarti": 0, "positivi": 0}
        
    if is_positive:
        stats[category]["positivi"] += 1
    else:
        stats[category]["scarti"] += 1

    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Errore nel salvataggio: {e}")

def main():
    root = tk.Tk()
    root.title("Valutazione Sfondo")
    
    # Dimensionamento e centratura finestra
    window_width = 320
    window_height = 240
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')
    root.attributes("-topmost", True) # Mantieni in primo piano
    root.resizable(False, False)

    lbl = tk.Label(root, text="Cosa vuoi fare con lo sfondo attuale?", font=("Segoe UI", 11), pady=15)
    lbl.pack()

    def run_apod():
        if APOD_SCRIPT.exists():
            subprocess.Popen([sys.executable, str(APOD_SCRIPT)], cwd=str(BASE_DIR), creationflags=subprocess.CREATE_NO_WINDOW)

    def action(choice):
        if choice == "open_txt":
            wp_path = get_current_wallpaper()
            if wp_path:
                txt_path = wp_path.with_suffix(".txt")
                if txt_path.exists():
                    os.startfile(txt_path)
            return

        cat = get_current_category()
        if choice == "like":
            if cat: update_stats(cat, is_positive=True)
            # Non cambia sfondo
        elif choice == "dislike":
            if cat: update_stats(cat, is_positive=False)
            run_apod()
        elif choice == "change":
            run_apod()
        root.destroy()

    def show_stats():
        stats_win = tk.Toplevel(root)
        stats_win.title("Statistiche Categorie")
        stats_win.geometry("450x300")
        stats_win.grab_set()
        
        columns = ("Categoria", "👍 Mi Piace", "👎 Scarti")
        tree = ttk.Treeview(stats_win, columns=columns, show="headings", height=10)
        tree.heading("Categoria", text="Categoria")
        tree.heading("👍 Mi Piace", text="👍 Mi Piace")
        tree.heading("👎 Scarti", text="👎 Scarti")
        
        tree.column("Categoria", width=180, anchor=tk.W)
        tree.column("👍 Mi Piace", width=100, anchor=tk.CENTER)
        tree.column("👎 Scarti", width=100, anchor=tk.CENTER)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    stats = json.load(f)
                sorted_stats = sorted(stats.items(), key=lambda item: (-item[1].get("positivi", 0), item[1].get("scarti", 0)))
                for cat, counts in sorted_stats:
                    p = counts.get("positivi", 0)
                    s = counts.get("scarti", 0)
                    tree.insert("", tk.END, values=(cat, p, s))
            except:
                tree.insert("", tk.END, values=("Nessuna statistica", "-", "-"))
        else:
            tree.insert("", tk.END, values=("Nessuna statistica", "-", "-"))
            
        btn_close = tk.Button(stats_win, text="Chiudi", command=stats_win.destroy, width=15)
        btn_close.pack(pady=5)

    btn_frame = tk.Frame(root)
    btn_frame.pack()

    btn_dislike = tk.Button(btn_frame, text="👎 Non mi piace\n(Scarta)", command=lambda: action("dislike"), width=16, bg="#ffe5e5", font=("Segoe UI", 9))
    btn_dislike.grid(row=0, column=0, padx=5, pady=5)

    btn_like = tk.Button(btn_frame, text="👍 Mi piace!\n(Mantieni)", command=lambda: action("like"), width=16, bg="#e5ffe5", font=("Segoe UI", 9))
    btn_like.grid(row=0, column=1, padx=5, pady=5)

    btn_change = tk.Button(btn_frame, text="🔄 Cambia\n(Senza valutare)", command=lambda: action("change"), width=16, bg="#f0f0f0", font=("Segoe UI", 9))
    btn_change.grid(row=1, column=0, padx=5, pady=5)

    btn_info = tk.Button(btn_frame, text="📄 Apri info\n(Mostra testo)", command=lambda: action("open_txt"), width=16, bg="#eef5ff", font=("Segoe UI", 9))
    btn_info.grid(row=1, column=1, padx=5, pady=5)

    btn_stats = tk.Button(btn_frame, text="📊 Mostra Statistiche", command=show_stats, width=34, bg="#fff4e5", font=("Segoe UI", 9))
    btn_stats.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
