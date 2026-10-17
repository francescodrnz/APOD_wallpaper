# Dalla sessione Windows

## 17/10/2026, partenza da `c17ddfd`

Esito completo in `verifica-windows.md`. Tutti i passi delle istruzioni sono riusciti; due correzioni.

### Codice condiviso cambiato

- `cambia_sfondo.pyw`, `center(win, size=None)`: con `size` dà alla finestra quella misura e non chiama `update_idletasks`; senza `size` fa come prima. Lo usano anche su Linux:
  - `action("open_txt")`: `center(info_win, (500, 400))` al posto di `info_win.geometry("500x400")`;
  - `manage_categories`: `center(manage_win, (600, 450))` al posto di `manage_win.geometry("600x450")`. Su Linux la misura viene poi allargata se serve, come prima, quindi la finestra può risultare un po' spostata dal centro.
- `make_modal`: cambiato solo il ramo Windows (`transient`).
- `comune.py`, `find_old_install`: cambiato solo il ramo Windows.

### Da ricontrollare su Linux

- Le finestre "Informazioni Sfondo" e "Gestione & Statistiche" si aprono centrate, con la misura giusta e senza testi tagliati (in particolare "Salva e Chiudi").
