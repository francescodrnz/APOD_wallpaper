import subprocess
import winreg
import json
import sys
import os
import time
import ctypes
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from PIL import Image

# --- CONFIGURAZIONI ---
BASE_DIR = Path(__file__).parent
STATS_FILE = BASE_DIR / "statistiche.json"
CONFIG_FILE = BASE_DIR / "config.json"
APOD_SCRIPT = BASE_DIR / "apod.pyw"

def get_current_wallpaper():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_READ) as key:
            wallpaper_path = winreg.QueryValueEx(key, "Wallpaper")[0]
            return Path(wallpaper_path) if wallpaper_path else None
    except:
        return None

def set_wallpaper(path):
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, str(path), 3)
        return True
    except: return False

def update_windows_accent(image_path):
    try:
        with Image.open(image_path) as img:
            img = img.resize((100, 100)).convert("RGB")
            colors = img.getcolors(10000)
            if not colors: return False
            
            colors.sort(key=lambda x: x[0], reverse=True)
            r, g, b = colors[0][1]

            if (r + g + b) < 80:
                r, g, b = 40, 40, 40

            accent_color_dword = (0 << 24) | (b << 16) | (g << 8) | r
            
            key_path = r"Software\Microsoft\Windows\DWM"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "AccentColor", 0, winreg.REG_DWORD, accent_color_dword)
                winreg.SetValueEx(key, "ColorPrevalence", 0, winreg.REG_DWORD, 1)
                
            ctypes.windll.user32.SystemParametersInfoW(20, 0, str(image_path), 3)
            return True
    except:
        return False

def get_current_wallpaper_info():
    info = {"title": "Sfondo Sconosciuto", "source": "Sconosciuto", "category": None, "content": "Nessuna informazione disponibile per questo sfondo.", "cat_or_source": None, "rated": False}
    wp_path = get_current_wallpaper()
    if wp_path and wp_path.exists():
        txt_path = wp_path.with_suffix(".txt")
        if txt_path.exists():
            try:
                content = txt_path.read_text(encoding="utf-8")
                info["content"] = content
                lines = content.splitlines()
                for line in lines:
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
    
    info = get_current_wallpaper_info()
    
    # Dimensionamento e centratura finestra
    window_width = 340
    window_height = 350
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.title("Valutazione Sfondo")

    lbl_title = tk.Label(root, text="", font=("Segoe UI", 10, "bold"), pady=10, wraplength=320)
    lbl_title.pack()

    lbl = tk.Label(root, text="Cosa vuoi fare con lo sfondo attuale?", font=("Segoe UI", 11), pady=5)
    lbl.pack()

    btn_frame = tk.Frame(root)
    btn_frame.pack()

    btn_dislike = tk.Button(btn_frame, width=16, bg="#ffe5e5", font=("Segoe UI", 9))
    btn_dislike.grid(row=0, column=0, padx=5, pady=5)

    btn_like = tk.Button(btn_frame, width=16, bg="#e5ffe5", font=("Segoe UI", 9))
    btn_like.grid(row=0, column=1, padx=5, pady=5)

    btn_change = tk.Button(btn_frame, text="🔄 Cambia\n(Senza valutare)", width=16, bg="#f0f0f0", font=("Segoe UI", 9))
    btn_change.grid(row=1, column=0, padx=5, pady=5)

    btn_info = tk.Button(btn_frame, text="📄 Apri info\n(Mostra testo)", width=16, bg="#eef5ff", font=("Segoe UI", 9))
    btn_info.grid(row=1, column=1, padx=5, pady=5)

    btn_manage = tk.Button(btn_frame, text="📊 Gestione & Statistiche", width=34, bg="#f3e5ff", font=("Segoe UI", 9))
    btn_manage.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

    btn_prev = tk.Button(btn_frame, text="⬅️ Precedente", width=16, bg="#f0f0f0", font=("Segoe UI", 9))
    btn_prev.grid(row=3, column=0, padx=5, pady=5)

    btn_next = tk.Button(btn_frame, text="Successivo ➡️", width=16, bg="#f0f0f0", font=("Segoe UI", 9))
    btn_next.grid(row=3, column=1, padx=5, pady=5)

    lbl_status = tk.Label(root, text="", font=("Segoe UI", 9, "italic"))
    lbl_status.pack(pady=2)

    def refresh_ui(status_msg="", color="green"):
        nonlocal info
        info = get_current_wallpaper_info()
        
        display_title = info["title"]
        if len(display_title) > 60:
            display_title = display_title[:57] + "..."
            
        if info.get("category"):
            title_str = f'{display_title} ({info["source"]} - {info["category"]})'
        else:
            title_str = f'{display_title} ({info["source"]})'
        
        lbl_title.config(text=title_str)
        
        rated = info.get("rated", False)
        text_dislike = "👎 Non mi piace\n(Già valutato)" if rated else "👎 Non mi piace\n(Scarta)"
        text_like = "👍 Mi piace!\n(Già valutato)" if rated else "👍 Mi piace!\n(Mantieni)"
        
        btn_dislike.config(text=text_dislike, state=tk.DISABLED if rated else tk.NORMAL)
        btn_like.config(text=text_like, state=tk.DISABLED if rated else tk.NORMAL)
        btn_change.config(state=tk.NORMAL)
        btn_info.config(state=tk.NORMAL)
        btn_manage.config(state=tk.NORMAL)
        
        # History check
        files = sorted((BASE_DIR / "apod_images").glob("wallpaper_*.jpg"), key=lambda f: f.stat().st_mtime)
        curr = get_current_wallpaper()
        try:
            idx = next(i for i, f in enumerate(files) if curr and f.name == curr.name)
        except StopIteration:
            idx = len(files) - 1
            
        btn_prev.config(state=tk.NORMAL if idx > 0 else tk.DISABLED)
        btn_next.config(state=tk.NORMAL if idx < len(files) - 1 else tk.DISABLED)
        
        if status_msg:
            lbl_status.config(text=status_msg, fg=color)
        else:
            lbl_status.config(text="")

    def check_process(proc, start_time):
        if proc.poll() is None:
            elapsed = int(time.time() - start_time)
            lbl_status.config(text=f"⏳ Sfondo in download... ({elapsed}s)", fg="blue")
            root.after(1000, check_process, proc, start_time)
        else:
            refresh_ui("✅ Sfondo cambiato con successo!", "green")

    def run_apod():
        if APOD_SCRIPT.exists():
            btn_dislike.config(state=tk.DISABLED)
            btn_like.config(state=tk.DISABLED)
            btn_change.config(state=tk.DISABLED)
            btn_info.config(state=tk.DISABLED)
            btn_manage.config(state=tk.DISABLED)
            btn_prev.config(state=tk.DISABLED)
            btn_next.config(state=tk.DISABLED)
            lbl_status.config(text="⏳ Sfondo in download... (0s)", fg="blue")
            proc = subprocess.Popen([sys.executable, str(APOD_SCRIPT)], cwd=str(BASE_DIR), creationflags=subprocess.CREATE_NO_WINDOW)
            root.after(1000, check_process, proc, time.time())

    def cycle_wallpaper(direction):
        files = sorted((BASE_DIR / "apod_images").glob("wallpaper_*.jpg"), key=lambda f: f.stat().st_mtime)
        if not files: return
        
        curr = get_current_wallpaper()
        try:
            idx = next(i for i, f in enumerate(files) if curr and f.name == curr.name)
        except StopIteration:
            idx = len(files) - 1

        new_idx = idx + direction
        if 0 <= new_idx < len(files):
            new_wp = files[new_idx]
            
            btn_dislike.config(state=tk.DISABLED)
            btn_like.config(state=tk.DISABLED)
            btn_change.config(state=tk.DISABLED)
            btn_info.config(state=tk.DISABLED)
            btn_manage.config(state=tk.DISABLED)
            btn_prev.config(state=tk.DISABLED)
            btn_next.config(state=tk.DISABLED)
            lbl_status.config(text="⏳ Impostazione sfondo...", fg="blue")
            root.update()
            
            if set_wallpaper(new_wp):
                update_windows_accent(new_wp)
                
            refresh_ui("✅ Sfondo impostato!", "green")

    def action(choice):
        if choice == "open_txt":
            info_win = tk.Toplevel(root)
            info_win.title("Informazioni Sfondo")
            info_win.geometry("500x400")
            info_win.grab_set()
            
            btn_close = tk.Button(info_win, text="Chiudi", command=info_win.destroy, width=15)
            btn_close.pack(side=tk.BOTTOM, pady=10)

            # Aggiungiamo uno scrollbar in caso di testo molto lungo
            frame_txt = tk.Frame(info_win)
            frame_txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

            scrollbar = tk.Scrollbar(frame_txt)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            txt_area = tk.Text(frame_txt, wrap=tk.WORD, font=("Segoe UI", 10), yscrollcommand=scrollbar.set)
            txt_area.insert(tk.END, info["content"])
            txt_area.config(state=tk.DISABLED)
            txt_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar.config(command=txt_area.yview)
            return

        cat = info["cat_or_source"]
        rated = info.get("rated", False)

        def mark_rated():
            wp_path = get_current_wallpaper()
            if wp_path:
                txt_path = wp_path.with_suffix(".txt")
                if txt_path.exists():
                    try:
                        with open(txt_path, "a", encoding="utf-8") as f:
                            f.write("\nValutato: Si\n")
                    except: pass

        if choice == "like":
            if cat and not rated: 
                update_stats(cat, is_positive=True)
                mark_rated()
            refresh_ui("✅ Valutazione salvata!", "green")
        elif choice == "dislike":
            if cat and not rated: 
                update_stats(cat, is_positive=False)
                mark_rated()
            run_apod()
        elif choice == "change":
            run_apod()

    def manage_categories():
        manage_win = tk.Toplevel(root)
        manage_win.title("Gestione & Statistiche")
        manage_win.geometry("600x450")
        manage_win.grab_set()

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except: return
        
        stats = {}
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    stats = json.load(f)
            except: pass

        lbl_info = tk.Label(manage_win, text="Gestisci le categorie e visualizza i voti (🔴 = Esclusa in automatico)", pady=10)
        lbl_info.pack()

        frames_container = tk.Frame(manage_win)
        frames_container.pack(fill=tk.BOTH, expand=True, padx=10)

        def treeview_sort_column(tv, col, reverse):
            l = [(tv.set(k, col), k) for k in tv.get_children('')]
            try:
                l.sort(key=lambda t: int(t[0]), reverse=reverse)
            except ValueError:
                l.sort(key=lambda t: t[0].lower(), reverse=reverse)
            
            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)
            tv.heading(col, command=lambda _col=col: treeview_sort_column(tv, _col, not reverse))

        def setup_section(parent, title, items):
            f_sec = tk.Frame(parent)
            f_sec.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            tk.Label(f_sec, text=title).pack()
            
            cols = ("cat", "p", "s")
            tree = ttk.Treeview(f_sec, columns=cols, show="headings", height=12)
            tree.heading("cat", text="Categoria", command=lambda: treeview_sort_column(tree, "cat", False))
            tree.heading("p", text="👍", command=lambda: treeview_sort_column(tree, "p", False))
            tree.heading("s", text="👎", command=lambda: treeview_sort_column(tree, "s", False))
            tree.column("cat", width=120, anchor=tk.W)
            tree.column("p", width=40, anchor=tk.CENTER)
            tree.column("s", width=40, anchor=tk.CENTER)
            
            for c in sorted(items, key=str.lower):
                p = stats.get(c, {}).get("positivi", 0)
                s = stats.get(c, {}).get("scarti", 0)
                tot = p + s
                display_cat = f"{c} 🔴" if (tot > 15 and (s / tot) > 0.8) else c
                tree.insert("", tk.END, text=c, values=(display_cat, p, s))
            tree.pack(fill=tk.BOTH, expand=True)
            
            entry = tk.Entry(f_sec)
            entry.pack(fill=tk.X, pady=2)
            
            def add_item():
                val = entry.get().strip()
                if val:
                    existing = [tree.item(child, "text") for child in tree.get_children()]
                    if val not in existing:
                        p = stats.get(val, {}).get("positivi", 0)
                        s = stats.get(val, {}).get("scarti", 0)
                        tot = p + s
                        display_cat = f"{val} 🔴" if (tot > 15 and (s / tot) > 0.8) else val
                        tree.insert("", tk.END, text=val, values=(display_cat, p, s))
                        entry.delete(0, tk.END)
            
            def rem_item():
                sel = tree.selection()
                if sel: tree.delete(sel[0])
                
            btn_f = tk.Frame(f_sec)
            btn_f.pack()
            tk.Button(btn_f, text="+ Aggiungi", command=add_item).pack(side=tk.LEFT, padx=2)
            tk.Button(btn_f, text="- Rimuovi", command=rem_item).pack(side=tk.LEFT, padx=2)
            
            return tree

        tree_u = setup_section(frames_container, "Unsplash Themes", cfg.get("unsplash_categories", []))
        tree_n = setup_section(frames_container, "NASA Queries", cfg.get("nasa_categories", []))

        def save_and_close():
            cfg["unsplash_categories"] = [tree_u.item(child, "text") for child in tree_u.get_children()]
            cfg["nasa_categories"] = [tree_n.item(child, "text") for child in tree_n.get_children()]
            try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=4)
            except: pass
            manage_win.destroy()

        btn_save = tk.Button(manage_win, text="Salva e Chiudi", command=save_and_close, bg="#e5ffe5", width=20)
        btn_save.pack(pady=10)

    btn_dislike.config(command=lambda: action("dislike"))
    btn_like.config(command=lambda: action("like"))
    btn_change.config(command=lambda: action("change"))
    btn_info.config(command=lambda: action("open_txt"))
    btn_manage.config(command=manage_categories)
    btn_prev.config(command=lambda: cycle_wallpaper(-1))
    btn_next.config(command=lambda: cycle_wallpaper(1))

    refresh_ui()

    root.mainloop()

if __name__ == "__main__":
    main()
