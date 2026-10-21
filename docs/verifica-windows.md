# Verifica su Windows del ramo `cambio-automatico`

Data: 21/10/2026. Commit di partenza: `5a26592`.

## Ambiente

- Windows 11 Pro 10.0.26200, Python 3.14.3 (`C:\Python314\pythonw.exe`), requests e pillow nel sito utente.
- Test del ciclo su una copia temporanea con `CYCLE_POLL = 2`, `CYCLE_RETRY = 5`, `minutes * 1`, `MIN_CYCLE_MINUTES = 1` e `"cambio_automatico_minuti": 20`.
- Installazione vera in `%LOCALAPPDATA%\APOD_wallpaper`, dall'installer del ramo (`APOD_RAMO=cambio-automatico`), lanciato dall'utente.

## Risultati

| Passo | Esito | Dettagli |
|---|---|---|
| 1. Controlli statici | OK | `ast.parse` dei quattro file; 107 stringhe in `tr(` e 107 chiavi in `EN`, nessuna mancante né in più. Ripetuto dopo la correzione. |
| 2. Inattività | OK | `user_idle_seconds()` cresce di 5 s a ogni riga e torna a ~0 muovendo il mouse. A schermo bloccato (Win+L, circa 30 s) cresce da 3 a 28 s e si azzera solo allo sblocco. `screen_locked()` che restituisce `False` basta: non è stato toccato. |
| 3. Voce `Run` del ciclo | OK | `set_cycle(True)` dalla copia scrive `APOD_wallpaper_ciclo = "C:\Python314\pythonw.exe" "<copia>\apod.pyw" --ciclo`. |
| 3. Istanza unica | OK | Il secondo `pythonw apod.pyw --ciclo` esce subito (codice 0); il blocco con `msvcrt.locking` funziona. Nessuna console, né all'avvio né ai cambi. |
| 3. Cambi | OK | Quattro cambi a 17:03:22, 17:03:43, 17:04:03, 17:04:24 (ogni ~20 s), con sfondo nel registro e colore d'accento aggiornati. |
| 3. Pausa per inattività | OK | Con `IDLE_MINUTES = 0.25` nessun cambio con inattività fra 26 e 90 s; cambio 4 s dopo il movimento del mouse. |
| 3. Riavvio dopo modifica | OK | Salvato `comune.py` della copia: PID da 3048 a 12960, sempre un solo ciclo. |
| 3. `set_cycle(False)` | OK | Il ciclo esce entro un controllo. |
| 4. Testi tagliati | OK | Riga "Cambia sfondo da solo ogni [ ] minuti" e nota grigia intere nella finestra di installazione, in italiano e in inglese (schermate da `PIL.ImageGrab`). |
| 4. "10" / "15" | OK | "10" con la casella selezionata mostra l'avviso e non salva; "15" salva. Nel registro ci sono `APOD_wallpaper` e `APOD_wallpaper_ciclo`, un solo processo `--ciclo`, config a 15. Riaprendo le Impostazioni la casella è selezionata e il valore è 15. |
| 4. `watch_changes` | OK | Con la finestra principale aperta (dalla copia), `pythonw apod.pyw` lanciato da fuori: il titolo passa da "Comet Leonard behind JWST Launch Plume" a "Mrs. Herbert Stevens May 2008" entro 6 s. |
| 4. Avvio all'accesso | OK, simulato | Invece di uscire da Windows: ciclo chiuso e rilanciato con il comando esatto del valore `APOD_wallpaper_ciclo` (`cmd /c start`): parte e resta uno solo. Il formato del valore è lo stesso di `APOD_wallpaper`, che Windows già esegue all'accesso. |
| 4. Casella tolta | OK | `APOD_wallpaper_ciclo` sparisce e il processo esce in circa 4 s. |
| 5. Disinstalla con ciclo attivo | OK | Spariscono tutti e due i valori `Run`, nessun processo `--ciclo`, cartella cancellata (già assente al primo controllo, pochi secondi dopo la conferma). |
| 5. Reinstallazione | dall'utente | Prima installazione dal ramo. La disinstallazione con cartella cancella anche `config.json` (comportamento voluto): le chiavi Unsplash/Pixabay vanno reinserite. |

## Correzioni

- `ebbf337` feat: scrivere i minuti del cambio automatico seleziona da sola la sua casella (richiesta dell'utente durante la prova). La casella dei minuti ora usa una `StringVar` con `trace_add("write")`. La variabile va letta anche in `save` e nel cambio di lingua: se resta solo una variabile locale, alla fine di `build_settings` il garbage collector la elimina e Tk toglie la variabile insieme al trace.

## Osservazioni senza correzione

- Un `apod.pyw --prefetch` della copia è rimasto acceso per più di 5 minuti mentre `cdn.esawebb.org` rispondeva lentamente (handshake TLS oltre i 20 s). I timeout scattano davvero (`ReadTimeout` riprodotto): sono tentativi lenti, non un blocco infinito. Il processo è staccato e non ritarda il ciclo.
