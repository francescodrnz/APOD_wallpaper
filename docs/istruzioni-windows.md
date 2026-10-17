# Terza verifica su Windows del ramo `installazione-semplice`

Istruzioni per la sessione su Windows. I giri precedenti sono in `docs/verifica-windows.md`, i tuoi finding del secondo giro in `docs/da-windows.md`.

## Risposte al secondo giro

- **`center(settings_win)` in `open_settings`**: provato su Linux, OK. Le Impostazioni si aprono al centro (568x584 su 1920x1080, in 676,276), intere e modali (`grab_status() == "local"`).
- **Bug 1, "Installa"/"Salva" senza riscontro**: corretto come proponevi.
  - `save()` in `build_settings` legge i valori dei widget, disabilita i pulsanti, mostra "⏳ Salvataggio in corso..." accanto ad "Annulla", toglie la chiusura dalla X e fa il lavoro con `run_in_background`. Il callback mostra l'eventuale avviso e chiude.
  - `set_shortcut(where, on)` è diventata `set_shortcuts({where: on})` in `comune.py`, che restituisce `{where: riuscito}`. Su Windows i `.lnk` da creare passano tutti per **un solo** PowerShell: i percorsi sono in `APOD_LNKS`, separati da `|`, e lo script fa `foreach`. Anche `uninstall` usa `set_shortcuts`.
- **Bug 2, installer sotto la finestra principale**: decisione presa. La finestra principale resta `-topmost` e anche quella di installazione (`install()`) diventa `-topmost`.

Su Linux ho provato tutto con `HOME` temporaneo e un ritardo finto di 3 s in `set_shortcuts`: messaggio e pulsanti disabilitati compaiono subito, la finestra si chiude a lavoro finito, i `.desktop` vengono creati e tolti. Il ramo Windows di `set_shortcuts` da qui non si può eseguire.

## Preparazione

- `git checkout installazione-semplice && git pull`. Serve il commit che contiene questo file.
- Stesso metodo dei giri precedenti: backup all'inizio, ripristino completo alla fine controllato con `reg export`, conferma dell'utente per le cose visibili.

## Cosa verificare

1. **`set_shortcuts` su Windows.**
   - `set_shortcuts({"menu": True, "desktop": True})` deve restituire `{"menu": True, "desktop": True}` e creare i due `.lnk` con destinazione, argomenti, cartella di lavoro e icona come prima (controlla con `WScript.Shell`).
   - Misura il tempo: deve essere circa la metà dei 3-4 s di prima.
   - Off/on per ciascuno, anche misti (`{"menu": False, "desktop": True}`): il file sparisce e ricompare.
   - Cartella Desktop inesistente (simulala in una copia, per esempio facendo restituire a `shortcut_path("desktop")` un percorso finto): `desktop` deve risultare `False`, e `menu` deve comunque essere creato.
2. **"Installa" e "Salva".**
   - Dalla finestra di installazione e dalle Impostazioni, alla pressione deve comparire subito "⏳ Salvataggio in corso...", con i pulsanti grigi. La finestra si chiude da sola a lavoro finito.
   - Controlla che la scritta non tagli i pulsanti. Nelle Impostazioni la riga ha anche "Disinstalla...".
   - **Chiedi all'utente di confermare che il riscontro si vede e che i tempi vanno bene.**
3. **Installer sopra la finestra principale.** Apri la finestra principale, poi rilancia l'installer. La finestra "APOD Wallpaper" deve comparire sopra quella principale, e un eventuale avviso di "Salva" deve restare visibile. **Chiedi conferma all'utente.**
4. **Disinstalla.** "Impostazioni → Disinstalla" deve togliere ancora entrambi i collegamenti e l'avvio automatico (ora passa da `set_shortcuts`).

## Alla fine

- Correggi quello che trovi: commit in italiano, Conventional Commits, una riga.
- In `docs/verifica-windows.md`, sezione "Seguito", aggiungi l'esito del terzo giro.
- Fai commit e push sul ramo `installazione-semplice`. Poi riporta il PC allo stato di partenza.

## Comunicazione con la sessione su Linux

Le due sessioni non si parlano direttamente: comunicano solo con file nella cartella `docs/` del ramo, che l'utente fa leggere all'altra dopo il pull. Non chiedere all'utente di copiare e incollare messaggi.

- Scrivi i finding per la sessione Linux in `docs/da-windows.md`, aggiungendo una sezione per questo giro, datata e con il commit di partenza. Ci vanno:
  - i bug trovati e non corretti, con passi per riprodurli e una proposta;
  - le decisioni da prendere;
  - le cose da provare su Linux;
  - le domande;
  - le modifiche che hai fatto a codice condiviso (`comune.py`, `cambia_sfondo.pyw`, `apod.pyw`), anche se sono già corrette, perché toccano anche Linux.
- I risultati della verifica restano in `docs/verifica-windows.md`. In `docs/da-windows.md` metti solo quello che richiede un'azione o una risposta.
- Le risposte e le nuove istruzioni da Linux arrivano in questo file (`docs/istruzioni-windows.md`): quando l'utente ti dice di fare pull, rileggilo.
- Fai sempre commit e push di questi file, altrimenti l'altra sessione non li vede.
- Alla fine di' all'utente in una riga se in `docs/da-windows.md` c'è qualcosa per la sessione Linux.
