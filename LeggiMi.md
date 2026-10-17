# Space & Nature Wallpaper Manager

*[Read in English](ReadMe.md)*

Cambia-sfondo automatico per Windows 10/11 e Linux (GNOME, KDE Plasma, XFCE, Cinnamon, MATE, Budgie). Gli stessi script riconoscono da soli il sistema. Scarica immagini ad alta risoluzione da **NASA**, **ESA (Hubble e Webb)**, **Wikimedia Commons**, **Bing** e **Unsplash**, le adatta allo schermo con un **Ambient Blur** (niente bande nere) e sincronizza il **colore d'accento di Windows** (solo Windows).

## Funzioni principali
* **Installazione con una riga:** niente git, niente configurazione a mano. L'installer installa anche Python (Windows) o le dipendenze (Linux) se mancano.
* **Ridimensionamento intelligente:** riempie lo schermo con un "Ambient Blur" in stile cinematografico, mantenendo le proporzioni originali senza ritagliare. La modalità di adattamento dello sfondo viene impostata da sola.
* **Colore d'accento:** prende il colore dominante dello sfondo e lo applica all'interfaccia di Windows (compatibile con il tema scuro). Si può disattivare nelle impostazioni.
* **Più fonti:** alterna NASA APOD, NASA Image Library (senza le foto di eventi e conferenze), le foto della settimana e del mese di ESA Hubble e Webb, la foto del giorno di Wikimedia Commons, l'immagine del giorno di Bing e Unsplash (natura/spazio).
* **Finestra delle impostazioni:** lingua, avvio automatico, collegamenti, chiave Unsplash, cartelle, aggiornamenti e disinstallazione, tutto in un posto.
* **Italiano e inglese:** la lingua segue quella del sistema e si può cambiare all'installazione o nelle impostazioni.
* **Avviso di aggiornamento:** la finestra avvisa quando su GitHub c'è una versione nuova e si aggiorna con un clic.
* **Cambio istantaneo:** dopo ogni cambio, lo sfondo successivo viene scaricato e preparato in background (`apod_images/prossimo/`), quindi il cambio seguente è quasi immediato.
* **Niente immagini sgranate:** le immagini con il lato lungo sotto i 1280 px vengono scartate.

## Installazione

**Windows**: apri PowerShell (Start → scrivi `powershell`) e incolla:
```powershell
irm https://raw.githubusercontent.com/francescodrnz/APOD_wallpaper/master/installa.ps1 | iex
```

**Linux**: apri un terminale e incolla:
```sh
curl -fsSL https://raw.githubusercontent.com/francescodrnz/APOD_wallpaper/master/installa.sh | sh
```

L'installer scarica il programma, installa quello che manca e apre la finestra di installazione. Scegli cosa vuoi (all'inizio è tutto selezionato) e premi **Installa**:
* lingua (italiano o inglese; la finestra cambia subito);
* cambio dello sfondo a ogni accesso;
* collegamento alla finestra di valutazione nel menu Start / menu delle applicazioni;
* collegamento sul desktop;
* chiave Unsplash (facoltativa).

Il primo sfondo viene scaricato subito. Tutto si può cambiare in seguito da **⚙️ Impostazioni** nella finestra di valutazione.

Il programma sta in `%LOCALAPPDATA%\APOD_wallpaper` (Windows) o `~/.local/share/apod_wallpaper` (Linux). Nelle impostazioni c'è un pulsante che apre la cartella.

**Aggiornare:** quando c'è una versione nuova la finestra di valutazione mostra una banda gialla con il pulsante **Aggiorna**. Puoi anche controllare dalle impostazioni, o semplicemente rilanciare la riga di installazione. Impostazioni, statistiche e immagini restano.

**Disinstallare:** **⚙️ Impostazioni → Disinstalla**. Toglie avvio automatico e collegamenti e, se vuoi, la cartella del programma.

**Arrivi da un vecchio clone git?** Lancia la riga di installazione: l'installer prende il posto del clone. Se il clone partiva all'accesso o da un collegamento, come dicevano le vecchie istruzioni, l'installer lo trova e porta qui chiave Unsplash, categorie e statistiche (la finestra di installazione dice da dove le ha prese). Altrimenti, dopo l'installazione, copia `config.json` e `statistiche.json` dal clone nella nuova cartella. Il vecchio avvio automatico e il vecchio collegamento `Cambia sfondo` vengono sostituiti, così lo sfondo non cambia due volte all'accesso. Poi puoi cancellare il clone.

## Chiavi API
* **NASA (APOD e Image Library), ESA Hubble e Webb, Wikimedia Commons, Bing:** non serve nessuna chiave.
* **Unsplash (facoltativa):** senza chiave lo script usa tutte le altre fonti. Per avere anche le immagini di Unsplash, prendi una chiave gratuita su [unsplash.com/developers](https://unsplash.com/developers) (Register -> Create a new App -> copia la Access Key) e incollala in **⚙️ Impostazioni**.

## Finestra e statistiche (`cambia_sfondo.pyw`)
Apri **Cambia Sfondo** (**Change Wallpaper** in inglese) dal menu Start, dal menu delle applicazioni o dal collegamento sul desktop.
1. Guarda **titolo, fonte e categoria** dell'immagine attuale.
2. Leggi la descrizione dell'immagine con il pulsante **Apri info**.
3. **Valuta** lo sfondo (Mi piace / Non mi piace) per registrare le tue preferenze (lo script impedisce i voti doppi).
4. Scorri gli sfondi precedenti con **Precedente / Successivo**.
5. Gestisci le categorie e guarda i voti con **Statistiche**.
6. Cambia la configurazione, lingua compresa, con **Impostazioni**.

## Problemi comuni
* **Il colore di Windows è blu / quello predefinito:** lo script scrive l'intera palette d'accento e disattiva l'opzione "Automatico" di Windows, che sulle immagini molto scure torna al blu. Se l'immagine è quasi nera (ad esempio lo spazio profondo), lo script usa un grigio scuro. Alcune applicazioni prendono il nuovo colore solo dopo un riavvio o una disconnessione.
* **Bande nere / immagine ritagliata:** a ogni cambio lo script imposta la modalità **Riempi** (Windows), **Zoom** (GNOME, Cinnamon, MATE, XFCE) o **Ridimensionata e ritagliata** (KDE). Se l'hai cambiata a mano, lo sfondo successivo la rimette.
* **L'installer dice che manca Python (Windows):** quando non riesce a installarlo da solo (manca `winget`), apre la [pagina di download di python.org](https://www.python.org/downloads/) e scrive i passi: scarica, **Install Now**, poi rilancia la riga di installazione.

## Linux
Desktop supportati: **GNOME** (Ubuntu, Fedora, Debian, Pop!_OS...), **KDE Plasma** (Kubuntu, Fedora KDE, openSUSE...), **XFCE** (Xubuntu, Linux Mint XFCE...), **Cinnamon** (Linux Mint), **MATE** e **Budgie**. Negli altri ambienti (i3, Sway, Hyprland, LXQt...) l'immagine viene scaricata ma lo sfondo non cambia.

Il supporto a KDE Plasma e XFCE non è ancora stato provato su un sistema vero: se non funziona, apri una issue.

Differenze rispetto a Windows:
* Il colore d'accento non viene cambiato (su Linux dipende dal tema del desktop).
* Il Python di sistema non permette `pip install`, quindi l'installer prende le dipendenze dalla distribuzione (apt, dnf, pacman o zypper) e chiede la password una volta.

## Installazione manuale (git)
Se preferisci un clone:
```sh
git clone https://github.com/francescodrnz/APOD_wallpaper
cd APOD_wallpaper
python cambia_sfondo.pyw --installa     # python3 su Linux
```
Su Linux installa prima le dipendenze:
```sh
sudo apt install python3-requests python3-pil python3-tk            # Debian, Ubuntu, Mint
sudo dnf install python3-requests python3-pillow python3-tkinter    # Fedora
sudo pacman -S python-requests python-pillow tk                     # Arch, Manjaro
sudo zypper install python3-requests python3-Pillow python3-tk      # openSUSE
```
Avvio automatico e collegamenti puntano allora al clone, e **Aggiorna** esegue `git pull`.

## Licenza
Licenza MIT. Creato da **Francesco Doronzo**.
