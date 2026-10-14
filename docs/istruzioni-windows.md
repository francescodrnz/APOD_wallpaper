# Seconda verifica su Windows del ramo `installazione-semplice`

Istruzioni per la sessione su Windows. Il primo giro è in `docs/verifica-windows.md`. Nella sezione "Seguito", in fondo, c'è la tabella delle correzioni ai bug aperti, con quello che è già stato provato su Linux.

## Preparazione

- Lavora sul ramo `installazione-semplice` (`git checkout installazione-semplice && git pull`). Servono almeno i commit `a7096a4` (correzioni dei bug aperti) e `934139c` (immagini in cache saltate).
- Usa lo stesso metodo del primo giro:
  - all'inizio, backup di registro, sfondo, colore d'accento e collegamenti;
  - alla fine, ripristino completo, controllato con un nuovo `reg export`;
  - per le cose visibili chiedi conferma all'utente.
- Prova tutto su Windows PowerShell 5.1, il caso in cui si è rotto il controllo di Tk.
- Usa l'installer del ramo: `$env:APOD_RAMO = 'installazione-semplice'` prima di `irm https://raw.githubusercontent.com/francescodrnz/APOD_wallpaper/installazione-semplice/installa.ps1 | iex`.

## Cosa verificare

1. **Bug 4 e 5, `Find-Python`.**
   - Controlla che venga scelto il primo Python con Tk. Per simulare un candidato senza Tk puoi sostituire `tkinter` con un modulo inesistente in una copia dello script.
   - Se nessun candidato ha Tk, deve comparire l'avviso "Questo Python non ha Tk...", non "Python non trovato".
   - Prova la riga `Sort-Object` su cartelle finte `Python39` e `Python313`: `Python313` deve venire prima.
2. **Bug 7 e bug 2, finestra dopo l'installer.**
   - Prima installazione: tutto come nel primo giro. Finestra "Installazione APOD Wallpaper", poi la finestra principale con il primo sfondo.
   - Rilancio con la stessa versione: la finestra si chiama "APOD Wallpaper" e dice "già all'ultima versione". Con "Salva" **non** deve aprirsi una seconda finestra principale.
   - Con lo sha di un commit vecchio in `versione.json`: la finestra dice "Aggiornamento completato".
   - Con `$env:APOD_RAMO = 'ramo-che-non-esiste'`: deve comparire il messaggio giallo "Download non riuscito..." senza l'eccezione rossa di PowerShell, e la finestra deve restare aperta.
3. **Bug 3, prima installazione annullata.** Senza `config.json`, premi "Annulla" nella finestra di installazione e rilancia l'installer. Deve essere ancora "Installazione APOD Wallpaper", con tutte le caselle selezionate. (Su Linux è già stato provato anche dal vero.)
4. **Bug 1, messaggio della disinstallazione.**
   - Fai "Impostazioni → Disinstalla" e chiedi di cancellare anche la cartella.
   - Il messaggio "APOD Wallpaper è stato disinstallato." deve comparire in primo piano (ora usa `MessageBoxW`). **Chiedi all'utente di confermare che lo vede.**
   - Dopo OK la cartella deve sparire.
5. **Bug 6, `check_update()`.**
   - Con lo sha di un commit vecchio deve restituire `commit` uguale alla punta del ramo e il campo `totale`.
   - Il conteggio delle modifiche deve essere giusto nella banda "Aggiorna", nelle Impostazioni e nella finestra delle novità.
6. **Immagini già in cache (`934139c`).** Dopo un cambio di sfondo con fonte APOD, l'immagine in `apod_images\prossimo` deve essere diversa da quella appena impostata: titolo e data nel `.txt` diversi.

## Alla fine

- Correggi quello che trovi: commit in italiano, Conventional Commits, una riga.
- In `docs/verifica-windows.md` aggiorna la sezione "Seguito": aggiungi l'esito su Windows di ogni riga e una riga per il punto 6.
- Fai commit e push sul ramo `installazione-semplice`. Poi riporta il PC allo stato di partenza.

## Comunicazione con la sessione su Linux

Le due sessioni non si parlano direttamente: comunicano solo con file nella cartella `docs/` del ramo, che l'utente fa leggere all'altra dopo il pull. Non chiedere all'utente di copiare e incollare messaggi.

- Scrivi i finding per la sessione Linux in `docs/da-windows.md`, con una sezione per ogni giro di verifica, datata e con il commit di partenza. Ci vanno:
  - i bug trovati e non corretti, con passi per riprodurli e una proposta;
  - le decisioni da prendere;
  - le cose da provare su Linux;
  - le domande;
  - le modifiche che hai fatto a codice condiviso (`comune.py`, `cambia_sfondo.pyw`, `apod.pyw`), anche se sono già corrette, perché toccano anche Linux.
- I risultati della verifica restano in `docs/verifica-windows.md`. In `docs/da-windows.md` metti solo quello che richiede un'azione o una risposta.
- Le risposte e le nuove istruzioni da Linux arrivano in questo file (`docs/istruzioni-windows.md`): quando l'utente ti dice di fare pull, rileggilo.
- Fai sempre commit e push di questi file, altrimenti l'altra sessione non li vede.
- Alla fine di' all'utente in una riga se in `docs/da-windows.md` c'è qualcosa per la sessione Linux.
