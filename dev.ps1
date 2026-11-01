<#
.SYNOPSIS
    Raccourcis de développement Kora pour Windows (PowerShell).

.DESCRIPTION
    Équivalent Windows du fichier Makefile : création de l'environnement, migrations,
    démonstration, tests, lint, serveurs et test d'un routeur MikroTik réel.

.EXAMPLE
    .\dev.ps1 install
    .\dev.ps1 migrate
    .\dev.ps1 demo
    .\dev.ps1 test
    .\dev.ps1 run
    .\dev.ps1 console

.EXAMPLE
    .\dev.ps1 probe -RouterHost 192.168.56.101 -RouterUser kora -RouterPassword "motdepasse"
    .\dev.ps1 probe -RouterHost 192.168.56.101 -RouterUser kora -RouterPassword "..." -Http -RouterPort 80

.NOTES
    Exécution autorisée : powershell -ExecutionPolicy Bypass -File .\dev.ps1 test
    ou, dans la session courante : Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#>
[CmdletBinding()]
param(
    [ValidateSet('help', 'install', 'migrate', 'demo', 'test', 'lint', 'run', 'console', 'probe', 'maquettes')]
    [string]$Task = 'help',

    [string]$RouterHost = '192.168.56.101',
    [string]$RouterUser = 'kora',
    [string]$RouterPassword = '',
    [int]$RouterPort = 443,
    [switch]$Http,
    [switch]$Interfaces
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvPython = Join-Path $Root '.venv\Scripts\python.exe'
$VenvPip = Join-Path $Root '.venv\Scripts\pip.exe'
$ManagePy = Join-Path $Root 'backend\manage.py'
$ConsoleDir = Join-Path $Root 'frontend\console'

function Write-Step([string]$Message) {
    Write-Host "`n$Message" -ForegroundColor Cyan
}

function Invoke-In([string]$Path, [scriptblock]$Action) {
    Push-Location $Path
    try { & $Action } finally { Pop-Location }
}

function Assert-Venv {
    if (-not (Test-Path $VenvPython)) {
        throw "Environnement introuvable : lancez d'abord .\dev.ps1 install"
    }
}

function Invoke-Manage([string[]]$Arguments) {
    Assert-Venv
    Invoke-In (Join-Path $Root 'backend') { & $VenvPython 'manage.py' @Arguments }
}

function Show-Help {
    $lines = @(
        'Kora — commandes Windows',
        '',
        '  .\dev.ps1 install    Crée .venv, installe le backend (editable) et la console (npm)',
        '  .\dev.ps1 migrate    Applique les migrations SQLite/Postgres',
        '  .\dev.ps1 demo       Jeu de démonstration complet (routeur simulé)',
        '  .\dev.ps1 test       Suite de tests pytest',
        '  .\dev.ps1 lint       Ruff (qualité de code Python)',
        '  .\dev.ps1 run        API sur http://localhost:8001',
        '  .\dev.ps1 console    Console React sur http://localhost:5173 (autre fenêtre)',
        '  .\dev.ps1 maquettes  Régénère les maquettes HTML (design\dist)',
        '',
        '  .\dev.ps1 probe -RouterHost 192.168.56.101 -RouterUser kora -RouterPassword "..."',
        '                       Teste un routeur RouterOS réel',
        '                       (ajoutez -Http -RouterPort 80 pour du HTTP simple)',
        '',
        'Variables : copiez .env.example en .env, il est chargé automatiquement.'
    )
    Write-Host ''
    $lines | ForEach-Object { Write-Host $_ }
}

switch ($Task) {
    'help' { Show-Help }

    'install' {
        if (-not (Test-Path $VenvPython)) {
            Write-Step '1/3 · Création de l''environnement virtuel (.venv)'
            python -m venv (Join-Path $Root '.venv')
        }
        Write-Step '2/3 · Dépendances Python (versions figées)'
        & $VenvPip install --upgrade pip
        if (Test-Path (Join-Path $Root 'backend\requirements-dev.txt')) {
            & $VenvPip install -r (Join-Path $Root 'backend\requirements-dev.txt')
        } else {
            & $VenvPip install -e "$Root\backend[dev]"
        }
        Write-Step '3/3 · Dépendances de la console'
        if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
            Write-Warning 'npm introuvable : installez Node.js 18+ puis relancez .\dev.ps1 install'
        } else {
            Invoke-In $ConsoleDir { npm install --no-audit --no-fund }
        }
        Write-Host "`nInstallation terminée. Étapes suivantes : .\dev.ps1 migrate ; .\dev.ps1 demo" -ForegroundColor Green
    }

    'migrate' {
        Write-Step 'Migrations'
        Invoke-Manage @('migrate', '--noinput')
    }

    'demo' {
        Write-Step 'Démonstration (routeur simulé)'
        Invoke-Manage @('demo_smoke')
    }

    'test' {
        Write-Step 'Tests'
        Assert-Venv
        Invoke-In (Join-Path $Root 'backend') { & $VenvPython '-m' 'pytest' }
    }

    'lint' {
        Write-Step 'Ruff'
        Assert-Venv
        Invoke-In (Join-Path $Root 'backend') { & $VenvPython '-m' 'ruff' 'check' '.' }
    }

    'run' {
        Write-Step 'API — http://localhost:8001 (Ctrl+C pour arrêter)'
        Invoke-Manage @('runserver', '0.0.0.0:8001')
    }

    'console' {
        Write-Step 'Console — http://localhost:5173 (Ctrl+C pour arrêter)'
        Invoke-In $ConsoleDir { npm run dev }
    }

    'maquettes' {
        Write-Step 'Génération des maquettes statiques'
        Assert-Venv
        & $VenvPython (Join-Path $Root 'design\build.py')
        Write-Host 'Servir avec :  python -m http.server 8000 -d design\dist' -ForegroundColor DarkGray
    }

    'probe' {
        Write-Step "Test du routeur $RouterHost"
        if (-not $RouterPassword) {
            throw 'Renseignez -RouterPassword (mot de passe de l''utilisateur RouterOS).'
        }
        $arguments = @(
            'probe_router',
            '--host', $RouterHost,
            '--username', $RouterUser,
            '--password', $RouterPassword,
            '--port', "$RouterPort"
        )
        if ($Http) { $arguments += '--http' }
        if ($Interfaces) { $arguments += '--interfaces' }
        Invoke-Manage $arguments
    }
}
