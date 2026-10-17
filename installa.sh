#!/bin/sh
# Installa o aggiorna APOD Wallpaper per l'utente corrente, senza git.
# Uso: curl -fsSL https://raw.githubusercontent.com/francescodrnz/APOD_wallpaper/master/installa.sh | sh
# Per provare un altro ramo: APOD_RAMO=nome-ramo prima di "sh".
# Config, statistiche e immagini non fanno parte dell'archivio: un aggiornamento li lascia intatti.

# Messaggi in italiano se il sistema e' in italiano, altrimenti in inglese (stesso criterio del programma)
IT=0
case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in it*) IT=1 ;; esac
msg() { if [ "$IT" = 1 ]; then printf '%s\n' "$1"; else printf '%s\n' "$2"; fi; }

# Tutto dentro una funzione: la shell la esegue solo dopo averla scaricata per intero
main() {
    set -eu
    REPO=francescodrnz/APOD_wallpaper
    RAMO=${APOD_RAMO:-master}
    DEST=${XDG_DATA_HOME:-$HOME/.local/share}/apod_wallpaper

    # Dipendenze dal gestore di pacchetti: il Python di sistema non permette pip install (PEP 668)
    if ! python3 -c "import requests, PIL, tkinter" >/dev/null 2>&1; then
        msg "Installo le dipendenze (Python, requests, Pillow, Tk): serve la password di amministratore." \
            "Installing the dependencies (Python, requests, Pillow, Tk): the administrator password is needed."
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get install -y python3 python3-requests python3-pil python3-tk </dev/null
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y python3 python3-requests python3-pillow python3-tkinter </dev/null
        elif command -v pacman >/dev/null 2>&1; then
            sudo pacman -S --needed --noconfirm python python-requests python-pillow tk </dev/null
        elif command -v zypper >/dev/null 2>&1; then
            sudo zypper --non-interactive install python3 python3-requests python3-Pillow python3-tk </dev/null
        else
            msg "Gestore di pacchetti non riconosciuto: installa Python 3 con requests, Pillow e Tk, poi rilancia." \
                "Unknown package manager: install Python 3 with requests, Pillow and Tk, then run this again." >&2
            exit 1
        fi
    fi

    # Versione gia' installata: la finestra finale dira' se e' cambiata
    PRECEDENTE=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["commit"])' \
        "$DEST/versione.json" 2>/dev/null || true)

    msg "Scarico APOD Wallpaper (ramo $RAMO)..." "Downloading APOD Wallpaper (branch $RAMO)..."
    # Commit e data della versione, scritti in versione.json per il controllo degli aggiornamenti
    COMMIT=$(curl -fsSL "https://api.github.com/repos/$REPO/commits/$RAMO") || errore_download
    INFO=$(printf '%s' "$COMMIT" | python3 -c \
        'import json, sys; c = json.load(sys.stdin); print(c["sha"], c["commit"]["committer"]["date"][:10])')
    SHA=${INFO% *}
    DATA=${INFO#* }

    TMP=$(mktemp -d)
    trap 'rm -rf "$TMP"' EXIT
    curl -fsSL -o "$TMP/apod.tar.gz" "https://github.com/$REPO/archive/$SHA.tar.gz" || errore_download
    tar -xzf "$TMP/apod.tar.gz" -C "$TMP"
    rm "$TMP/apod.tar.gz"
    mkdir -p "$DEST"
    # Solo i file della radice della repo (l'archivio sta tutto in una cartella REPO-commit/)
    find "$TMP" -mindepth 2 -maxdepth 2 -type f ! -name .gitignore -exec cp {} "$DEST/" \;
    printf '{\n    "commit": "%s",\n    "ramo": "%s",\n    "data": "%s"\n}\n' "$SHA" "$RAMO" "$DATA" > "$DEST/versione.json"

    msg "Installato in $DEST. Si apre la finestra delle impostazioni..." "Installed in $DEST. Opening the settings window..."
    python3 "$DEST/cambia_sfondo.pyw" --installa ${PRECEDENTE:+"--precedente=$PRECEDENTE"} </dev/null
}

errore_download() {
    msg "Download non riuscito: controlla la connessione e riprova (ramo $RAMO)." \
        "Download failed: check your connection and try again (branch $RAMO)." >&2
    exit 1
}

main "$@"
