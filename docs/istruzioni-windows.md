# Verifica su Windows del ramo `bilingue`

Istruzioni per la sessione Claude Code su Windows. Il ramo aggiunge l'inglese all'interfaccia: la lingua si sceglie nella finestra di installazione e nelle Impostazioni. Il commit della funzione è `30db595`. La cartella `docs/` non finisce nelle installazioni (gli installer copiano solo i file della radice) e verrà tolta prima del merge.

**Questo è l'unico giro.** L'utente non vuole passaggi avanti e indietro tra Linux e Windows: correggi tu quello che trovi (vedi "Alla fine").

## Cosa è cambiato

Leggi la sezione "Lingua" di `AGENTS.md`. In breve:

- `testi.py` (nuovo) contiene solo `EN = {"frase italiana": "English text"}`. In `comune.py` ci sono `LINGUE`, `system_language()` (su Windows `GetUserDefaultUILanguage() & 0x3FF == 0x10`), `language()`, `set_language()` e `tr(testo, **valori)`. La lingua sta in `config.json` (`"lingua": "it"` / `"en"`); se manca vale quella del sistema e `load_config` la aggiunge.
- Tutti i testi visibili di `cambia_sfondo.pyw`, i popup e i messaggi di `comune.py` e la descrizione Unsplash di `apod.pyw` passano per `tr`.
- `build_settings` ha come prima sezione "🌐 Lingua / Language". Cambiando lingua la finestra si riempie di nuovo subito (`rebuild` → `fill` del chiamante, con le scelte già fatte in `values`). "Annulla" rimette la lingua di prima; "Salva" la scrive e, se è cambiata, riapre la finestra principale con `restart_ui`.
- **Solo Windows, non provato:** il `.lnk` si chiama `Cambia Sfondo.lnk` o `Change Wallpaper.lnk` secondo la lingua (`shortcut_path(where, lingua)`). `set_shortcuts` toglie sempre i collegamenti in tutte e due le lingue (`_shortcut_paths`) prima di creare quello nuovo; `shortcut_exists` li cerca entrambi. La `Description` del `.lnk` arriva a PowerShell nella variabile `APOD_DESC`.
- `installa.ps1`: `$it = (Get-UICulture).TwoLetterISOLanguageName -eq 'it'` e `function T($testoIt, $testoEn)`; ogni `Write-Host` passa per `T`. Lo script è solo ASCII. **Non provato**: qui non c'è PowerShell.

## Già provato su Linux

Copia in una cartella temporanea e `HOME` finta: copertura delle traduzioni (nessuna frase senza traduzione, nessuna avanzata, stessi segnaposto), `system_language()` con `LANG` italiano, inglese e tedesco, finestra di installazione con il cambio it→en (caselle e chiave conservate, config con `"lingua": "en"`, `.desktop` con `Name=Change Wallpaper`), Impostazioni con "Annulla" (lingua ripristinata) e "Salva" (finestra principale riaperta, collegamento rinominato), screenshot di finestra principale, Impostazioni e Statistiche in inglese senza testi tagliati. Su Linux però le finestre prendono la misura richiesta dai widget, su Windows la finestra principale ha una misura fissa: lì va controllato.

## Preparazione

- `git fetch && git checkout bilingue && git pull`. Serve il commit che contiene questo file.
- L'utente non vuole accorgimenti: puoi cambiare sfondo, lingua, collegamenti, avvio automatico e installazione quanto serve per i test, senza backup e senza chiedere conferma.

## Cosa verificare

1. **Controlli statici.** `python -c "import ast; [ast.parse(open(f, encoding='utf-8').read()) for f in ('comune.py', 'apod.pyw', 'cambia_sfondo.pyw', 'testi.py')]"`. Poi, con `ast`, raccogli le stringhe passate a `tr(` nei tre file Python e confrontale con le chiavi di `EN`: non ne deve mancare nessuna. `python -c "import comune; print(comune.system_language())"` deve dare `it` se Windows è in italiano.

2. **Installer.** Con l'installazione vera:
   - `$env:APOD_RAMO = 'bilingue'` e poi `irm https://raw.githubusercontent.com/francescodrnz/APOD_wallpaper/bilingue/installa.ps1 | iex` (prendi lo script dal ramo, non da `master`). Deve girare fino in fondo su PowerShell 5.1 con i messaggi in italiano; `T` deve funzionare anche dentro il blocco `& { }` letto da `iex`. In `%LOCALAPPDATA%\APOD_wallpaper` deve esserci `testi.py`.
   - Messaggi inglesi senza cambiare la lingua di Windows: scarica `installa.ps1` in una cartella temporanea, sostituisci la riga di `$it` con `$it = $false` e lancialo con `$env:APOD_RAMO = 'bilingue'`. Controlla che i messaggi siano in inglese. Per vedere anche il messaggio di errore, prova un ramo che non esiste.

3. **Finestra di installazione, prima installazione.** Senza toccare il sistema: copia `*.py`, `*.pyw` e `icona.*` in una cartella temporanea senza `config.json` e lancia `pythonw cambia_sfondo.pyw --installa`.
   - Titolo "Installazione APOD Wallpaper", sezione "🌐 Lingua / Language" in cima, "Italiano" selezionato.
   - Togli una casella e scrivi qualcosa nella chiave, poi passa a "English": tutti i testi in inglese ("APOD Wallpaper Setup", pulsante "Install"), le caselle e la chiave come le avevi lasciate. La finestra deve restare in primo piano (`-topmost`), centrata, senza testi tagliati. Torna a "Italiano" e ricontrolla.
   - Chiudi con **Annulla**: nella cartella temporanea non deve comparire `config.json`.

4. **Impostazioni e collegamenti** (sull'installazione vera).
   - Apri la finestra principale dal menu Start → "⚙️ Impostazioni" → "English" → **Annulla**. La finestra principale deve restare in italiano; riaprendo le Impostazioni, la lingua selezionata è "Italiano".
   - "⚙️ Impostazioni" → "English" → **Save**. La finestra principale si deve riaprire in inglese. Nel menu Start e sul Desktop deve esserci solo `Change Wallpaper.lnk`, senza `Cambia Sfondo.lnk`. Controlla con `WScript.Shell` destinazione, argomenti, cartella di lavoro e icona (uguali a prima) e `Description` = "Rate and change the wallpaper". In `config.json`: `"lingua": "en"`.
   - Di nuovo in italiano con "Salva": deve tornare solo `Cambia Sfondo.lnk`, con la descrizione italiana.
   - Con entrambi i nomi presenti (copia a mano il `.lnk` con l'altro nome), `set_shortcuts({"menu": False, "desktop": False})` deve toglierli tutti e due. Con il solo nome inglese presente, `shortcut_exists` deve dare `True`.
   - Il menu Start appena aggiornato può tenere il `.lnk` aperto per qualche istante: `_unlink` riprova per circa 5 s. Controlla che il cambio di nome riesca anche subito dopo aver aperto la finestra dal collegamento.

5. **Finestre in inglese a misura fissa.** Con la lingua inglese:
   - Finestra principale (340x350 fissa su Windows): niente pulsanti o testi tagliati, in particolare "🔄 Change\n(Without rating)", "👍 Like!\n(Already rated)" e "What to do with this wallpaper?". Prova anche con la banda dell'aggiornamento (punto 6).
   - "📄 Open info", "📊 Statistics" (600x450: intestazioni "Unsplash Themes" / "NASA Queries", "+ Add", "- Remove", "Save and Close"), "⚙️ Settings", e le scritte di stato ("⏳ Downloading wallpaper... (Ns)", "✅ Wallpaper changed!").
   - Controlla con gli screenshot. Se qualcosa è tagliato, accorcia il testo inglese in `testi.py`: non cambiare le misure delle finestre.

6. **Aggiornamento da una versione senza lingua.** È il percorso degli utenti attuali: il vecchio `apply_update` deve portare anche `testi.py`.
   - Installa la versione di `master` (installer senza `APOD_RAMO`). Cancella `testi.py`, rimasto dal punto 2 (l'installer copia i file ma non toglie quelli in più), e togli `"lingua"` dal config se c'è.
   - In `versione.json` metti `"ramo": "bilingue"` lasciando il commit di `master`. Riapri la finestra principale: deve comparire la banda "Aggiorna". Premi e accetta.
   - La finestra si deve riaprire senza errori, nella lingua di sistema. Nel config deve comparire `"lingua"`, e `testi.py` deve essere nella cartella.

7. **Disinstalla in inglese:** i messaggi sono in inglese, `MessageBoxW` compreso, e spariscono i collegamenti in tutte e due le lingue e l'avvio automatico. Poi reinstalla.

8. **Fine.** Lascia il programma installato e funzionante, con le impostazioni che preferisci. In `versione.json` metti `"ramo": "master"`, altrimenti dopo il merge l'installazione cercherebbe gli aggiornamenti su un ramo che non c'è più.

## Alla fine: unico giro

- **Correggi tu ogni problema**, anche piccolo e anche di UX: non scrivere proposte né decisioni da prendere. Se c'è da scegliere, scegli la soluzione più semplice e scrivi il motivo nel messaggio di commit.
- Testi nuovi o cambiati: in italiano dentro `tr(...)`, con la traduzione in `EN` in `testi.py`. Ripeti il controllo del punto 1.
- Se tocchi codice condiviso, metti le modifiche nel ramo Windows (`if IS_WINDOWS` / sotto `if not IS_WINDOWS:`) quando puoi. Se devi cambiare codice comune ai due sistemi, fai la modifica più piccola possibile e controlla con `ast.parse` che i file restino validi.
- Aggiorna `AGENTS.md` se cambia qualcosa di quello che descrive. Se cambi qualcosa che l'utente vede, aggiorna sia `ReadMe.md` sia `LeggiMi.md`.
- Commit in italiano, Conventional Commits, una riga.
- Scrivi i risultati in `docs/verifica-windows.md`: ambiente, tabella passo/esito/dettagli, correzioni fatte con il loro commit.
- In `docs/da-windows.md` scrivi **una volta sola**, in una sezione datata con il commit di partenza: cosa hai cambiato nel codice condiviso e cosa va ricontrollato su Linux. Niente proposte, domande o decisioni. La sessione Linux sistema quello che resta, toglie `docs/` e fa il merge su `master` senza rimandare niente a Windows.
- Fai commit e push sul ramo `bilingue`.
- All'utente di' una riga sola: il ramo è pronto per il merge, oppure c'è qualcosa in `docs/da-windows.md` per la sessione Linux.
