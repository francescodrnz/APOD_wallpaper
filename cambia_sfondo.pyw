import subprocess
import json
import queue
import sys
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont

from comune import (IS_WINDOWS, BG_PROCESS, BASE_DIR, CONFIG_FILE, STATS_FILE, IMAGES_DIR, APOD_SCRIPT,
                    UI_SCRIPT, ICON_PNG, UNSPLASH_KEY_PLACEHOLDER, DEFAULT_CONFIG, show_popup, read_config,
                    get_current_wallpaper, set_wallpaper,
                    update_windows_accent, load_stats, is_excluded, read_info, mark_rated, list_history,
                    current_index, load_config, save_config, unsplash_key, autostart_enabled, set_autostart,
                    shortcut_exists, set_shortcuts, open_path, is_install_dir, uninstall, local_version,
                    check_update, apply_update, find_old_install, import_old_install)

FONT = ("Segoe UI", 9)

def make_modal(win):
    if IS_WINDOWS:
        win.grab_set()
        return
    # Su Linux la finestra diventa visibile solo quando il window manager la mostra:
    # grab_set prima di allora fallisce e interromperebbe la costruzione della finestra
    try:
        win.wait_visibility()
        win.grab_set()
    except tk.TclError: pass

def setup_window(root):
    try: root.iconphoto(True, tk.PhotoImage(master=root, file=str(ICON_PNG)))
    except tk.TclError: pass
    if not IS_WINDOWS:
        # Su Linux il font e' piu' alto e con l'altezza predefinita le righe delle tabelle tagliavano le lettere
        ttk.Style(root).configure("Treeview", rowheight=tkfont.nametofont("TkDefaultFont").metrics("linespace") + 4)

def center(win):
    # Centra la finestra lasciandole la misura richiesta dai widget
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    win.geometry(f"+{(win.winfo_screenwidth() - w) // 2}+{(win.winfo_screenheight() - h) // 2}")

def run_in_background(root, func, callback):
    # Esegue func in un thread (rete, download) e passa (risultato, eccezione) a callback
    # sul thread di Tk, che non puo' essere toccato da altri thread
    results = queue.Queue()
    def worker():
        try: results.put((func(), None))
        except Exception as e: results.put((None, e))
    threading.Thread(target=worker, daemon=True).start()
    def poll():
        try: result, error = results.get_nowait()
        except queue.Empty:
            root.after(200, poll)
            return
        try: callback(result, error)
        except tk.TclError: pass  # la finestra da aggiornare e' stata chiusa nel frattempo
    root.after(200, poll)

def restart_ui(root, *args):
    # Chiude questa finestra e ne apre una nuova in un processo separato (codice appena aggiornato,
    # oppure fine dell'installazione: cosi' il terminale da cui e' partito l'installer si libera)
    try: subprocess.Popen([sys.executable, str(UI_SCRIPT), *args], cwd=str(BASE_DIR), **BG_PROCESS)
    except: pass
    root.destroy()

def version_text(version):
    if not version:
        return "Versione sconosciuta"
    data = version.get("data") or ""
    if len(data) == 10:
        data = f"{data[8:10]}/{data[5:7]}/{data[:4]}"
    return f"Versione {version['commit'][:7]}" + (f" del {data}" if data else "") + f" (ramo {version.get('ramo', 'master')})"

def ask_and_update(root, parent, update, set_status):
    novita = update["novita"]
    totale = update.get("totale", len(novita))
    elenco = "\n".join(f"• {n}" for n in novita[-15:])
    if totale > 15:
        elenco = f"... e altre {totale - 15} modifiche precedenti\n" + elenco
    if not messagebox.askyesno("Aggiornamento disponibile", f"Novità:\n\n{elenco}\n\nVuoi aggiornare ora?", parent=parent):
        return
    set_status("⏳ Aggiornamento in corso...", "blue")

    def done(error, exc):
        error = error or (str(exc) if exc else None)
        owner = parent if parent.winfo_exists() else root
        if error:
            set_status("⚠️ Aggiornamento non riuscito", "red")
            messagebox.showerror("Aggiornamento non riuscito", error, parent=owner)
        else:
            messagebox.showinfo("Aggiornamento completato", "La finestra si riapre con la nuova versione.", parent=owner)
            restart_ui(root)
    run_in_background(root, lambda: apply_update(update), done)

def build_settings(root, win, on_close, intro=None, first_install=False, old_config=None):
    """Riempie win con le impostazioni. on_close(salvate) chiude la finestra.
    intro: testo in cima, solo nella finestra mostrata dagli installer; first_install: prima installazione, tutto selezionato;
    old_config: config di una vecchia installazione da portare qui."""
    install_mode = intro is not None
    # Senza creare config.json: se la prima installazione viene annullata, al rilancio deve risultare ancora la prima
    cfg = {**DEFAULT_CONFIG, **(old_config or {}), **read_config()}
    body = tk.Frame(win, padx=12, pady=8)
    body.pack(fill=tk.BOTH, expand=True)

    if install_mode:
        tk.Label(body, text=intro, font=("Segoe UI", 10), justify=tk.LEFT, wraplength=480).pack(anchor=tk.W, pady=(0, 6))

    def section(title):
        frame = tk.LabelFrame(body, text=title, font=("Segoe UI", 9, "bold"), padx=8, pady=4)
        frame.pack(fill=tk.X, pady=4)
        return frame

    # Avvio automatico e collegamenti: lo stato viene letto dal sistema
    f = section("Avvio")
    v_auto = tk.BooleanVar(win, first_install or autostart_enabled())
    v_menu = tk.BooleanVar(win, first_install or shortcut_exists("menu"))
    v_desk = tk.BooleanVar(win, first_install or shortcut_exists("desktop"))
    menu_name = "menu Start" if IS_WINDOWS else "menu delle applicazioni"
    for text, var in (("Cambia sfondo a ogni accesso", v_auto),
                      (f"Collegamento a questa finestra nel {menu_name}", v_menu),
                      ("Collegamento a questa finestra sul desktop", v_desk)):
        tk.Checkbutton(f, text=text, variable=var, font=FONT).pack(anchor=tk.W)

    f = section("Fonti")
    tk.Label(f, text="Chiave Unsplash (facoltativa: senza, le immagini arrivano solo dalla NASA)",
             font=FONT, justify=tk.LEFT, wraplength=480).pack(anchor=tk.W)
    entry_key = tk.Entry(f, width=48, font=FONT)
    entry_key.insert(0, unsplash_key(cfg))
    entry_key.pack(fill=tk.X, pady=2)
    link = tk.Label(f, text="Ottieni una chiave gratuita (Register → New Application → Access Key)",
                    fg="blue", cursor="hand2", font=("Segoe UI", 9, "underline"))
    link.pack(anchor=tk.W)
    link.bind("<Button-1>", lambda e: webbrowser.open("https://unsplash.com/developers"))

    v_accent = tk.BooleanVar(win, cfg.get("colore_accento", True))
    if IS_WINDOWS:
        f = section("Aspetto")
        tk.Checkbutton(f, text="Usa il colore dello sfondo come colore d'accento di Windows",
                       variable=v_accent, font=FONT).pack(anchor=tk.W)

    f = section("Cartelle")
    row = tk.Frame(f)
    row.pack(fill=tk.X)
    tk.Button(row, text="📁 Apri cartella del programma", font=FONT,
              command=lambda: open_path(BASE_DIR)).pack(side=tk.LEFT, padx=(0, 4), pady=2)
    tk.Button(row, text="🖼️ Apri cartella immagini", font=FONT,
              command=lambda: (IMAGES_DIR.mkdir(exist_ok=True), open_path(IMAGES_DIR))).pack(side=tk.LEFT, pady=2)
    tk.Label(f, text=str(BASE_DIR), fg="gray", font=("Segoe UI", 8), justify=tk.LEFT, wraplength=480).pack(anchor=tk.W)

    if not install_mode:
        f = section("Versione")
        tk.Label(f, text=version_text(local_version()), font=FONT).pack(anchor=tk.W)
        row = tk.Frame(f)
        row.pack(fill=tk.X)
        btn_check = tk.Button(row, text="🔍 Controlla aggiornamenti", font=FONT)
        btn_check.pack(side=tk.LEFT, padx=(0, 4), pady=2)
        btn_update = tk.Button(row, text="⬇️ Aggiorna", font=FONT, state=tk.DISABLED)
        btn_update.pack(side=tk.LEFT, pady=2)
        lbl_update = tk.Label(f, text="", font=("Segoe UI", 9, "italic"))
        lbl_update.pack(anchor=tk.W)
        found = {}

        def set_status(text, color):
            if lbl_update.winfo_exists():
                lbl_update.config(text=text, fg=color)

        def checked(update, error):
            btn_check.config(state=tk.NORMAL)
            if error:
                set_status("⚠️ Impossibile controllare (connessione assente?)", "red")
            elif update:
                found["update"] = update
                set_status(f"🆕 Nuova versione disponibile ({update.get('totale', len(update['novita']))} modifiche)", "green")
                btn_update.config(state=tk.NORMAL)
            else:
                set_status("✅ Il programma è aggiornato", "green")

        def check():
            btn_check.config(state=tk.DISABLED)
            set_status("⏳ Controllo in corso...", "blue")
            run_in_background(root, check_update, checked)

        btn_check.config(command=check)
        btn_update.config(command=lambda: ask_and_update(root, win, found["update"], set_status))

    def save():
        # Su Windows ogni collegamento passa da PowerShell e ci mette qualche secondo: il lavoro va in un thread,
        # intanto la finestra dice cosa sta facendo e non accetta altri clic
        key, accent, auto = entry_key.get().strip() or UNSPLASH_KEY_PLACEHOLDER, v_accent.get(), v_auto.get()
        shortcuts = {"menu": v_menu.get(), "desktop": v_desk.get()}
        for button in buttons:
            button.config(state=tk.DISABLED)
        lbl_saving.config(text="⏳ Salvataggio in corso...")
        win.config(cursor="watch")
        win.protocol("WM_DELETE_WINDOW", lambda: None)

        def work():
            # Senza config.json si parte da quello mostrato, che contiene anche le categorie della vecchia installazione
            new_cfg = load_config() if CONFIG_FILE.exists() else dict(cfg)
            new_cfg["UNSPLASH_API_KEY"] = key
            new_cfg["colore_accento"] = accent
            # Tutto viene riscritto anche se non e' cambiato: cosi' i collegamenti puntano sempre a questa cartella
            done = {"config.json": save_config(new_cfg), "avvio automatico": set_autostart(auto)}
            links = set_shortcuts(shortcuts)
            done[f"collegamento nel {menu_name}"] = links["menu"]
            done["collegamento sul desktop"] = links["desktop"]
            return [name for name, ok in done.items() if not ok]

        def saved(failed, error):
            win.config(cursor="")
            if error:
                failed = ["impostazioni"]
            if failed:
                messagebox.showwarning("Impostazioni", "Non è stato possibile impostare: " + ", ".join(failed), parent=win)
            on_close(True)
        run_in_background(root, work, saved)

    def do_uninstall():
        if not messagebox.askyesno("Disinstalla", "Vuoi togliere l'avvio automatico e i collegamenti?", parent=win):
            return
        delete = is_install_dir() and messagebox.askyesno(
            "Disinstalla", f"Vuoi cancellare anche la cartella del programma, con immagini e statistiche?\n\n{BASE_DIR}", parent=win)
        ok = uninstall(delete)
        msg = "APOD Wallpaper è stato disinstallato." if ok else "Alcuni collegamenti non sono stati tolti."
        if not delete:
            msg += f"\n\nI file sono rimasti in:\n{BASE_DIR}"
        win.destroy()
        if IS_WINDOWS:
            # Explorer, aggiornando il desktop senza i collegamenti, puo' passare davanti alla finestra:
            # MessageBoxW di show_popup resta in primo piano
            root.withdraw()
            show_popup("Disinstalla", msg)
        else:
            messagebox.showinfo("Disinstalla", msg, parent=root)
        root.destroy()

    bottom = tk.Frame(win, padx=12, pady=8)
    bottom.pack(fill=tk.X)
    buttons = []
    if not install_mode:
        buttons.append(tk.Button(bottom, text="🗑️ Disinstalla...", font=FONT, command=do_uninstall))
        buttons[-1].pack(side=tk.LEFT)
    buttons.append(tk.Button(bottom, text="Installa" if first_install else "Salva", font=FONT, width=12, bg="#e5ffe5",
                             command=save))
    buttons[-1].pack(side=tk.RIGHT, padx=(4, 0))
    buttons.append(tk.Button(bottom, text="Annulla", font=FONT, width=10, command=lambda: on_close(False)))
    buttons[-1].pack(side=tk.RIGHT)
    lbl_saving = tk.Label(bottom, text="", fg="blue", font=("Segoe UI", 9, "italic"))
    lbl_saving.pack(side=tk.RIGHT, padx=4)
    win.protocol("WM_DELETE_WINDOW", lambda: on_close(False))

def install():
    # Finestra aperta dagli installer (--installa): solo le impostazioni, poi, alla prima installazione,
    # la finestra principale. Gli installer passano --precedente=<commit> se c'era gia' una versione.
    first_install = not CONFIG_FILE.exists()
    previous = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--precedente=")), "")
    unchanged = previous and previous == (local_version() or {}).get("commit")
    old_config = None
    if first_install:
        title = "Installazione APOD Wallpaper"
        intro = ("Scegli come usare APOD Wallpaper e premi Installa: il primo sfondo arriva subito dopo.\n"
                 "Potrai cambiare tutto in seguito dal pulsante Impostazioni.")
        # Versione precedente installata a mano: chiave, categorie e statistiche passano qui
        old_dir = find_old_install()
        if old_dir:
            old_config = import_old_install(old_dir)
            intro += (f"\n\nChiave Unsplash, categorie e statistiche sono state prese dalla versione precedente, in:\n"
                      f"{old_dir}\nDopo l'installazione puoi cancellare quella cartella.")
    elif unchanged:
        title = "APOD Wallpaper"
        intro = "APOD Wallpaper è già all'ultima versione. Qui sotto puoi cambiare le impostazioni."
    else:
        title = "APOD Wallpaper aggiornato"
        intro = "Aggiornamento completato. Le impostazioni sono rimaste quelle di prima."
    root = tk.Tk()
    setup_window(root)
    root.title(title)
    root.resizable(False, False)
    # La finestra principale, se e' aperta, sta sempre in primo piano e coprirebbe questa
    root.attributes("-topmost", True)

    def close(saved):
        if saved and first_install:
            # La finestra principale scarica subito il primo sfondo. Dopo un aggiornamento non si apre:
            # potrebbe essere gia' aperta e ne comparirebbe una seconda
            restart_ui(root, "--primo-sfondo")
        else:
            root.destroy()

    build_settings(root, root, close, intro=intro, first_install=first_install, old_config=old_config)
    center(root)
    root.mainloop()

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
    if "--installa" in sys.argv:
        install()
        return

    root = tk.Tk()
    setup_window(root)
    
    info = get_current_wallpaper_info()
    
    # Dimensionamento e centratura finestra
    window_width = 340
    window_height = 350
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    if IS_WINDOWS:
        root.geometry(f'{window_width}x{window_height}+{x}+{y}')
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.title("Valutazione Sfondo")

    # Banda mostrata solo se su GitHub c'e' una versione piu' recente
    banner = tk.Frame(root, bg="#fff4cc")
    tk.Label(banner, text="🆕 È disponibile un aggiornamento", bg="#fff4cc", font=FONT).pack(side=tk.LEFT, padx=6, pady=4)
    btn_update = tk.Button(banner, text="Aggiorna", font=FONT)
    btn_update.pack(side=tk.RIGHT, padx=6, pady=4)

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

    btn_manage = tk.Button(btn_frame, text="📊 Statistiche", width=16, bg="#f3e5ff", font=("Segoe UI", 9))
    btn_manage.grid(row=2, column=0, padx=5, pady=5)

    btn_settings = tk.Button(btn_frame, text="⚙️ Impostazioni", width=16, bg="#f0f0f0", font=("Segoe UI", 9))
    btn_settings.grid(row=2, column=1, padx=5, pady=5)

    btn_prev = tk.Button(btn_frame, text="⬅️ Precedente", width=16, bg="#f0f0f0", font=("Segoe UI", 9))
    btn_prev.grid(row=3, column=0, padx=5, pady=5)

    btn_next = tk.Button(btn_frame, text="Successivo ➡️", width=16, bg="#f0f0f0", font=("Segoe UI", 9))
    btn_next.grid(row=3, column=1, padx=5, pady=5)

    lbl_status = tk.Label(root, text="", font=("Segoe UI", 9, "italic"))
    lbl_status.pack(pady=2)

    all_buttons = (btn_dislike, btn_like, btn_change, btn_info, btn_manage, btn_settings, btn_prev, btn_next)

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
        btn_settings.config(state=tk.NORMAL)
        
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
            proc = subprocess.Popen([sys.executable, str(APOD_SCRIPT)], cwd=str(BASE_DIR), **BG_PROCESS)
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
            make_modal(info_win)
            
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
        make_modal(manage_win)

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

        if not IS_WINDOWS:
            # Con il font di Linux la misura fissa tagliava "Salva e Chiudi": allarga se serve
            manage_win.update_idletasks()
            manage_win.geometry(f"{max(600, manage_win.winfo_reqwidth())}x{max(450, manage_win.winfo_reqheight())}")

    def open_settings():
        settings_win = tk.Toplevel(root)
        settings_win.title("Impostazioni")
        settings_win.resizable(False, False)
        settings_win.transient(root)

        def close(saved):
            settings_win.destroy()
            if saved:
                refresh_ui("✅ Impostazioni salvate", "green")

        build_settings(root, settings_win, close)
        # Senza posizione Tk su Windows la apre nell'angolo in alto a sinistra dello schermo
        center(settings_win)
        make_modal(settings_win)

    def show_banner(update, error):
        if error or not update: return
        btn_update.config(command=lambda: ask_and_update(root, root, update, lambda t, c: lbl_status.config(text=t, fg=c)))
        banner.pack(fill=tk.X, before=lbl_title)
        if IS_WINDOWS:
            # Su Windows la finestra ha una misura fissa: va allungata per far posto alla banda
            root.update_idletasks()
            root.geometry(f"{window_width}x{window_height + banner.winfo_reqheight()}")

    btn_dislike.config(command=lambda: action("dislike"))
    btn_like.config(command=lambda: action("like"))
    btn_change.config(command=lambda: action("change"))
    btn_info.config(command=lambda: action("open_txt"))
    btn_manage.config(command=manage_categories)
    btn_settings.config(command=open_settings)
    btn_prev.config(command=lambda: cycle_wallpaper(-1))
    btn_next.config(command=lambda: cycle_wallpaper(1))

    refresh_ui()

    if not IS_WINDOWS:
        # Su Linux Segoe UI manca e il font sostitutivo e' piu' largo: la misura fissa tagliava
        # i pulsanti, quindi la finestra prende quella richiesta dai widget e si centra
        center(root)

    # Il controllo degli aggiornamenti non rallenta l'apertura: gira in un thread
    run_in_background(root, check_update, show_banner)
    if "--primo-sfondo" in sys.argv:
        root.after(300, run_apod)

    root.mainloop()

if __name__ == "__main__":
    main()
