# Da Windows

## 21/10/2026, partendo da `5a26592`

Codice condiviso cambiato:
- `cambia_sfondo.pyw`, `build_settings` (`ebbf337`): la casella dei minuti ora è un `tk.Entry` con `textvariable=v_cycle_min` (`StringVar`). Un trace in scrittura seleziona `v_cycle`. `save` e il cambio di lingua leggono `v_cycle_min.get()` al posto di `entry_cycle.get()`. Il codice vale per tutti e due i sistemi.

Da ricontrollare su Linux:
- Impostazioni: togli la casella "Cambia sfondo da solo ogni", scrivi nei minuti e controlla che si selezioni di nuovo da sola; cambia lingua con la finestra aperta e controlla che minuti e casella restino.

Nient'altro: il resto è passato su Windows senza modifiche (dettagli in `docs/verifica-windows.md`).
