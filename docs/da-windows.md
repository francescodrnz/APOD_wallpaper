# Dalla sessione Windows

Finding per la sessione Linux. I risultati delle verifiche sono in `docs/verifica-windows.md`; qui solo quello che richiede un'azione o una risposta.

## Seconda verifica, 17/10/2026, dal commit `fabe6a2`

Tutti i punti di `docs/istruzioni-windows.md` sono OK su Windows (dettagli nella sezione "Seguito" di `docs/verifica-windows.md`).

### Modifiche a codice condiviso

- **`cambia_sfondo.pyw`, `open_settings`: chiama `center(settings_win)` prima di `make_modal`.** Su Windows il `Toplevel` delle Impostazioni si apriva in (0,0), nell'angolo in alto a sinistra dello schermo. Da provare su Linux: le Impostazioni devono aprirsi al centro, intere, e restare modali (con `make_modal`, che su Linux aspetta `wait_visibility`).

### Bug trovati e non corretti

1. **"Installa" e "Salva" non danno riscontro per 3-4 secondi.** L'utente lo trova strano: preme il pulsante, non succede niente, poi la finestra si chiude e tutto funziona. Non va corretto subito, l'utente l'ha segnalato come piccolezza di UX.
   - Riprodurre: finestra di installazione o Impostazioni → "Installa"/"Salva".
   - Causa: `save()` in `build_settings` lavora sul thread di Tk. `set_shortcut` lancia un PowerShell per ogni `.lnk` (misurato: 1,5-1,8 s ciascuno, quindi 3-4 s per menu + desktop). Il `cursor="watch"` impostato prima quasi non si nota.
   - Proposta: mostrare subito "⏳ Salvataggio in corso..." e disabilitare i pulsanti, poi fare il lavoro con `run_in_background` e chiudere nel callback. In più, su Windows, creare i due `.lnk` con una sola chiamata a PowerShell, così il tempo si dimezza.
2. **La finestra dell'installer compare sotto la finestra principale.** Se la finestra principale è aperta (ha `-topmost`, `cambia_sfondo.pyw:306`), la finestra "APOD Wallpaper" / "APOD Wallpaper aggiornato" aperta dall'installer resta coperta. L'utente deve spostare la finestra principale per premere "Salva".
   - Riprodurre: apri la finestra principale, poi rilancia l'installer.
   - Proposta: in `install()`, `root.attributes("-topmost", True)` anche per la finestra di installazione, che è più recente e quindi va sopra. Togliere poi `-topmost` non basta: la finestra tornerebbe sotto quella principale.

### Decisioni da prendere

- Bug 2: la finestra principale deve restare `-topmost`? Copre tutte le finestre che non lo sono, compresa quella dell'installer. Se resta, va messo `-topmost` anche alla finestra di installazione (proposta sopra).

## Terza verifica, 17/10/2026, dal commit `8666067`

Tutti i punti di `docs/istruzioni-windows.md` sono OK su Windows dopo due correzioni (dettagli in `docs/verifica-windows.md`). Da qui non c'è niente da decidere: resta solo da ricontrollare su Linux che le modifiche a `comune.py` non abbiano cambiato niente.

### Modifiche a codice condiviso (`comune.py`)

- **Nuova funzione `_unlink(path)`, usata in `set_shortcuts` al posto di `path.unlink(missing_ok=True)`.** Su Windows riprova per circa 5 s se riceve `PermissionError`; su Linux rilancia subito l'eccezione, come prima. Nuovo `import time` in cima al file.
- **`set_shortcuts`, ramo Windows**: il `.lnk` vecchio viene cancellato prima di PowerShell e l'esito è solo `path.exists()`, non più il codice di uscita. Il ramo Linux (`_write_desktop_file`) non è stato toccato.

### Da ricontrollare su Linux

- Con `HOME` temporaneo: `set_shortcuts({"menu": True, "desktop": True})` e poi `{"menu": False, "desktop": False}` creano e tolgono ancora i due `.desktop`, e "Disinstalla" li toglie entrambi.
