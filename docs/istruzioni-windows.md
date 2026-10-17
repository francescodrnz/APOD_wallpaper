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

## Alla fine: questo è l'ultimo giro

L'utente non vuole altri passaggi tra Linux e Windows. Chiudi tu tutto quello che trovi, senza rimandare niente alla sessione Linux:

- **Correggi tu ogni problema**, anche piccolo e anche di UX: non scrivere proposte né decisioni da prendere. Se c'è da scegliere, scegli la soluzione più semplice e scrivi il motivo nel messaggio di commit.
- Se tocchi codice condiviso, metti le modifiche nel ramo Windows (`if IS_WINDOWS` / sotto il ramo `if not IS_WINDOWS:`) quando puoi. Se devi cambiare codice comune ai due sistemi, fai la modifica più piccola possibile e controlla che il ramo Linux resti com'era: `python -c "import ast; ast.parse(open('cambia_sfondo.pyw', encoding='utf-8').read())"` e lo stesso per `comune.py` e `apod.pyw`.
- Commit in italiano, Conventional Commits, una riga.
- In `docs/verifica-windows.md`, sezione "Seguito", aggiungi l'esito del terzo giro e le correzioni fatte.
- In `docs/da-windows.md` puoi scrivere **un'ultima volta**, in una sezione "Terza verifica" datata e con il commit di partenza. Scrivi solo cosa hai cambiato nel codice condiviso e cosa va ricontrollato su Linux. Niente proposte, domande o decisioni: quelle le hai già risolte tu. La sessione Linux sistema quello che resta senza rimandare niente a Windows: dopo questo non ci sono altri giri.
- Fai commit e push sul ramo `installazione-semplice`, poi riporta il PC allo stato di partenza.
- All'utente di' solo una riga: il ramo è pronto per il merge su `master`, oppure c'è qualcosa in `docs/da-windows.md` per la sessione Linux.
