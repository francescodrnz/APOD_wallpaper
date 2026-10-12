import subprocess
import json
import sys
import time
import tkinter as tk
from tkinter import ttk

from comune import (BASE_DIR, CONFIG_FILE, STATS_FILE, get_current_wallpaper, set_wallpaper,
                    update_windows_accent, load_stats, is_excluded, read_info, mark_rated,
                    list_history, current_index)

APOD_SCRIPT = BASE_DIR / "apod.pyw"

def get_current_wallpaper_info():
    wp_path = get_current_wallpaper()
    return read_info(wp_path.with_suffix(".txt") if wp_path else None)

def update_stats(category, is_positive):
    stats = load_stats()

    if category not in stats:
        stats[category] = {"scarti": 0, "positivi": 0}
        
    if is_positive:
        stats[category]["positivi"] += 1
    else:
        stats[category]["scarti"] += 1

    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)
    except: pass

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

    all_buttons = (btn_dislike, btn_like, btn_change, btn_info, btn_manage, btn_prev, btn_next)

    def disable_buttons(status_msg):
        for btn in all_buttons:
            btn.config(state=tk.DISABLED)
        lbl_status.config(text=status_msg, fg="blue")

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
        files = list_history()
        idx = current_index(files, get_current_wallpaper())

        btn_prev.config(state=tk.NORMAL if idx > 0 else tk.DISABLED)
        btn_next.config(state=tk.NORMAL if idx < len(files) - 1 else tk.DISABLED)
        
        if status_msg:
            lbl_status.config(text=status_msg, fg=color)
        else:
            lbl_status.config(text="")

    def check_process(proc, start_time, previous_wp):
        if proc.poll() is None:
            elapsed = int(time.time() - start_time)
            lbl_status.config(text=f"⏳ Sfondo in download... ({elapsed}s)", fg="blue")
            root.after(250, check_process, proc, start_time, previous_wp)
        elif get_current_wallpaper() != previous_wp:
            refresh_ui("✅ Sfondo cambiato con successo!", "green")
        else:
            refresh_ui("⚠️ Nessuno sfondo trovato, riprova più tardi", "red")

    def run_apod():
        if APOD_SCRIPT.exists():
            disable_buttons("⏳ Sfondo in download... (0s)")
            previous_wp = get_current_wallpaper()
            proc = subprocess.Popen([sys.executable, str(APOD_SCRIPT)], cwd=str(BASE_DIR), creationflags=subprocess.CREATE_NO_WINDOW)
            root.after(250, check_process, proc, time.time(), previous_wp)

    def cycle_wallpaper(direction):
        files = list_history()
        if not files: return

        new_idx = current_index(files, get_current_wallpaper()) + direction
        if 0 <= new_idx < len(files):
            new_wp = files[new_idx]

            disable_buttons("⏳ Impostazione sfondo...")
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

        def mark_current_rated():
            wp_path = get_current_wallpaper()
            if wp_path:
                mark_rated(wp_path.with_suffix(".txt"))

        if choice == "like":
            if cat and not rated:
                update_stats(cat, is_positive=True)
                mark_current_rated()
            refresh_ui("✅ Valutazione salvata!", "green")
        elif choice == "dislike":
            if cat and not rated:
                update_stats(cat, is_positive=False)
                mark_current_rated()
            run_apod()
        elif choice == "change":
            run_apod()

    def manage_categories():
        # Config letta prima di aprire la finestra: se manca non resta una finestra vuota
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except: return

        stats = load_stats()

        manage_win = tk.Toplevel(root)
        manage_win.title("Gestione & Statistiche")
        manage_win.geometry("600x450")
        manage_win.grab_set()

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
            
            def insert_item(c):
                counts = stats.get(c, {})
                display_cat = f"{c} 🔴" if is_excluded(counts) else c
                tree.insert("", tk.END, text=c, values=(display_cat, counts.get("positivi", 0), counts.get("scarti", 0)))

            for c in sorted(items, key=str.lower):
                insert_item(c)
            tree.pack(fill=tk.BOTH, expand=True)
            
            entry = tk.Entry(f_sec)
            entry.pack(fill=tk.X, pady=2)
            
            def add_item():
                val = entry.get().strip()
                if val:
                    existing = [tree.item(child, "text") for child in tree.get_children()]
                    if val not in existing:
                        insert_item(val)
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
