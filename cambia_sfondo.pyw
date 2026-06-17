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
CONFIG_FILE = BASE_DIR / "config.json"
APOD_SCRIPT = BASE_DIR / "apod.pyw"

def get_current_wallpaper():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_READ) as key:
            wallpaper_path = winreg.QueryValueEx(key, "Wallpaper")[0]
            return Path(wallpaper_path) if wallpaper_path else None
    except:
        return None

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
    
    # Troncamento del titolo se è troppo lungo
    display_title = info["title"]
    if len(display_title) > 60:
        display_title = display_title[:57] + "..."
        
    if info.get("category"):
        title_str = f'{display_title} ({info["source"]} - {info["category"]})'
    else:
        title_str = f'{display_title} ({info["source"]})'
    
    root.title("Valutazione Sfondo")
    
    # Dimensionamento e centratura finestra
    window_width = 340
    window_height = 280
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')
    root.attributes("-topmost", True) # Mantieni in primo piano
    root.resizable(False, False)

    lbl_title = tk.Label(root, text=title_str, font=("Segoe UI", 10, "bold"), pady=10, wraplength=320)
    lbl_title.pack()

    lbl = tk.Label(root, text="Cosa vuoi fare con lo sfondo attuale?", font=("Segoe UI", 11), pady=5)
    lbl.pack()

    def run_apod():
        if APOD_SCRIPT.exists():
            subprocess.Popen([sys.executable, str(APOD_SCRIPT)], cwd=str(BASE_DIR), creationflags=subprocess.CREATE_NO_WINDOW)

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
            # Non cambia sfondo
        elif choice == "dislike":
            if cat and not rated: 
                update_stats(cat, is_positive=False)
                mark_rated()
            run_apod()
        elif choice == "change":
            run_apod()
        root.destroy()

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

        def setup_section(parent, title, items):
            f_sec = tk.Frame(parent)
            f_sec.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            tk.Label(f_sec, text=title).pack()
            
            cols = ("cat", "p", "s")
            tree = ttk.Treeview(f_sec, columns=cols, show="headings", height=12)
            tree.heading("cat", text="Categoria")
            tree.heading("p", text="👍")
            tree.heading("s", text="👎")
            tree.column("cat", width=120, anchor=tk.W)
            tree.column("p", width=40, anchor=tk.CENTER)
            tree.column("s", width=40, anchor=tk.CENTER)
            
            for c in items:
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

    btn_frame = tk.Frame(root)
    btn_frame.pack()

    rated = info.get("rated", False)
    text_dislike = "👎 Non mi piace\n(Già valutato)" if rated else "👎 Non mi piace\n(Scarta)"
    text_like = "👍 Mi piace!\n(Già valutato)" if rated else "👍 Mi piace!\n(Mantieni)"

    btn_dislike = tk.Button(btn_frame, text=text_dislike, command=lambda: action("dislike"), width=16, bg="#ffe5e5", font=("Segoe UI", 9))
    if rated: btn_dislike.config(state=tk.DISABLED) # Disabilitato perché già valutato
    btn_dislike.grid(row=0, column=0, padx=5, pady=5)

    btn_like = tk.Button(btn_frame, text=text_like, command=lambda: action("like"), width=16, bg="#e5ffe5", font=("Segoe UI", 9))
    if rated: btn_like.config(state=tk.DISABLED) # Disabilitato perché già valutato
    btn_like.grid(row=0, column=1, padx=5, pady=5)

    btn_change = tk.Button(btn_frame, text="🔄 Cambia\n(Senza valutare)", command=lambda: action("change"), width=16, bg="#f0f0f0", font=("Segoe UI", 9))
    btn_change.grid(row=1, column=0, padx=5, pady=5)

    btn_info = tk.Button(btn_frame, text="📄 Apri info\n(Mostra testo)", command=lambda: action("open_txt"), width=16, bg="#eef5ff", font=("Segoe UI", 9))
    btn_info.grid(row=1, column=1, padx=5, pady=5)

    btn_manage = tk.Button(btn_frame, text="📊 Gestione & Statistiche", command=manage_categories, width=34, bg="#f3e5ff", font=("Segoe UI", 9))
    btn_manage.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
