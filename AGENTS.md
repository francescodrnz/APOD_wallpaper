# AGENTS.md

Note per agenti di coding che lavorano su questo repository. Per l'uso lato utente vedi `ReadMe.md`.

## Cos'è

Cambia-sfondo per Windows 10/11 in Python. Scarica un'immagine da una fonte casuale (NASA APOD, NASA Image Library, Unsplash), la adatta allo schermo con un "ambient blur", la imposta come sfondo e sincronizza il colore d'accento di Windows. Solo Windows: usa `ctypes.windll`, `winreg` e `SystemParametersInfoW`.

## File

| File | Ruolo |
|---|---|
| `apod.pyw` | Script headless: sceglie una fonte, scarica, ridimensiona, imposta lo sfondo, scrive i metadati, pulisce la cache. Pensato per l'avvio automatico al login. |
| `cambia_sfondo.pyw` | Finestra Tkinter: mostra info sullo sfondo attuale, like/dislike, scorrimento avanti/indietro tra gli sfondi in cache, gestione categorie e statistiche. Per cambiare sfondo lancia `apod.pyw` come sottoprocesso. |
| `config.json` | Chiavi API e liste di categorie. **Ignorato da git, contiene segreti: non committarlo e non riportarne il contenuto.** Viene generato al primo avvio di `apod.pyw`. |
| `statistiche.json` | Voti per categoria (`positivi` / `scarti`). Ignorato da git. |
| `apod_images/` | Cache locale di immagini e metadati. Ignorata da git. |

## Flusso di `apod.pyw`

1. `install_dependencies()` installa in silenzio `requests` e `pillow` se mancano.
2. `load_config()` crea o migra `config.json`.
3. `main()` mescola le fonti `[get_apod_data, get_unsplash_image, get_nasa_image_library]` e prova ognuna fino a `MAX_RETRIES` volte. Per APOD il primo tentativo è l'immagine di oggi, i successivi sono date casuali dal 1995.
4. Ogni funzione sorgente restituisce un dict `{url, title, description, date, source[, category]}`, oppure `None` per far passare al tentativo successivo.
5. Poi `download_image`, `smart_resize_wallpaper`, `set_wallpaper`, `update_windows_accent`, la scrittura del `.txt` e `cleanup` (tiene i 12 file `wallpaper_*` più recenti, cioè circa 6 coppie immagine/testo, oltre allo sfondo corrente).

## Contratto tra i due script

`cambia_sfondo.pyw` legge il file `.txt` accanto all'immagine attiva (stesso nome, estensione diversa) e cerca queste righe:

```
Title: ...
Date: ...
Source: ...
Category/Theme: ...   (opzionale; se manca le statistiche usano Source)
Valutato: Si          (aggiunta dopo un voto, impedisce i voti doppi)
```

Se cambi il formato di questi file, aggiorna entrambi gli script. Lo stesso vale per lo schema dei nomi `wallpaper_<fonte>_<YYYYmmdd_HHMMSS>.jpg`, su cui si basano lo scorrimento e la pulizia.

Esclusione automatica delle categorie (`get_valid_categories`): una categoria con più di 15 voti e più dell'80% di scarti non viene più usata.

## Fonti

- **NASA APOD.** APOD è migrato su science.nasa.gov. La vecchia `api.nasa.gov/planetary/apod` restituisce il logo NASA (titolo "NASA Science") al posto dell'immagine, quindi non va usata. La fonte attuale è l'API "APOD Basic JSON":
  - oggi: `https://science.nasa.gov/wp-json/wp/v2/apod-basic?per_page=1` (restituisce una lista)
  - una data: `https://science.nasa.gov/wp-json/wp/v2/apod-basic/YYMMDD` (data nel formato legacy)
  - documentazione: https://api.nasa.gov/assets/files/apod/APOD-APIs-and-RSS-info.pdf
  - Non serve una chiave API.
  - `hdurl` contiene parametri di ridimensionamento. Per avere l'originale a piena risoluzione togli la query e sostituisci `/dynamicimage/assets/` con `/content/dam/`.
  - Per molte date vecchie (soprattutto anni '90) `hdurl` è un segnaposto generico (`.../cosmic-origins/images/misc/news-thumbnail.png`). Queste date vengono scartate controllando che l'URL contenga `/apod/`. La foto vera sarebbe in `/apod-basic/YYMMDD/html`, ma di solito è una GIF piccola e inadatta come sfondo.
  - `media_type` può valere `video` o `iframe`: in quel caso la data viene scartata.
  - `explanation` e `title` contengono HTML, passali per `_strip_tags`.
- **NASA Image Library** (`images-api.nasa.gov`): non serve una chiave. Usa una pagina casuale tra le prime 10 per variare i risultati.
- **Unsplash**: richiede `UNSPLASH_API_KEY`. Il fallback senza chiave (`source.unsplash.com`) è un servizio dismesso.

`NASA_API_KEY` in `config.json` al momento non è usata da nessuna fonte.

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
```

Attenzione: l'import esegue `load_config()`. Se `config.json` non esiste, lo crea, mostra un popup ed esce.

Lanciare `apod.pyw` o usare la finestra modifica lo sfondo e il colore d'accento reali dell'utente, e il voto scrive su `statistiche.json`. Chiedi prima di farlo.
