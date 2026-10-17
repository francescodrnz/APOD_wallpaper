"""Traduzioni inglesi dei testi dell'interfaccia, usate da tr() in comune.py.

La chiave e' la frase italiana scritta nel codice: una frase che manca qui resta in italiano.
I segnaposto tra graffe ({cartella}, {n}...) vanno lasciati uguali nella traduzione.
"""

EN = {
    # --- comune.py ---
    "Errore Critico": "Critical Error",
    "Impossibile creare {file}": "Cannot create {file}",
    "Errore Config": "Config Error",
    "File config.json corrotto: {errore}": "Corrupted config.json file: {errore}",
    "Sfondo Sconosciuto": "Unknown Wallpaper",
    "Sconosciuto": "Unknown",
    "Nessuna informazione disponibile per questo sfondo.": "No information available for this wallpaper.",
    "Cambia lo sfondo all'accesso": "Changes the wallpaper at login",
    "Cambia Sfondo": "Change Wallpaper",
    "Valuta e cambia lo sfondo": "Rate and change the wallpaper",
    "git pull non riuscito: {errore}": "git pull failed: {errore}",
    "git pull non riuscito": "git pull failed",
    "Aggiornamento non riuscito: {errore}": "Update failed: {errore}",

    # --- apod.pyw ---
    "Nessuna descrizione disponibile.": "No description available.",

    # --- cambia_sfondo.pyw: versione e aggiornamenti ---
    "Versione sconosciuta": "Unknown version",
    "Versione {commit} del {data} (ramo {ramo})": "Version {commit} from {data} (branch {ramo})",
    "Versione {commit} (ramo {ramo})": "Version {commit} (branch {ramo})",
    "... e altre {n} modifiche precedenti": "... and {n} earlier changes",
    "Aggiornamento disponibile": "Update available",
    "Novità:\n\n{elenco}\n\nVuoi aggiornare ora?": "What's new:\n\n{elenco}\n\nUpdate now?",
    "⏳ Aggiornamento in corso...": "⏳ Updating...",
    "⚠️ Aggiornamento non riuscito": "⚠️ Update failed",
    "Aggiornamento non riuscito": "Update failed",
    "Aggiornamento completato": "Update complete",
    "La finestra si riapre con la nuova versione.": "The window will reopen with the new version.",
    "🆕 È disponibile un aggiornamento": "🆕 An update is available",
    "Aggiorna": "Update",

    # --- cambia_sfondo.pyw: impostazioni ---
    "Impostazioni": "Settings",
    "Avvio": "Startup",
    "menu Start": "Start menu",
    "menu delle applicazioni": "applications menu",
    "Cambia sfondo a ogni accesso": "Change wallpaper at every login",
    "Collegamento a questa finestra nel {menu}": "Shortcut to this window in the {menu}",
    "Collegamento a questa finestra sul desktop": "Shortcut to this window on the desktop",
    "Fonti": "Sources",
    "Chiave Unsplash (facoltativa: senza, le immagini arrivano solo dalla NASA)":
        "Unsplash key (optional: without it, images come only from NASA)",
    "Ottieni una chiave gratuita (Register → New Application → Access Key)":
        "Get a free key (Register → New Application → Access Key)",
    "Aspetto": "Appearance",
    "Usa il colore dello sfondo come colore d'accento di Windows": "Use the wallpaper color as the Windows accent color",
    "Cartelle": "Folders",
    "📁 Apri cartella del programma": "📁 Open program folder",
    "🖼️ Apri cartella immagini": "🖼️ Open images folder",
    "Versione": "Version",
    "🔍 Controlla aggiornamenti": "🔍 Check for updates",
    "⬇️ Aggiorna": "⬇️ Update",
    "⚠️ Impossibile controllare (connessione assente?)": "⚠️ Could not check (no connection?)",
    "🆕 Nuova versione disponibile ({n} modifiche)": "🆕 New version available ({n} changes)",
    "✅ Il programma è aggiornato": "✅ The program is up to date",
    "⏳ Controllo in corso...": "⏳ Checking...",
    "⏳ Salvataggio in corso...": "⏳ Saving...",
    "avvio automatico": "auto-start",
    "collegamento nel {menu}": "shortcut in the {menu}",
    "collegamento sul desktop": "desktop shortcut",
    "impostazioni": "settings",
    "Non è stato possibile impostare: {elenco}": "Could not set: {elenco}",
    "Disinstalla": "Uninstall",
    "🗑️ Disinstalla...": "🗑️ Uninstall...",
    "Vuoi togliere l'avvio automatico e i collegamenti?": "Remove auto-start and shortcuts?",
    "Vuoi cancellare anche la cartella del programma, con immagini e statistiche?\n\n{cartella}":
        "Also delete the program folder, with images and statistics?\n\n{cartella}",
    "APOD Wallpaper è stato disinstallato.": "APOD Wallpaper has been uninstalled.",
    "Alcuni collegamenti non sono stati tolti.": "Some shortcuts could not be removed.",
    "\n\nI file sono rimasti in:\n{cartella}": "\n\nThe files are still in:\n{cartella}",
    "Installa": "Install",
    "Salva": "Save",
    "Annulla": "Cancel",
    "✅ Impostazioni salvate": "✅ Settings saved",

    # --- cambia_sfondo.pyw: installazione ---
    "Installazione APOD Wallpaper": "APOD Wallpaper Setup",
    "Scegli come usare APOD Wallpaper e premi Installa: il primo sfondo arriva subito dopo.\n"
    "Potrai cambiare tutto in seguito dal pulsante Impostazioni.":
        "Choose how to use APOD Wallpaper and press Install: the first wallpaper arrives right after.\n"
        "You can change everything later from the Settings button.",
    "\n\nChiave Unsplash, categorie e statistiche sono state prese dalla versione precedente, in:\n"
    "{cartella}\nDopo l'installazione puoi cancellare quella cartella.":
        "\n\nUnsplash key, categories and statistics were taken from the previous version, in:\n"
        "{cartella}\nAfter installing you can delete that folder.",
    "APOD Wallpaper è già all'ultima versione. Qui sotto puoi cambiare le impostazioni.":
        "APOD Wallpaper is already up to date. You can change the settings below.",
    "APOD Wallpaper aggiornato": "APOD Wallpaper Updated",
    "Aggiornamento completato. Le impostazioni sono rimaste quelle di prima.":
        "Update complete. Your settings have been kept.",

    # --- cambia_sfondo.pyw: finestra principale ---
    "Valutazione Sfondo": "Rate Wallpaper",
    "Cosa vuoi fare con lo sfondo attuale?": "What to do with this wallpaper?",
    "👎 Non mi piace\n(Già valutato)": "👎 Dislike\n(Already rated)",
    "👎 Non mi piace\n(Scarta)": "👎 Dislike\n(Discard)",
    "👍 Mi piace!\n(Già valutato)": "👍 Like!\n(Already rated)",
    "👍 Mi piace!\n(Mantieni)": "👍 Like!\n(Keep)",
    "🔄 Cambia\n(Senza valutare)": "🔄 Change\n(Without rating)",
    "📄 Apri info\n(Mostra testo)": "📄 Open info\n(Show text)",
    "📊 Statistiche": "📊 Statistics",
    "⚙️ Impostazioni": "⚙️ Settings",
    "⬅️ Precedente": "⬅️ Previous",
    "Successivo ➡️": "Next ➡️",
    "⏳ Sfondo in download... ({s}s)": "⏳ Downloading wallpaper... ({s}s)",
    "✅ Sfondo cambiato con successo!": "✅ Wallpaper changed!",
    "⚠️ Nessuno sfondo trovato, riprova più tardi": "⚠️ No wallpaper found, try again later",
    "⏳ Impostazione sfondo...": "⏳ Setting wallpaper...",
    "✅ Sfondo impostato!": "✅ Wallpaper set!",
    "✅ Valutazione salvata!": "✅ Rating saved!",
    "Informazioni Sfondo": "Wallpaper Info",
    "Chiudi": "Close",

    # --- cambia_sfondo.pyw: categorie e statistiche ---
    "Gestione & Statistiche": "Categories & Statistics",
    "Gestisci le categorie e visualizza i voti (🔴 = Esclusa in automatico)":
        "Manage categories and view ratings (🔴 = excluded automatically)",
    "Categoria": "Category",
    "+ Aggiungi": "+ Add",
    "- Rimuovi": "- Remove",
    "Temi Unsplash": "Unsplash Themes",
    "Ricerche NASA": "NASA Queries",
    "Salva e Chiudi": "Save and Close",
}
