# Verifica su Windows del ramo `bilingue`

Partenza dal commit `c17ddfd`, istruzioni in `istruzioni-windows.md`.

## Ambiente

- Windows 11 Home 10.0.26300, lingua dell'interfaccia `it-IT`, schermo con scala al 125% (120 DPI).
- Python 3.14.3 per l'utente (`%LOCALAPPDATA%\Programs\Python\Python314`), con Tk. PowerShell 5.1.26100.
- C'era già una versione installata a mano seguendo il vecchio ReadMe: il clone in `Documents\APOD_wallpaper`, con `config.json` e `statistiche.json`, `Cambia sfondo.lnk` sul Desktop ed `apod.pyw - collegamento.lnk` in Esecuzione automatica.

## Come sono state guidate le finestre

`irm ... | iex` è stato bloccato dai permessi della sessione: lo script è stato scaricato, confrontato con quello del ramo (identico) e lanciato con `Get-Content -Raw ... | Invoke-Expression`, che lo legge da `iex` dentro il blocco `& { }` esattamente come `irm | iex`.

Le finestre Tk sono state guidate da un piccolo harness: carica `cambia_sfondo.pyw` dalla cartella di prova, al posto del `mainloop` esegue i passi (clic con `invoke()`, lettura dei testi, delle caselle e del campo della chiave) e prende gli screenshot da un processo esterno DPI-aware, che legge anche `-topmost` e centratura della finestra vera. Le `messagebox` di Tk sono simulate (testo registrato, risposta scelta dal piano); il `MessageBoxW` della disinstallazione è quello vero, fotografato e chiuso da un thread. Le finestre riaperte da `restart_ui` sono processi veri, controllati con gli screenshot. L'apertura dal menu Start è vera (tasto Win, nome, Invio).

## Risultati

| Passo | Esito | Dettagli |
|---|---|---|
| 1. Controlli statici | OK | I quattro file passano `ast.parse`. 100 frasi in `tr(` e 100 chiavi in `EN`: nessuna mancante, nessuna avanzata, stessi segnaposto, nessun `tr` con argomento non costante. `system_language()` = `it`. Ripetuto dopo le correzioni. |
| 2. Installer, italiano | OK | Gira fino in fondo su PowerShell 5.1, messaggi in italiano, `T` funziona dentro `& { }` letto da `iex`. `testi.py` copiato in `%LOCALAPPDATA%\APOD_wallpaper`, `versione.json` senza BOM. |
| 2. Installer, inglese | OK | Con `$it = $false` tutti i messaggi in inglese. Con un ramo inesistente: "Download failed: check your connection and try again (branch ...)" più i dettagli (422). |
| 2. Vecchia installazione | Corretto | La finestra di installazione non diceva di aver trovato il clone: nei due `.lnk` il percorso locale non c'è, c'è solo quello di rete (`\\DESKTOP-...\Users` + `Francesco\Documents\...`) e uno relativo. Corretto in `7f3555b`; dopo la correzione il clone viene trovato e chiave, categorie e statistiche passano all'installazione. |
| 3. Finestra di installazione | OK | Titolo "Installazione APOD Wallpaper", "🌐 Lingua / Language" in cima con "Italiano" selezionato. Tolta una casella e scritta una chiave, "English" mostra "APOD Wallpaper Setup" e "Install", con caselle e chiave conservate; tornando a "Italiano" idem. Sempre `-topmost`, centrata, nessun testo tagliato. "Annulla" non crea `config.json`. |
| 4. Impostazioni, Annulla | OK | "English" → "Cancel": la finestra principale resta in italiano e riaprendo le Impostazioni è selezionato "Italiano". |
| 4. Impostazioni, Save | OK | La finestra principale si riapre in inglese ("Rate Wallpaper"). Nel menu Start e sul Desktop c'è solo `Change Wallpaper.lnk`: destinazione `pythonw.exe`, argomenti, cartella di lavoro e icona come prima, `Description` = "Rate and change the wallpaper". `config.json`: `"lingua": "en"`. |
| 4. Di nuovo in italiano | OK | "Salva" riporta solo `Cambia Sfondo.lnk` con "Valuta e cambia lo sfondo". |
| 4. Entrambi i nomi | OK | Con i due nomi presenti `set_shortcuts({"menu": False, "desktop": False})` li toglie tutti; con il solo nome inglese `shortcut_exists` dà `True` per menu e desktop. |
| 4. `.lnk` appena usato | OK | Finestra aperta dal menu Start e subito dopo `set_shortcuts` con cambio di nome: riuscito in 1,9 s. |
| 5. Finestra principale in inglese | OK | 340x350 (logici) senza testi tagliati, anche con la banda di aggiornamento (simulata), con "👍 Like!\n(Already rated)" e "🔄 Change\n(Without rating)". Le scritte di stato inglesi sono tutte più corte o poco più lunghe delle italiane (la più lunga, "⚠️ No wallpaper found, try again later", 205 px su 340). |
| 5. Open info, Statistics, Settings | Corretto | Testi inglesi interi, "Unsplash Themes" / "NASA Queries", "+ Add", "- Remove", "Save and Close". Però "Wallpaper Info" e "Categories & Statistics" si aprivano in alto a sinistra e la finestra principale, `-topmost`, ne copriva una parte (la tabella "NASA Queries"). Il difetto non dipende dalla lingua. Corretto in `7f57639`. |
| 6. Aggiornamento da `master` | OK | Installata la versione di `master` (`eb61324`), tolti `testi.py` e `"lingua"`, `"ramo": "bilingue"`. Banda "Aggiorna" comparsa, novità elencate, aggiornamento riuscito; la finestra si riapre senza errori in italiano e `testi.py` c'è. `"lingua"` compare nel config alla prima esecuzione di `apod.pyw` (provato con `--prefetch`): la finestra principale non chiama `load_config`, e fino ad allora vale la lingua del sistema, cioè lo stesso valore. |
| 7. Disinstalla in inglese | OK | "Remove auto-start and shortcuts?", "Also delete the program folder, ...?" e il `MessageBoxW` finale ("APOD Wallpaper has been uninstalled. ...") in inglese. Tolti collegamenti (erano quelli italiani, con la lingua inglese) e avvio automatico. Cartella non cancellata, per tenere config e statistiche. |
| 8. Fine | OK | Reinstallato dal ramo, Impostazioni in italiano con tutte le caselle, avvio automatico e collegamenti attivi, `versione.json` con `"ramo": "master"`. Finestra aperta dal menu Start con `pythonw`: funziona. |

## Correzioni

| Commit | Cosa |
|---|---|
| `7f3555b` | `find_old_install` su Windows legge destinazione e argomenti dei `.lnk` con un solo PowerShell + `WScript.Shell` (output in UTF-8) invece di cercare il percorso nei byte, dove può mancare. Circa 1-2 s in più, solo alla prima installazione. `AGENTS.md` aggiornato. |
| `7f57639` | `make_modal` su Windows rende la finestra `transient` della principale, come già le Impostazioni, così resta sopra di lei. `center` accetta una misura: info (500x400) e statistiche (600x450) si aprono centrate. Con una misura `center` non chiama `update_idletasks`, perché su Windows `transient` vale solo se arriva prima che la finestra sia mostrata. |

Lasciati com'erano: il 🌐 del titolo della sezione lingua è il mappamondo monocromo di Segoe UI Symbol, come le altre emoji delle finestre; il messaggio dell'installer per un ramo inesistente parla di connessione, ma riporta ramo e dettagli dell'errore.
