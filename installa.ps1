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

    # Percorso di python.exe, oppure $null. Lo stub "python" di WindowsApps apre il Microsoft Store: si salta.
    function Find-Python {
        $candidates = @()
        $py = Get-Command py -ErrorAction SilentlyContinue
        if ($py) { $candidates += [pscustomobject]@{ Exe = $py.Source; Args = @('-3') } }
        foreach ($c in @(Get-Command python -All -ErrorAction SilentlyContinue)) {
            if ($c.Source -notlike '*\WindowsApps\*') { $candidates += [pscustomobject]@{ Exe = $c.Source; Args = @() } }
        }
        # L'installer di python.org per il solo utente non aggiunge Python al PATH
        foreach ($f in @(Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)) {
            $candidates += [pscustomobject]@{ Exe = $f.FullName; Args = @() }
        }
        foreach ($c in $candidates) {
            $exeArgs = @($c.Args)
            try {
                $out = & $c.Exe @exeArgs -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $out) { return "$out".Trim() }
            } catch { }
        }
        return $null
    }

    $python = Find-Python
    if (-not $python) {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Host 'Python non trovato: lo installo con winget (qualche minuto)...'
            winget install -e --id Python.Python.3.13 --scope user --silent --accept-package-agreements --accept-source-agreements
            $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
            $python = Find-Python
        }
        if (-not $python) {
            Write-Host 'Python non trovato. Installalo da https://www.python.org/downloads/ e rilancia questo comando.' -ForegroundColor Yellow
            return
        }
    }
    Write-Host "Python: $python"

    Write-Host "Scarico APOD Wallpaper (ramo $ramo)..."
    $commit = Invoke-RestMethod "https://api.github.com/repos/$repo/commits/$ramo"
    $sha = $commit.sha
    # PowerShell 7 converte da solo le date ISO in DateTime, PowerShell 5 no
    $data = $commit.commit.committer.date
    $data = if ($data -is [datetime]) { $data.ToString('yyyy-MM-dd') } else { "$data".Substring(0, 10) }

    $tmp = Join-Path ([IO.Path]::GetTempPath()) ('apod_' + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
        $zip = Join-Path $tmp 'apod.zip'
        Invoke-WebRequest "https://github.com/$repo/archive/$sha.zip" -OutFile $zip -UseBasicParsing
        Expand-Archive $zip -DestinationPath $tmp
        $src = Get-ChildItem $tmp -Directory | Select-Object -First 1
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        # Solo i file della radice della repo
        Get-ChildItem $src.FullName -File -Force | Where-Object Name -ne '.gitignore' | Copy-Item -Destination $dest -Force
    } finally {
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
    # Senza BOM: Set-Content -Encoding UTF8 di PowerShell 5 lo aggiungerebbe
    $versione = [ordered]@{ commit = $sha; ramo = $ramo; data = $data } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $dest 'versione.json'), $versione)

    Write-Host 'Installo le dipendenze (requests, Pillow)...'
    & $python -m pip install --user --disable-pip-version-check requests pillow
    if ($LASTEXITCODE -ne 0) { Write-Host 'pip non e'' riuscito: ci riprovera'' il programma al primo avvio.' -ForegroundColor Yellow }
    & $python -c "import tkinter" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Questo Python non ha Tk: reinstallalo da python.org lasciando selezionato "tcl/tk and IDLE".' -ForegroundColor Yellow
        return
    }

    $pythonw = Join-Path (Split-Path $python) 'pythonw.exe'
    if (-not (Test-Path $pythonw)) { $pythonw = $python }
    Write-Host "Installato in $dest. Si apre la finestra delle impostazioni..."
    Start-Process -FilePath $pythonw -ArgumentList @(('"' + (Join-Path $dest 'cambia_sfondo.pyw') + '"'), '--installa') -WorkingDirectory $dest
}
