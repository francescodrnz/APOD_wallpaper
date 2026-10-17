# Installa o aggiorna APOD Wallpaper per l'utente corrente, senza git e senza permessi di amministratore.
# Uso (PowerShell): irm https://raw.githubusercontent.com/francescodrnz/APOD_wallpaper/master/installa.ps1 | iex
# Per provare un altro ramo: $env:APOD_RAMO = 'nome-ramo' prima del comando.
# Config, statistiche e immagini non fanno parte dell'archivio: un aggiornamento li lascia intatti.

# Tutto dentro un blocco: con "irm | iex" un exit chiuderebbe la finestra di PowerShell, return no
& {
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'  # con la barra di avanzamento Invoke-WebRequest e' lentissimo
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $repo = 'francescodrnz/APOD_wallpaper'
    $ramo = if ($env:APOD_RAMO) { $env:APOD_RAMO } else { 'master' }
    $dest = Join-Path $env:LOCALAPPDATA 'APOD_wallpaper'
    # Messaggi in italiano se Windows e' in italiano, altrimenti in inglese (stesso criterio del programma)
    $it = (Get-UICulture).TwoLetterISOLanguageName -eq 'it'
    function T($testoIt, $testoEn) { if ($it) { $testoIt } else { $testoEn } }

    # Percorso di python.exe, oppure $null. Lo stub "python" di WindowsApps apre il Microsoft Store: si salta.
    # Preferisce un Python con Tk; se nessuno ce l'ha restituisce il primo che funziona, e l'avviso arriva dopo.
    function Find-Python {
        # Con 'Stop' PowerShell 5 trasformerebbe il traceback su stderr in un errore (vale solo dentro la funzione)
        $ErrorActionPreference = 'Continue'
        $candidates = @()
        $py = Get-Command py -ErrorAction SilentlyContinue
        if ($py) { $candidates += [pscustomobject]@{ Exe = $py.Source; Args = @('-3') } }
        foreach ($c in @(Get-Command python -All -ErrorAction SilentlyContinue)) {
            if ($c.Source -notlike '*\WindowsApps\*') { $candidates += [pscustomobject]@{ Exe = $c.Source; Args = @() } }
        }
        # L'installer di python.org per il solo utente non aggiunge Python al PATH
        # Ordinati per versione: come stringhe Python39 verrebbe prima di Python313
        $installed = @(Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue |
            Sort-Object { [int]('0' + ($_.Directory.Name -replace '^Python3(\d*).*$', '$1')) } -Descending)
        foreach ($f in $installed) {
            $candidates += [pscustomobject]@{ Exe = $f.FullName; Args = @() }
        }
        $senzaTk = $null
        foreach ($c in $candidates) {
            $exeArgs = @($c.Args)
            try {
                $out = & $c.Exe @exeArgs -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -ne 0 -or -not $out) { continue }
                & $c.Exe @exeArgs -c "import tkinter" 2>$null
                if ($LASTEXITCODE -eq 0) { return "$out".Trim() }
                if (-not $senzaTk) { $senzaTk = "$out".Trim() }
            } catch { }
        }
        return $senzaTk
    }

    $python = Find-Python
    if (-not $python) {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Host (T 'Python non trovato: lo installo con winget (qualche minuto)...' 'Python not found: installing it with winget (a few minutes)...')
            winget install -e --id Python.Python.3.13 --scope user --silent --accept-package-agreements --accept-source-agreements
            $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
            $python = Find-Python
        }
        if (-not $python) {
            # Senza winget (o se non ci riesce) Python va scaricato a mano: si apre gia' la pagina giusta
            $urlPython = 'https://www.python.org/downloads/'
            Write-Host ''
            Write-Host (T 'Python non trovato e non installabile in automatico. Installalo a mano:' 'Python not found and it could not be installed automatically. Install it by hand:') -ForegroundColor Yellow
            Write-Host (T "  1. Si apre la pagina $urlPython : premi il pulsante giallo `"Download Python`"." "  1. The page $urlPython opens: press the yellow `"Download Python`" button.") -ForegroundColor Yellow
            Write-Host (T '  2. Apri il file scaricato e premi "Install Now".' '  2. Open the downloaded file and press "Install Now".') -ForegroundColor Yellow
            Write-Host (T '  3. Finita l''installazione, rilancia in questa finestra lo stesso comando di prima:' '  3. When it is done, run the same command again in this window:') -ForegroundColor Yellow
            Write-Host "     irm https://raw.githubusercontent.com/$repo/master/installa.ps1 | iex" -ForegroundColor Yellow
            try { Start-Process $urlPython } catch { }
            return
        }
    }
    Write-Host "Python: $python"

    # Versione gia' installata: la finestra finale dira' se e' cambiata
    $precedente = ''
    $fileVersione = Join-Path $dest 'versione.json'
    if (Test-Path $fileVersione) {
        try { $precedente = "$((Get-Content $fileVersione -Raw | ConvertFrom-Json).commit)" } catch { }
    }

    Write-Host (T "Scarico APOD Wallpaper (ramo $ramo)..." "Downloading APOD Wallpaper (branch $ramo)...")
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ('apod_' + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
        $commit = Invoke-RestMethod "https://api.github.com/repos/$repo/commits/$ramo"
        $sha = $commit.sha
        # PowerShell 7 converte da solo le date ISO in DateTime, PowerShell 5 no
        $data = $commit.commit.committer.date
        $data = if ($data -is [datetime]) { $data.ToString('yyyy-MM-dd') } else { "$data".Substring(0, 10) }
        $zip = Join-Path $tmp 'apod.zip'
        Invoke-WebRequest "https://github.com/$repo/archive/$sha.zip" -OutFile $zip -UseBasicParsing
        Expand-Archive $zip -DestinationPath $tmp
        $src = Get-ChildItem $tmp -Directory | Select-Object -First 1
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        # Solo i file della radice della repo
        Get-ChildItem $src.FullName -File -Force | Where-Object Name -ne '.gitignore' | Copy-Item -Destination $dest -Force
    } catch {
        Write-Host (T "Download non riuscito: controlla la connessione e riprova (ramo $ramo)." "Download failed: check your connection and try again (branch $ramo).") -ForegroundColor Yellow
        Write-Host ((T 'Dettagli: ' 'Details: ') + $_.Exception.Message) -ForegroundColor DarkGray
        return
    } finally {
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
    # Senza BOM: Set-Content -Encoding UTF8 di PowerShell 5 lo aggiungerebbe
    $versione = [ordered]@{ commit = $sha; ramo = $ramo; data = $data } | ConvertTo-Json
    [IO.File]::WriteAllText($fileVersione, $versione)

    Write-Host (T 'Installo le dipendenze (requests, Pillow)...' 'Installing the dependencies (requests, Pillow)...')
    & $python -m pip install --user --disable-pip-version-check requests pillow
    if ($LASTEXITCODE -ne 0) { Write-Host (T 'pip non e'' riuscito: ci riprovera'' il programma al primo avvio.' 'pip failed: the program will try again when it first starts.') -ForegroundColor Yellow }
    # Con 'Stop' PowerShell 5 trasformerebbe il traceback su stderr in un errore che interrompe lo script
    $ErrorActionPreference = 'Continue'
    & $python -c "import tkinter" 2>$null
    $tk = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($tk -ne 0) {
        $urlPython = 'https://www.python.org/downloads/'
        Write-Host ''
        Write-Host (T "Questo Python non ha Tk, che serve alla finestra del programma. Si apre la pagina $urlPython :" "This Python has no Tk, which the program window needs. The page $urlPython opens:") -ForegroundColor Yellow
        Write-Host (T '  scarica Python, nell''installazione scegli "Customize installation" e lascia selezionato "tcl/tk and IDLE",' '  download Python, choose "Customize installation" in the installer and keep "tcl/tk and IDLE" selected,') -ForegroundColor Yellow
        Write-Host (T "  poi rilancia: irm https://raw.githubusercontent.com/$repo/master/installa.ps1 | iex" "  then run again: irm https://raw.githubusercontent.com/$repo/master/installa.ps1 | iex") -ForegroundColor Yellow
        try { Start-Process $urlPython } catch { }
        return
    }

    $pythonw = Join-Path (Split-Path $python) 'pythonw.exe'
    if (-not (Test-Path $pythonw)) { $pythonw = $python }
    Write-Host (T "Installato in $dest. Si apre la finestra delle impostazioni..." "Installed in $dest. Opening the settings window...")
    $uiArgs = @(('"' + (Join-Path $dest 'cambia_sfondo.pyw') + '"'), '--installa')
    if ($precedente) { $uiArgs += "--precedente=$precedente" }
    Start-Process -FilePath $pythonw -ArgumentList $uiArgs -WorkingDirectory $dest
}
