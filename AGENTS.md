# AGENTS.md

Note per agenti di coding che lavorano su questo repository. Per l'uso lato utente vedi `ReadMe.md`.

## Cos'è

Cambia-sfondo in Python per Windows 10/11 e Linux. Scarica un'immagine da una fonte casuale (NASA APOD, NASA Image Library, Unsplash), la adatta allo schermo con un "ambient blur", la imposta come sfondo e, solo su Windows, sincronizza il colore d'accento. Gli stessi file girano su entrambi i sistemi e scelgono da soli il ramo giusto (vedi "Windows e Linux").

## File

| File | Ruolo |
|---|---|
| `apod.pyw` | Script headless: sceglie una fonte, scarica, ridimensiona, imposta lo sfondo, scrive i metadati, pulisce la cache e prepara in anticipo il prossimo sfondo. Pensato per l'avvio automatico al login. |
| `cambia_sfondo.pyw` | Finestra Tkinter: mostra info sullo sfondo attuale, like/dislike, scorrimento avanti/indietro tra gli sfondi in cache, gestione categorie e statistiche. Per cambiare sfondo lancia `apod.pyw` come sottoprocesso. |
| `comune.py` | Codice condiviso dai due script: rilevamento della piattaforma (`IS_WINDOWS`, `BG_PROCESS`), installazione delle dipendenze, percorsi, lettura/impostazione dello sfondo, colore d'accento, statistiche e regola di esclusione, lettura/scrittura del `.txt`, storico. Le funzioni usate da entrambi vanno qui, non duplicate. |
| `config.json` | Chiave Unsplash (opzionale) e liste di categorie. **Ignorato da git, contiene segreti: non committarlo e non riportarne il contenuto.** Viene generato al primo avvio di `apod.pyw`. |
| `statistiche.json` | Voti per categoria (`positivi` / `scarti`). Ignorato da git. |
| `apod_images/` | Cache locale di immagini e metadati. Ignorata da git. |

## Flusso di `apod.pyw`

1. L'import di `comune` esegue `install_dependencies()`, che installa in silenzio `requests` e `pillow` se mancano. Per questo `comune` va importato prima di loro.
2. `load_config()` crea o migra `config.json`.
3. `main()` prende lo sfondo già pronto in `apod_images/prossimo/` (`take_prefetched`). Se non c'è, lo prepara al momento con `prepare_image`. Poi avvia `apod.pyw --prefetch` come processo separato, e infine chiama `set_wallpaper`, `update_windows_accent` e `cleanup` (tiene i 12 file `wallpaper_*` più recenti, cioè circa 6 coppie immagine/testo, oltre allo sfondo corrente).
4. `prepare_image` → `find_image` mescola le fonti `[get_apod_data, get_unsplash_image, get_nasa_image_library]` e prova ognuna fino a `MAX_RETRIES` volte. Per APOD il primo tentativo è l'immagine di oggi, i successivi sono date casuali dal 1995. Ogni funzione sorgente restituisce un dict `{url, title, description, date, source[, category]}`, oppure `None` per far passare al tentativo successivo.
5. `fetch_image` scarica in memoria e restituisce `None` (tentativo fallito) se il file non è un'immagine o se il lato lungo è sotto `MIN_LATO_LUNGO` (1280 px). `smart_resize_wallpaper` porta l'immagine alla risoluzione fisica dello schermo (`screen_size`: su Windows tramite `GetDeviceCaps`, perché `GetSystemMetrics` darebbe quella scalata dai DPI; su Linux tramite `xrandr` o, su Wayland e senza xrandr, dai file del kernel in `/sys/class/drm`). Il `.txt` viene scritto prima del `.jpg`, che viene salvato come `.tmp` e rinominato: se il `.jpg` esiste, la coppia è completa.

Prefetch: con `--prefetch` lo script prepara un'immagine in `apod_images/prossimo/` senza toccare sfondo, accento e storico, ed esce subito se ce n'è già una pronta. La sottocartella non rientra nei glob `wallpaper_*`, quindi storico e pulizia non la vedono. Quando uno sfondo preparato viene usato, `take_prefetched` lo sposta in `apod_images/` e ne aggiorna la mtime, perché lo storico è ordinato per mtime. Tutte le chiamate HTTP passano per `SESSION` (`requests.Session`), che riusa le connessioni.

## Windows e Linux

`comune.py` definisce `IS_WINDOWS = sys.platform == "win32"`. Le funzioni che parlano col sistema hanno un ramo `if not IS_WINDOWS:` all'inizio e, sotto, il codice Windows originale. Quando modifichi una di queste funzioni, aggiorna entrambi i rami.

| Cosa | Windows | Linux |
|---|---|---|
| `get_current_wallpaper` / `set_wallpaper` | `SystemParametersInfoW` + registro | dipende dal desktop (`_linux_desktop`), vedi sotto |
| `update_windows_accent` | registro + `WM_SETTINGCHANGE` | restituisce `False`, non fa nulla |
| `screen_size` (`apod.pyw`) | `GetDeviceCaps` | su X11 `xrandr --current` (monitor primario); su Wayland o senza xrandr la prima modalità del primo schermo collegato in `/sys/class/drm/card*-*/modes`; ripiego 1920x1080 |
| `show_popup` (`apod.pyw`) | `MessageBoxW` | `zenity`, con gli stessi codici di ritorno (6/7/1); se manca restituisce 7 = "No" |
| apertura di `config.json` | `os.startfile` | `xdg-open` |
| `BG_PROCESS` (opzioni di `Popen`) | `creationflags=CREATE_NO_WINDOW` | `start_new_session=True` |

Su Linux `_linux_desktop()` riconosce l'ambiente desktop da `XDG_CURRENT_DESKTOP` (o da `DESKTOP_SESSION`), e `_linux_get_wallpaper` / `_linux_set_wallpaper` scelgono il metodo:

- **Cinnamon, GNOME (anche Unity e Budgie), MATE**: `gsettings`, con schema e chiavi in `GSETTINGS_KEYS`. GNOME scrive anche `picture-uri-dark`; MATE vuole un percorso semplice invece di un URI `file://`.
- **XFCE**: `xfconf-query -c xfce4-desktop`. `set` scrive tutte le proprietà `.../last-image` esistenti (una per monitor e area di lavoro), `get` legge la prima in ordine alfabetico.
- **KDE Plasma**: `set` usa `plasma-apply-wallpaperimage` (Plasma 5.24+); se manca, manda `KDE_SCRIPT` a `org.kde.PlasmaShell.evaluateScript` con il primo tra `qdbus6`, `qdbus-qt6`, `qdbus` e `qdbus-qt5` che risulta installato. Plasma non salva subito `plasma-org.kde.plasma.desktop-appletsrc`, quindi `set` annota il percorso in `apod_images/sfondo_impostato_kde` (il file non rientra nei glob `wallpaper_*`). `get` restituisce quel percorso, a meno che `appletsrc` non sia più recente e non lo contenga più, cioè se lo sfondo è stato cambiato a mano.
- Altri ambienti: `get` restituisce `None`, `set` restituisce `False`.

KDE e XFCE sono stati provati solo con comandi finti, non su un desktop vero. `set_wallpaper` usa `Path.absolute()` e non `resolve()`, così il percorso letto dal desktop resta confrontabile con `IMAGES_DIR` in `cleanup`. Sul Python di sistema di Linux `pip install` non è permesso (PEP 668), quindi `install_dependencies` fallisce in silenzio e le dipendenze vanno installate con il gestore di pacchetti della distribuzione (comandi nel ReadMe).

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
- **NASA Image Library** (`images-api.nasa.gov`): non serve una chiave. Usa una pagina casuale tra le prime 10 per variare i risultati.
- **Unsplash**: fonte opzionale, l'unica che richiede una chiave (`UNSPLASH_API_KEY`). Se la chiave è vuota o è ancora il segnaposto `UNSPLASH_KEY_PLACEHOLDER`, `get_unsplash_image` restituisce subito `None` e restano le fonti NASA. Il vecchio fallback senza chiave (`source.unsplash.com`) è stato chiuso e non va reintrodotto.

Il progetto deve funzionare anche senza nessuna chiave. Al primo avvio `load_config()` crea `config.json` e chiede se aprirlo per inserire la chiave Unsplash: con "No" prosegue, con "Sì" apre il file ed esce. Eventuali `NASA_API_KEY` nei vecchi `config.json` vengono ignorate.

## Convenzioni

- Commenti, testi dell'interfaccia e messaggi di commit sono in italiano. I commit seguono Conventional Commits (`feat:`, `fix:`, `perf:`, `refactor:`, `docs:`), con una sola riga descrittiva in italiano.
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

Su Linux lancia gli script con `python3`. Per provare `show_popup` e il primo avvio senza aprire finestre, metti in testa al `PATH` uno script `zenity` finto che esce con 0 ("Sì") o 1 ("No").

Il prefetch non cambia lo sfondo: per provarlo, copia `comune.py`, `apod.pyw` e `config.json` in una cartella temporanea e lancia lì `python apod.pyw --prefetch`.

Attenzione: l'import esegue `load_config()`. Se `config.json` non esiste, lo crea e mostra un popup bloccante. Per provare il primo avvio, lavora su una copia di `apod.pyw` in una cartella temporanea e sostituisci `ctypes.windll.user32.MessageBoxW` con una funzione finta.

Lanciare `apod.pyw` o usare la finestra modifica lo sfondo e il colore d'accento reali dell'utente, e il voto scrive su `statistiche.json`. Chiedi prima di farlo.
