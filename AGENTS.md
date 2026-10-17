# AGENTS.md

Note per agenti di coding che lavorano su questo repository. Per l'uso lato utente vedi `ReadMe.md` (inglese) e `LeggiMi.md` (italiano).

## Cos'è

Cambia-sfondo in Python per Windows 10/11 e Linux, installabile con una riga di comando e senza git. Scarica un'immagine da una fonte casuale (NASA APOD, NASA Image Library, ESA/Hubble e ESA/Webb, Wikimedia Commons, Bing, Unsplash, Pixabay), la adatta allo schermo con un "ambient blur", la imposta come sfondo e, solo su Windows, sincronizza il colore d'accento. L'interfaccia è in italiano e in inglese. Gli stessi file girano su entrambi i sistemi e scelgono da soli il ramo giusto (vedi "Windows e Linux").

## File

| File | Ruolo |
|---|---|
| `apod.pyw` | Script headless: sceglie una fonte, scarica, ridimensiona, imposta lo sfondo, scrive i metadati, pulisce la cache e prepara in anticipo il prossimo sfondo. Pensato per l'avvio automatico al login. Con `--ciclo` resta acceso e cambia sfondo ogni N minuti (vedi "Cambio automatico"). |
| `cambia_sfondo.pyw` | Finestra Tkinter: mostra info sullo sfondo attuale, like/dislike, scorrimento avanti/indietro tra gli sfondi in cache, gestione categorie e statistiche, Impostazioni, banda di aggiornamento. Per cambiare sfondo lancia `apod.pyw` come sottoprocesso. Con `--installa` mostra solo le Impostazioni in modalità installazione (vedi "Installazione e aggiornamenti"). |
| `comune.py` | Codice condiviso dai due script: rilevamento della piattaforma (`IS_WINDOWS`, `BG_PROCESS`), installazione delle dipendenze, percorsi, lingua (`tr`, vedi "Lingua"), `config.json` (`load_config`, `read_config`, `save_config`), popup, lettura/impostazione dello sfondo, colore d'accento, statistiche e regola di esclusione, lettura/scrittura del `.txt`, storico, avvio automatico e collegamenti, disinstallazione, versione e aggiornamenti. Le funzioni usate da entrambi vanno qui, non duplicate. |
| `testi.py` | Solo la tabella `EN` delle traduzioni inglesi, con le frasi italiane come chiavi (vedi "Lingua"). |
| `installa.ps1` / `installa.sh` | Installer da una riga (`irm ... \| iex` / `curl ... \| sh`): Python o dipendenze, download dell'archivio del commit da GitHub in `INSTALL_DIR`, `versione.json`, poi `cambia_sfondo.pyw --installa`. |
| `icona.png` / `icona.ico` | Icona di finestre e collegamenti (`.png` per Tk e Linux, `.ico` per i `.lnk` di Windows). |
| `config.json` | Chiavi Unsplash e Pixabay (opzionali), `lingua` (`it` / `en`), `colore_accento`, `cambio_automatico_minuti` e liste di categorie. **Ignorato da git, contiene segreti: non committarlo e non riportarne il contenuto.** Viene generato in silenzio al primo avvio. |
| `versione.json` | `{commit, ramo, data}` della versione installata, scritto dagli installer e da `apply_update`. Ignorato da git; manca nei clone, dove la versione si legge da git. |
| `statistiche.json` | Voti per categoria (`positivi` / `scarti`). Ignorato da git. |
| `apod_images/` | Cache locale di immagini e metadati. Ignorata da git. |
| `ReadMe.md` / `LeggiMi.md` | Istruzioni per l'utente in inglese e in italiano: vanno tenute allineate. |

## Flusso di `apod.pyw`

1. L'import di `comune` esegue `install_dependencies()`, che installa in silenzio `requests` e `pillow` se mancano. Per questo `comune` va importato prima di loro.
2. `load_config()` (in `comune.py`) crea `config.json` in silenzio, oppure aggiunge le chiavi mancanti prendendole da `DEFAULT_CONFIG`.
3. `main()` controlla prima l'APOD del giorno (`todays_apod`, vedi sotto): se non è ancora stata sfondo la scarica al momento con `prepare_image(IMAGES_DIR, data)`. Altrimenti prende lo sfondo già pronto in `apod_images/prossimo/` (`take_prefetched`); se non c'è, lo prepara al momento con `prepare_image`. Poi avvia `apod.pyw --prefetch` come processo separato, e infine chiama `set_wallpaper`, `mark_apod_seen`, `update_windows_accent` e `cleanup` (tiene i 12 file `wallpaper_*` più recenti, cioè circa 6 coppie immagine/testo, oltre allo sfondo corrente).
4. `prepare_image` → `find_image` mescola le fonti `[get_apod_data, get_unsplash_image, get_pixabay_image, get_nasa_image_library, get_esa_image, get_wikimedia_image, get_bing_image]` e prova ognuna fino a `MAX_RETRIES` volte. Per APOD sono tutte date casuali dal 1995 a ieri: l'immagine di oggi passa solo da `todays_apod`. Ogni funzione sorgente restituisce un dict `{url, title, description, date, source[, category]}`, oppure `None` per far passare al tentativo successivo. Un'immagine con titolo e data già presenti in un `.txt` della cache o di `prossimo/` (`recent_images`) conta come tentativo fallito.
5. `fetch_image` scarica in memoria e restituisce `None` (tentativo fallito) se il file non è un'immagine o se il lato lungo è sotto `MIN_LATO_LUNGO` (1280 px). `smart_resize_wallpaper` porta l'immagine alla risoluzione fisica dello schermo (`screen_size`: su Windows tramite `GetDeviceCaps`, perché `GetSystemMetrics` darebbe quella scalata dai DPI; su Linux tramite `xrandr` o, su Wayland e senza xrandr, dai file del kernel in `/sys/class/drm`). Il `.txt` viene scritto prima del `.jpg`, che viene salvato come `.tmp` e rinominato: se il `.jpg` esiste, la coppia è completa.

APOD del giorno: deve diventare sfondo almeno una volta, quindi ha la precedenza anche sullo sfondo già pronto, che resta in `prossimo/` per il cambio successivo. La data dell'APOD più recente usata come sfondo sta in `apod_images/apod_del_giorno` (fuori dai glob `wallpaper_*`); `mark_apod_seen` la aggiorna dopo `set_wallpaper` solo se la nuova data è più recente, così le APOD d'archivio non la fanno tornare indietro. `todays_apod` non fa nessuna richiesta se la data annotata è già quella locale di oggi (la data APOD segue l'ora di New York); salta anche video e immagini già in cache o in `prossimo/`. Il prefetch non usa questa precedenza: preparata la sera prima, l'APOD sarebbe già vecchia al cambio successivo.

Prefetch: con `--prefetch` lo script prepara un'immagine in `apod_images/prossimo/` senza toccare sfondo, accento e storico, ed esce subito se ce n'è già una pronta. La sottocartella non rientra nei glob `wallpaper_*`, quindi storico e pulizia non la vedono. Quando uno sfondo preparato viene usato, `take_prefetched` lo sposta in `apod_images/` e ne aggiorna la mtime, perché lo storico è ordinato per mtime. Tutte le chiamate HTTP passano per `SESSION` (`requests.Session`), che riusa le connessioni e ha uno user agent con il nome del progetto (Wikimedia rifiuta quello predefinito di `requests` con un 403).
## Cambio automatico

`apod.pyw --ciclo` è un processo che resta acceso e ogni `CYCLE_POLL` (15 s) controlla se è ora di cambiare sfondo; per cambiarlo lancia `apod.pyw` come sottoprocesso, così il ciclo non tiene PIL in memoria e dopo un aggiornamento usa subito il codice nuovo. Su questo PC (Intel N95) un cambio costa circa 2 s, 0,35 s di CPU, 1,6 MB di download e 5 J: il limite pratico è la rete, non l'energia. Il minimo di `MIN_CYCLE_MINUTES` (15) protegge la chiave demo di Unsplash (50 richieste all'ora).

- **Attivo o no** si legge dal sistema, come l'avvio automatico: il ciclo è attivo se esiste la sua voce di avvio (`cycle_enabled` / `set_cycle` in `comune.py`, valore `APOD_wallpaper_ciclo` in `Run` o `~/.config/autostart/apod_ciclo.desktop`). Il ciclo controlla la voce a ogni giro ed esce se manca, quindi Impostazioni e `uninstall` lo fermano togliendola. I minuti stanno in `config.json` (`cambio_automatico_minuti`) e vengono riletti a ogni giro. "Salva" lancia subito il ciclo con `start_cycle`.
- **Istanza unica:** blocco esclusivo su `apod_images/ciclo.lock` (`fcntl.flock` / `msvcrt.locking`); un secondo ciclo esce subito.
- **Quando cambia:** `set_wallpaper` aggiorna la mtime di `apod_images/ultimo_cambio` (fuori dai glob `wallpaper_*`) a ogni cambio riuscito, anche a mano o con Precedente/Successivo. Il ciclo cambia quando sono passati N minuti da `max(avvio del ciclo, ultimo_cambio)`, misurati con `time.time()` a ogni giro, così dopo una sospensione cambia una volta sola. Un cambio fallito non tocca `ultimo_cambio`: il ciclo riprova dopo `CYCLE_RETRY` (5 min).
- **Inattività:** se è ora ma `user_inactive()` è vero (schermo bloccato o nessun input da `IDLE_MINUTES`, 10 min) il ciclo aspetta; cambia al primo controllo dopo il ritorno dell'utente. Se non si può sapere, l'utente conta come presente.
- **Aggiornamenti:** se cambia la mtime di `apod.pyw` o `comune.py` il ciclo rilascia il blocco, ne avvia uno nuovo ed esce.
- La finestra principale controlla `ultimo_cambio` ogni 5 s e si aggiorna se lo sfondo è cambiato da fuori.

## Windows e Linux

`comune.py` definisce `IS_WINDOWS = sys.platform == "win32"`. Le funzioni che parlano col sistema hanno un ramo `if not IS_WINDOWS:` all'inizio e, sotto, il codice Windows originale. Quando modifichi una di queste funzioni, aggiorna entrambi i rami.

| Cosa | Windows | Linux |
|---|---|---|
| `get_current_wallpaper` / `set_wallpaper` | `SystemParametersInfoW` + registro | dipende dal desktop (`_linux_desktop`), vedi sotto |
| `update_windows_accent` | registro + `WM_SETTINGCHANGE` | restituisce `False`, non fa nulla |
| `screen_size` (`apod.pyw`) | `GetDeviceCaps` | su X11 `xrandr --current` (monitor primario); su Wayland o senza xrandr la prima modalità del primo schermo collegato in `/sys/class/drm/card*-*/modes`; ripiego 1920x1080 |
| riempimento (`set_wallpaper`) | `WallpaperStyle=10`, `TileWallpaper=0` nel registro | `picture-options 'zoom'` (gsettings), `image-style 5` (XFCE), `FillMode 2` in `KDE_SCRIPT` |
| `show_popup` (`comune.py`) | `MessageBoxW` | `zenity`, con gli stessi codici di ritorno (6/7/1); se manca restituisce 7 = "No" |
| `open_path` (cartelle) | `os.startfile` | `xdg-open` |
| `autostart_enabled` / `set_autostart` | valore `APOD_wallpaper` in `HKCU\...\CurrentVersion\Run`; toglie anche i vecchi `.lnk` ad `apod.pyw` in Esecuzione automatica | `~/.config/autostart/apod.desktop` con `sleep 15` |
| `cycle_enabled` / `set_cycle` | valore `APOD_wallpaper_ciclo` nella stessa chiave `Run`, con `--ciclo` | `~/.config/autostart/apod_ciclo.desktop`, senza `sleep` |
| `user_idle_seconds` | `GetLastInputInfo` | su X11 `XScreenSaverQueryInfo` con ctypes (`libX11.so.6`, `libXss.so.1`); su Wayland solo GNOME (`org.gnome.Mutter.IdleMonitor` con `gdbus`), perché XWayland vede solo l'input delle finestre X11; altrimenti `None` |
| `screen_locked` | `False` (a schermo bloccato l'inattività cresce da sola) | `LockedHint` di `loginctl`, poi `GetActive` degli screensaver Cinnamon, GNOME e freedesktop (KDE) con `gdbus` |
| `shortcut_path` / `set_shortcuts` (`{"menu": on, "desktop": on}`) | `Cambia Sfondo.lnk` o `Change Wallpaper.lnk` secondo la lingua (il nome del file è quello che si vede); `set_shortcuts` toglie sempre i collegamenti in tutte e due le lingue (`_shortcut_paths`) e `shortcut_exists` li cerca entrambi. Creato con PowerShell + `WScript.Shell`, un solo PowerShell per tutti i `.lnk` (valori passati nelle variabili d'ambiente). Il `.lnk` vecchio si toglie prima e l'esito è `path.exists()`, non il codice di uscita. `_unlink` riprova per circa 5 s su `PermissionError` (un collegamento appena usato dal menu Start resta aperto qualche istante) | `cambia_sfondo.desktop` (nome del file fisso, `Name=` tradotto) in `~/.local/share/applications` e nella cartella di `xdg-user-dir DESKTOP` (eseguibile e `metadata::trusted`) |
| `uninstall` (cancellazione cartella) | PowerShell staccato: `Wait-Process` sul processo che chiama (che tiene la cartella come directory corrente), poi `Remove-Item` con qualche tentativo | `shutil.rmtree` |
| `pythonw_path` | `pythonw.exe` accanto a `python.exe` | `sys.executable` |
| `_run` | aggiunge `CREATE_NO_WINDOW`, altrimenti da `pythonw` ogni comando aprirebbe una console | `subprocess.run` |
| `BG_PROCESS` (opzioni di `Popen`) | `creationflags=CREATE_NO_WINDOW` | `start_new_session=True` |

Su Linux `_linux_desktop()` riconosce l'ambiente desktop da `XDG_CURRENT_DESKTOP` (o da `DESKTOP_SESSION`), e `_linux_get_wallpaper` / `_linux_set_wallpaper` scelgono il metodo:

- **Cinnamon, GNOME (anche Unity e Budgie), MATE**: `gsettings`, con schema e chiavi in `GSETTINGS_KEYS`. GNOME scrive anche `picture-uri-dark`; MATE vuole un percorso semplice invece di un URI `file://`.
- **XFCE**: `xfconf-query -c xfce4-desktop`. `set` scrive tutte le proprietà `.../last-image` esistenti (una per monitor e area di lavoro), `get` legge la prima in ordine alfabetico.
- **KDE Plasma**: `set` usa `plasma-apply-wallpaperimage` (Plasma 5.24+); se manca, manda `KDE_SCRIPT` a `org.kde.PlasmaShell.evaluateScript` con il primo tra `qdbus6`, `qdbus-qt6`, `qdbus` e `qdbus-qt5` che risulta installato. Plasma non salva subito `plasma-org.kde.plasma.desktop-appletsrc`, quindi `set` annota il percorso in `apod_images/sfondo_impostato_kde` (il file non rientra nei glob `wallpaper_*`). `get` restituisce quel percorso, a meno che `appletsrc` non sia più recente e non lo contenga più, cioè se lo sfondo è stato cambiato a mano.
- Altri ambienti: `get` restituisce `None`, `set` restituisce `False`.

KDE e XFCE sono stati provati solo con comandi finti, non su un desktop vero. Il rilevamento dell'inattività è stato provato solo su Cinnamon con X11, non su Wayland né su KDE. `set_wallpaper` usa `Path.absolute()` e non `resolve()`, così il percorso letto dal desktop resta confrontabile con `IMAGES_DIR` in `cleanup`. Sul Python di sistema di Linux `pip install` non è permesso (PEP 668), quindi `install_dependencies` fallisce in silenzio e le dipendenze vanno installate con il gestore di pacchetti della distribuzione (comandi nel ReadMe).

## Lingua

Le lingue sono `LINGUE = {"it": "Italiano", "en": "English"}` in `comune.py`. La lingua in uso si legge all'import di `comune` da `config.json` (`lingua`); se manca vale `system_language()`: italiano se il sistema è in italiano (Windows: `GetUserDefaultUILanguage`; Linux: il primo tra `LC_ALL`, `LC_MESSAGES`, `LANG`), altrimenti inglese. Gli installer usano lo stesso criterio per i loro messaggi nel terminale (`T` in `installa.ps1`, `msg` in `installa.sh`).

- I testi si scrivono in italiano dentro `tr(...)`: `tr("Salva")`, `tr("Impossibile creare {file}", file=...)`. In inglese `tr` prende la traduzione da `EN` in `testi.py`, la cui chiave è la frase italiana esatta; se manca resta l'italiano. Ogni frase nuova o cambiata va aggiunta (o aggiornata) in `EN`, con gli stessi segnaposto. Non usare f-string dentro `tr`: le variabili vanno passate come argomenti.
- `tr` va chiamata quando il testo serve, non a livello di modulo, perché la lingua può cambiare mentre la finestra è aperta.
- Non si traducono il formato del `.txt` (`Title:`, `Valutato: Si`...), i nomi dei file, le categorie (sono parole di ricerca) né le novità degli aggiornamenti (sono i messaggi di commit).
- Nelle Impostazioni e nella finestra di installazione la prima sezione è "🌐 Lingua / Language". Al cambio `set_language` vale subito e la finestra viene riempita di nuovo da `rebuild` (la funzione `fill` del chiamante), passando a `build_settings` le scelte già fatte in `values`. "Annulla" nelle Impostazioni rimette la lingua di prima; "Salva" la scrive nel config, riscrive i collegamenti con il nome nuovo e, se è cambiata, riapre la finestra principale con `restart_ui`.
- Su Windows la finestra principale ha una misura fissa (340x350): i testi inglesi dei pulsanti vanno tenuti lunghi quanto quelli italiani.

## Contratto tra i due script

`cambia_sfondo.pyw` legge il file `.txt` accanto all'immagine attiva (stesso nome, estensione diversa) e cerca queste righe:

```
Title: ...
Date: ...
Source: ...
Category/Theme: ...   (opzionale; se manca le statistiche usano Source)
Valutato: Si          (aggiunta dopo un voto, impedisce i voti doppi)
```

Il formato è definito in un solo posto: `write_info`, `read_info` e `mark_rated` in `comune.py`. Non cambiare lo schema dei nomi `wallpaper_<fonte>_<YYYYmmdd_HHMMSS>.jpg` senza aggiornare entrambi gli script: lo usano lo scorrimento (`list_history`), la pulizia e il prefetch.

Esclusione automatica delle categorie (`is_excluded` in `comune.py`, usata da `get_valid_categories` e dalla finestra delle statistiche): una categoria con più di 15 voti e più dell'80% di scarti non viene più usata.

## Fonti

- **NASA APOD.** APOD è migrato su science.nasa.gov. La vecchia `api.nasa.gov/planetary/apod` restituisce il logo NASA (titolo "NASA Science") al posto dell'immagine, quindi non va usata. La fonte attuale è l'API "APOD Basic JSON":
  - oggi: `https://science.nasa.gov/wp-json/wp/v2/apod-basic?per_page=1` (restituisce una lista)
  - una data: `https://science.nasa.gov/wp-json/wp/v2/apod-basic/YYMMDD` (data nel formato legacy)
  - documentazione: https://api.nasa.gov/assets/files/apod/APOD-APIs-and-RSS-info.pdf
  - Non serve nessuna chiave API.
  - `hdurl` contiene parametri di ridimensionamento. Per avere l'originale a piena risoluzione togli la query e sostituisci `/dynamicimage/assets/` con `/content/dam/`.
  - Per molte date vecchie (soprattutto anni '90) `hdurl` è un segnaposto generico (`.../cosmic-origins/images/misc/news-thumbnail.png`). Queste date vengono scartate controllando che l'URL contenga `/apod/`. La foto vera sarebbe in `/apod-basic/YYMMDD/html`, ma di solito è una GIF piccola e inadatta come sfondo.
  - `media_type` può valere `video` o `iframe`: in quel caso la data viene scartata.
  - `explanation` e `title` contengono HTML, passali per `_strip_tags`.
- **NASA Image Library** (`images-api.nasa.gov`): non serve una chiave. Usa una pagina casuale tra le prime 10 per variare i risultati. Molti risultati sono foto di eventi, conferenze, ritratti e satelliti in hangar: `_nasa_wallpaper_item` scarta quelli dei centri in `NASA_EXCLUDED_CENTERS` (`HQ`, `KSC`, quasi solo foto di eventi) e, per gli altri centri, quelli con titolo o parole chiave che corrispondono a `NASA_EXCLUDED_WORDS` (trattini e underscore diventano spazi, perché alcuni titoli sono nomi di file) e quelli con un titolo come "NASA astronaut *Nome*..." (`NASA_PERSON_TITLE`, che tiene le passeggiate spaziali). I fotografi ufficiali della sede seguono gli eventi anche negli altri centri (es. "2017 Astronaut Class", JSC), quindi il centro da solo non basta. La categoria "astronaut" è stata tolta da `DEFAULT_CONFIG`: restituiva quasi solo ritratti e classi di candidati, che il filtro scarta tutti. La descrizione non si guarda, perché parole come "pressure" o "visible" darebbero falsi positivi; per lo stesso motivo le parole hanno `\b` da tutti e due i lati ("gala" senza confine finale scartava "galaxy"). Su un campione di circa 1500 risultati delle categorie predefinite ne resta circa due terzi, e restano le foto della Terra scattate dalla ISS (centro `JSC`).
- **ESA/Hubble e ESA/Webb** (`get_esa_image`): non serve una chiave. Usa la foto della settimana di Hubble (`potwYYWWa`, settimana ISO, dal 2010 al 2025), la foto del mese di Hubble dal 2026 (`potmYYMMa`) e quella di Webb da luglio 2022 (`potmYYMMa`, su `esawebb.org`). Sceglie una data a caso e costruisce l'identificativo; settimane o mesi senza foto restituiscono 404 e contano come tentativo fallito. I metadati vengono da `https://<sito>/images/<id>/api/json/`, che restituisce i testi come repr di bytes Python (`"b'...'"`, con l'UTF-8 in `\x..`): `_esa_text` li decodifica con `ast.literal_eval`. L'immagine è la risorsa `Large` (JPEG a piena risoluzione); quelle sopra i 40 MB vengono saltate. Il feed RSS di tutte le immagini non va usato: contiene anche grafici e foto di workshop e ignora la paginazione.
- **Wikimedia Commons** (`get_wikimedia_image`): non serve una chiave, ma serve uno user agent descrittivo. Prende la foto del giorno di una data a caso dal 2005 con una sola chiamata a `commons.wikimedia.org/w/api.php` (`generator=images` su `Template:Potd/YYYY-MM-DD`, con `imageinfo` ed `extmetadata` nella lingua dell'interfaccia). `iiurlwidth` chiede una miniatura larga quanto lo schermo, che Commons arrotonda a una misura standard. Scarta video e immagini con proporzioni fuori da `1 < larghezza/altezza <= 2,5`, perché molte foto del giorno sono verticali o panoramiche. Il feed `api/rest_v1/feed/featured` di Wikipedia non va usato: per le date vecchie restituisce 404.
- **Bing** (`get_bing_image`): non serve una chiave. `HPImageArchive.aspx` (non ufficiale, ma stabile da anni) arriva indietro solo di circa due settimane (`idx` da 0 a 7, `n` al massimo 8). Il mercato (`it-IT` o `en-US`) segue la lingua, così titolo e descrizione sono già tradotti. Le immagini con `wp: false` non sono offerte come sfondo e vengono scartate; le altre si scaricano in 4K con `<urlbase>_UHD.jpg`.
- **Unsplash**: fonte opzionale, richiede una chiave (`UNSPLASH_API_KEY`). Se la chiave è vuota o è ancora il segnaposto `UNSPLASH_KEY_PLACEHOLDER`, `get_unsplash_image` restituisce subito `None` e restano le altre fonti. Il vecchio fallback senza chiave (`source.unsplash.com`) è stato chiuso e non va reintrodotto.
- **Pixabay**: fonte opzionale, richiede una chiave gratuita (`PIXABAY_API_KEY`, letta da `pixabay_key()`; vuota = fonte saltata). Usa gli stessi temi di Unsplash (`unsplash_categories`, il nome della chiave è rimasto per compatibilità), quindi i voti di una categoria valgono per tutte e due. Cerca prima tra le foto scelte dalla redazione (`editors_choice`) e, se non ce ne sono, tra tutte; scarta quelle con `isAiGenerated` o `isLowQuality`. Con la chiave normale l'API dà solo `largeImageURL`, larga al massimo 1280 px: `imageURL` e `fullHDURL` arrivano solo se Pixabay approva l'accesso completo all'API, e in quel caso vengono usati da soli. Non costruire URL più grandi a mano: sarebbe aggirare quella limitazione. L'API non dà la data di pubblicazione, che si ricava dal percorso di `previewURL` (`/photo/AAAA/MM/GG/`). Pexels non è tra le fonti perché ha sospeso il rilascio di nuove chiavi.

Il progetto deve funzionare anche senza nessuna chiave. Al primo avvio `load_config()` crea `config.json` senza chiedere niente: le chiavi Unsplash e Pixabay si inseriscono dalla finestra Impostazioni (`unsplash_key()` tratta il segnaposto come chiave assente). Eventuali `NASA_API_KEY` nei vecchi `config.json` vengono ignorate.

## Installazione e aggiornamenti

- **Installer.** `installa.ps1` (Windows) cerca Python (launcher `py -3`, poi `python` escluso lo stub di `WindowsApps`, poi `%LOCALAPPDATA%\Programs\Python\Python3*` ordinati per versione) e preferisce il primo che ha Tk; se non ne trova nessuno lo installa con `winget`. Se non ci riesce, o se il Python trovato non ha Tk, apre `https://www.python.org/downloads/` con `Start-Process` e stampa i passi da seguire, compresa la riga da rilanciare. I comandi nativi che possono scrivere su stderr girano con `$ErrorActionPreference = 'Continue'`: con `Stop` PowerShell 5 interromperebbe lo script. Poi fa `pip install --user requests pillow`. `installa.sh` (Linux) installa le dipendenze con apt, dnf, pacman o zypper solo se `import requests, PIL, tkinter` fallisce. Entrambi leggono lo sha di `APOD_RAMO` (predefinito `master`) dall'API di GitHub, scaricano l'archivio di quel commit e copiano i file della radice in `INSTALL_DIR` (`%LOCALAPPDATA%\APOD_wallpaper`, `~/.local/share/apod_wallpaper`). Se il download fallisce mostrano un messaggio nella lingua del sistema. Scrivono `versione.json` senza BOM e lanciano `cambia_sfondo.pyw --installa`, con `--precedente=<commit>` se c'era già una versione installata. Con `irm | iex`, `exit` chiuderebbe la finestra di PowerShell: lo script sta in un blocco `& { }` ed esce con `return`.
- **`--installa`.** Se `config.json` non esisteva è la prima installazione: tutte le caselle sono selezionate, il pulsante è "Installa" e alla fine `restart_ui` apre la finestra principale con `--primo-sfondo`, che lancia subito `run_apod`. La finestra principale parte come processo separato, così il terminale dell'installer si libera. Altrimenti le caselle mostrano lo stato attuale, il testo dice "aggiornamento completato" o "già all'ultima versione" (confronto con `--precedente`) e alla fine la finestra principale non si apre, perché potrebbe essere già aperta. `build_settings` legge il config con `read_config()`, che non crea il file: se la prima installazione viene annullata, al rilancio è ancora la prima. Il file lo crea "Installa". Alla prima installazione `find_old_install` (in `comune.py`) cerca una versione installata a mano con il vecchio ReadMe, di solito un clone: legge i percorsi di `apod.pyw` / `cambia_sfondo.pyw` dal valore `Run` e dai `.lnk` di Esecuzione automatica, desktop e menu Start (Windows: destinazione e argomenti dei `.lnk` letti con un solo PowerShell + `WScript.Shell`, perché nei byte il percorso locale può mancare, ad esempio se `C:\Users` è condivisa in rete), oppure dai `.desktop` di `~/.config/autostart` e dai collegamenti (Linux), e prende la prima cartella diversa da `BASE_DIR` con `config.json` o `statistiche.json`. `import_old_install` copia subito `statistiche.json` se qui manca, mentre il config vecchio passa a `build_settings` come `old_config` e viene scritto solo da "Installa".
- **Impostazioni.** `build_settings` riempie sia la finestra di installazione sia il `Toplevel` aperto da "⚙️ Impostazioni". Lo stato di avvio automatico e collegamenti si legge dal sistema, non dal config. "Salva" riscrive sempre tutto, così i collegamenti puntano alla cartella attuale. Il lavoro gira con `run_in_background` (su Windows PowerShell impiega qualche secondo): intanto compare "⏳ Salvataggio in corso..." e i pulsanti sono disabilitati. La finestra di installazione è `-topmost` come quella principale, altrimenti resterebbe sotto di lei. "Disinstalla" offre di cancellare la cartella solo se `is_install_dir()`; il messaggio finale su Windows usa `show_popup` (`MessageBoxW` resta in primo piano anche se Explorer, aggiornando il desktop, passa davanti).
- **Aggiornamenti.** `local_version()` legge `versione.json`; nei clone usa `git rev-parse`. `check_update()` prende la punta del ramo da `GET /repos/.../commits/<ramo>` e l'elenco delle novità da `compare/<sha>...<punta>` (che elenca al massimo 250 commit, quindi non va usato per la punta): restituisce `None` se la versione è aggiornata o più avanti del ramo, `{commit, data, novita, totale}` se ce n'è una nuova, e solleva un'eccezione in caso di errore. `apply_update()` nei clone fa `git pull --ff-only`; altrimenti scarica lo zip del commit, sostituisce i file della radice (config, statistiche e immagini non sono nella repo) e riscrive `versione.json`. Restituisce `None` oppure un messaggio d'errore. In `cambia_sfondo.pyw` la rete gira in un thread tramite `run_in_background`, che riporta il risultato sul thread di Tk. All'apertura, se c'è una versione nuova compare la banda "Aggiorna"; dopo l'aggiornamento la finestra si riapre.
- Quello che un aggiornamento deve portare va nella radice della repo: le sottocartelle non vengono copiate.

## Convenzioni

- Commenti e messaggi di commit sono in italiano. I testi dell'interfaccia si scrivono in italiano dentro `tr(...)` e hanno la traduzione inglese in `testi.py` (vedi "Lingua"). I commit seguono Conventional Commits (`feat:`, `fix:`, `perf:`, `refactor:`, `docs:`), con una sola riga descrittiva in italiano.
- I `.pyw` girano senza console, quindi gli errori vengono ignorati di proposito (`except: return None` / `pass`) e ogni fonte fallisce in silenzio. Mantieni questo comportamento: un'eccezione non gestita non sarebbe visibile a nessuno. I popup (`show_popup`) servono solo per problemi di configurazione.
- Dipendenze esterne: solo `requests` e `pillow`. Tutto il resto deve venire dalla libreria standard.

## Test e verifica

Non ci sono test automatici. Per verificare una fonte senza cambiare lo sfondo, importa il modulo senza chiamare `main()`:

```python
import importlib.machinery, importlib.util
loader = importlib.machinery.SourceFileLoader("apod", "apod.pyw")
spec = importlib.util.spec_from_loader("apod", loader)
m = importlib.util.module_from_spec(spec); loader.exec_module(m)
print(m.get_apod_data())              # oggi
print(m.get_apod_data("2010-03-15"))  # data specifica
img = m.fetch_image(m.get_apod_data()["url"], m.screen_size())
print(m.smart_resize_wallpaper(img, m.screen_size()).size)
```

Per controllare le traduzioni, confronta le stringhe passate a `tr(` nei tre file Python (con `ast`) con le chiavi di `EN`: non devono mancarne e non devono avanzarne. Per provare l'altra lingua senza toccare il config vero, usa una copia con `"lingua"` nel suo `config.json`, oppure `LANG=en_US.UTF-8` se il config non ha la chiave.

Su Linux lancia gli script con `python3`. Per provare avvio automatico, collegamenti e installazione senza toccare il sistema, usa una copia degli script in una cartella temporanea e `HOME=$(mktemp -d)` (su X11 tieni `XAUTHORITY` puntato al file vero). La finestra si può controllare con `PIL.ImageGrab`. Per provare un ramo con l'installer: `APOD_RAMO=<ramo>` (`$env:APOD_RAMO` su Windows), dopo averlo pubblicato. Per provare l'aggiornamento, metti in `versione.json` lo sha di un commit vecchio.

Il prefetch non cambia lo sfondo: per provarlo, copia `comune.py`, `apod.pyw` e `config.json` in una cartella temporanea e lancia lì `python apod.pyw --prefetch`.

Attenzione: l'import di `apod.pyw` esegue `load_config()`, che crea `config.json` accanto agli script se manca (in silenzio). Per provare il primo avvio lavora su una copia in una cartella temporanea.

Lanciare `apod.pyw` o usare la finestra modifica lo sfondo e il colore d'accento reali dell'utente, e il voto scrive su `statistiche.json`. "Salva" nelle Impostazioni, senza `HOME` temporaneo, crea avvio automatico e collegamenti veri. Chiedi prima di farlo.
