# Verifica su Windows del ramo `cambio-automatico`

Istruzioni per la sessione Claude Code su Windows. Il ramo aggiunge il cambio automatico dello sfondo ogni N minuti, in pausa mentre il PC è bloccato o inattivo. Il commit della funzione è `ebb975d`. La cartella `docs/` non finisce nelle installazioni (gli installer copiano solo i file della radice) e verrà tolta prima del merge.

**Questo è l'unico giro.** L'utente non vuole passaggi avanti e indietro tra Linux e Windows: correggi tu quello che trovi (vedi "Alla fine").

## Cosa è cambiato

Leggi la sezione "Cambio automatico" di `AGENTS.md` e le righe nuove della tabella "Windows e Linux". In breve:

- `apod.pyw --ciclo` resta acceso. Ogni `CYCLE_POLL` (15 s) esce se manca la sua voce di avvio, si riavvia se `apod.pyw` o `comune.py` sono cambiati, e se sono passati N minuti da `max(avvio, mtime di apod_images/ultimo_cambio)` e l'utente non è inattivo lancia `pythonw apod.pyw` con `subprocess.run(..., **BG_PROCESS)`. Un cambio fallito si riprova dopo `CYCLE_RETRY` (300 s).
- Istanza unica con `_lock_cycle`: su Windows `msvcrt.locking(fd, LK_NBLCK, 1)` su `apod_images/ciclo.lock` aperto in `"a+"` dopo `seek(0)`. **Non provato su Windows.**
- `comune.py`:
  - `autostart_enabled` / `set_autostart` ora passano per `_run_entry_exists` / `_set_run_entry`. Il valore `APOD_wallpaper` nel registro deve restare identico a prima (`"<pythonw>" "<apod.pyw>"`), e i vecchi `.lnk` in Esecuzione automatica vanno ancora tolti.
  - `cycle_enabled` / `set_cycle`: valore `APOD_wallpaper_ciclo` nella stessa chiave `Run`, `"<pythonw>" "<apod.pyw>" --ciclo`. `start_cycle()` lo lancia subito con `pythonw_path()`.
  - `set_wallpaper` è diventato un involucro di `_set_wallpaper` che, se il cambio riesce, fa `touch` di `LAST_CHANGE_FILE`.
  - `user_idle_seconds()` su Windows: `GetLastInputInfo` e `(GetTickCount() - dwTime) & 0xFFFFFFFF`. `GetTickCount` non ha `restype`, quindi può tornare negativo: la maschera dovrebbe bastare. `screen_locked()` su Windows restituisce sempre `False`: si conta sul fatto che a schermo bloccato non arriva input. **Da verificare.** `IDLE_MINUTES = 10`.
  - `uninstall()` chiama anche `set_cycle(False)`. Il ciclo esce entro 15 s; nel frattempo tiene aperto `ciclo.lock`, e il PowerShell staccato riprova `Remove-Item` per 30 s.
- `cambia_sfondo.pyw`: nella sezione "Avvio" c'è la riga "Cambia sfondo da solo ogni [ ] minuti" con una nota grigia sotto. "Salva" rifiuta valori non interi o sotto 15, se la casella è selezionata. La finestra principale controlla `ultimo_cambio` ogni 5 s (`watch_changes`) e si aggiorna se lo sfondo è cambiato da fuori.

## Già provato su Linux (Cinnamon, X11)

In una copia temporanea con `HOME` finta e `set_wallpaper` sostituito da un log:
- un secondo `--ciclo` esce subito;
- i cambi arrivano alla scadenza giusta (intervalli ridotti);
- con `IDLE_MINUTES = 0` non arriva nessun cambio;
- modificando `comune.py` il ciclo riparte con un nuovo PID;
- togliendo il `.desktop` il ciclo esce;
- Impostazioni: "10" e "abc" mostrano l'avviso e non salvano; "25" salva e avvia il ciclo; togliendo la casella il ciclo esce;
- il `.desktop` dell'avvio all'accesso è identico a prima;
- traduzioni complete.

Non provata nemmeno su Linux: l'aggiornamento della finestra principale aperta (`watch_changes`).

## Preparazione

- `git fetch && git checkout cambio-automatico && git pull`. Serve il commit che contiene questo file.
- L'utente non vuole accorgimenti: puoi cambiare sfondo, impostazioni, avvio automatico e installazione quanto serve per i test, senza backup e senza chiedere conferma.
- Per avere cambi rapidi, lavora su una copia degli script in una cartella temporanea (con `config.json`) e abbassa lì le costanti: `CYCLE_POLL = 2`, `CYCLE_RETRY = 5` in `apod.pyw`, `minutes * 60` → `minutes * 1` (i "minuti" diventano secondi), `IDLE_MINUTES` in `comune.py` secondo il test. Non toccare queste costanti nel ramo.

## Cosa verificare

1. **Controlli statici.** `ast.parse` dei quattro file Python, e confronto con `ast` tra le stringhe passate a `tr(` e le chiavi di `EN`: non ne devono mancare né avanzare.

2. **Inattività.** `python -c "import comune, time; [print(comune.user_idle_seconds(), comune.user_inactive()) or time.sleep(5) for _ in range(12)]"`:
   - senza toccare niente, il valore deve crescere di circa 5 s a ogni riga, e muovendo il mouse deve tornare vicino a 0;
   - blocca lo schermo (Win+L) per un minuto durante il ciclo: il valore deve continuare a crescere. Se a schermo bloccato si azzera o resta fermo, implementa `screen_locked()` su Windows (ad esempio con `OpenInputDesktop`/`SwitchDesktop`, o `WTSQuerySessionInformation` con `WTSSessionInfoEx`).

3. **Ciclo nella copia temporanea** (costanti abbassate, `"cambio_automatico_minuti": 20` nel config della copia):
   - Registra la voce con `python -c "import comune; print(comune.set_cycle(True))"` dalla copia. Il valore `APOD_wallpaper_ciclo` deve puntare alla copia.
   - `pythonw apod.pyw --ciclo` e, subito dopo, un secondo `pythonw apod.pyw --ciclo`: il secondo deve uscire subito (controlla con `Get-Process pythonw` o `Get-CimInstance Win32_Process` e la riga di comando). Nessuna finestra di console deve comparire, né ora né a ogni cambio.
   - Lo sfondo vero deve cambiare circa ogni 20 s, con il colore d'accento.
   - Con `IDLE_MINUTES` abbassato a un valore piccolo e senza toccare il PC, non deve cambiare; muovendo il mouse, deve cambiare entro un controllo.
   - Modifica `comune.py` della copia (basta salvarlo): il ciclo deve ripartire con un nuovo PID e restare uno solo.
   - `set_cycle(False)`: il ciclo deve uscire entro un controllo.
   - Alla fine togli la voce e chiudi il ciclo della copia.

4. **Impostazioni sull'installazione vera** (`$env:APOD_RAMO = 'cambio-automatico'` e l'installer preso dal ramo, oppure aggiornamento dalla banda dopo aver messo `"ramo": "cambio-automatico"` in `versione.json`):
   - Nella finestra di installazione e nelle Impostazioni, la riga "Cambia sfondo da solo ogni [60] minuti" e la nota sotto non devono essere tagliate, sia in italiano sia in inglese.
   - "10" con la casella selezionata → avviso, niente salvato. "15" → salvato. In `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` devono esserci `APOD_wallpaper` (se l'avvio all'accesso è selezionato) e `APOD_wallpaper_ciclo`, e un solo processo `--ciclo`. Riaprendo le Impostazioni, la casella è selezionata e il valore è 15.
   - Con la finestra principale aperta, cambia sfondo con `pythonw apod.pyw` lanciato da fuori: entro 5 s il titolo nella finestra deve aggiornarsi.
   - Esci e rientra in Windows: il ciclo deve ripartire all'accesso, insieme al cambio all'accesso se è attivo.
   - Togli la casella e salva: il valore `APOD_wallpaper_ciclo` sparisce e il processo esce entro 15 s.

5. **Disinstalla** con il ciclo attivo, scegliendo di cancellare anche la cartella: devono sparire entrambi i valori `Run`, il processo `--ciclo` deve uscire e la cartella deve sparire entro circa 30 s, nonostante `ciclo.lock`. Poi reinstalla dal ramo.

6. **Fine.** Lascia il programma installato e funzionante, con il cambio automatico come preferisce l'utente. In `versione.json` metti `"ramo": "master"`, altrimenti dopo il merge l'installazione cercherebbe gli aggiornamenti su un ramo che non c'è più.

## Alla fine: unico giro

- **Correggi tu ogni problema**, anche piccolo e anche di UX: non scrivere proposte né decisioni da prendere. Se c'è da scegliere, scegli la soluzione più semplice e scrivi il motivo nel messaggio di commit.
- Testi nuovi o cambiati: in italiano dentro `tr(...)`, con la traduzione in `EN` in `testi.py`. Ripeti il controllo del punto 1.
- Se tocchi codice condiviso, metti le modifiche nel ramo Windows (`if IS_WINDOWS` / sotto `if not IS_WINDOWS:`) quando puoi. Se devi cambiare codice comune ai due sistemi, fai la modifica più piccola possibile e controlla con `ast.parse` che i file restino validi.
- Aggiorna `AGENTS.md` se cambia qualcosa di quello che descrive. Se cambi qualcosa che l'utente vede, aggiorna sia `ReadMe.md` sia `LeggiMi.md`.
- Commit in italiano, Conventional Commits, una riga.
- Scrivi i risultati in `docs/verifica-windows.md`: ambiente, tabella passo/esito/dettagli, correzioni fatte con il loro commit.
- In `docs/da-windows.md` scrivi **una volta sola**, in una sezione datata con il commit di partenza: cosa hai cambiato nel codice condiviso e cosa va ricontrollato su Linux. Niente proposte, domande o decisioni. La sessione Linux sistema quello che resta, toglie `docs/` e fa il merge su `master` senza rimandare niente a Windows.
- Fai commit e push sul ramo `cambio-automatico`.
- All'utente di' una riga sola: il ramo è pronto per il merge, oppure c'è qualcosa in `docs/da-windows.md` per la sessione Linux.
