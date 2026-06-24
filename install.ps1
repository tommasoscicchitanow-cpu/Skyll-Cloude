<#
.SYNOPSIS
    Builds the Celestia watch face and installs it on a Wear OS device over
    Wireless Debugging (ADB over TCP/IP).

.DESCRIPTION
    One-shot installer for the Xiaomi Watch 2:
      1. Builds app-debug.apk with the Gradle wrapper.
      2. (First run only) pairs with the watch using a 6-digit code.
      3. Connects to the watch and installs the APK.

.PARAMETER WatchIp
    The watch IP shown under Developer options -> Wireless debugging.
    Default: 192.168.178.32

.PARAMETER ConnectPort
    The connection port shown on the Wireless debugging main screen.
    Default: 45491

.PARAMETER Pair
    Use this switch the FIRST time: it runs `adb pair` and asks for the
    pairing port + 6-digit code shown under "Pair device with pairing code".

.EXAMPLE
    .\install.ps1 -Pair
    (first time: pairs, then builds and installs)

.EXAMPLE
    .\install.ps1
    (subsequent runs: just builds and installs)
#>

param(
    [string]$WatchIp = "192.168.178.32",
    [int]$ConnectPort = 45491,
    [switch]$Pair,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

function Find-Adb {
    # 1) adb already on PATH?
    $cmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    # 2) standard Android SDK platform-tools locations
    $candidates = @(
        "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe",
        "$env:USERPROFILE\AppData\Local\Android\Sdk\platform-tools\adb.exe",
        "$env:ANDROID_HOME\platform-tools\adb.exe",
        "$env:ANDROID_SDK_ROOT\platform-tools\adb.exe"
    )
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    throw "adb non trovato. Installa 'Android SDK Platform-Tools' (o aprilo una volta da Android Studio) e riprova."
}

Write-Host "==> Celestia installer" -ForegroundColor Cyan
$adb = Find-Adb
Write-Host "    adb: $adb"

# --- 1. Build ---------------------------------------------------------------
$apk = Join-Path $ScriptDir "app\build\outputs\apk\debug\app-debug.apk"
if (-not $SkipBuild) {
    Write-Host "==> Compilo l'APK (gradlew assembleDebug)..." -ForegroundColor Cyan
    & "$ScriptDir\gradlew.bat" :app:assembleDebug
    if ($LASTEXITCODE -ne 0) { throw "Build fallita. Controlla l'output di Gradle qui sopra." }
}
if (-not (Test-Path $apk)) { throw "APK non trovato in $apk" }
Write-Host "    APK: $apk" -ForegroundColor Green

# --- 2. Pair (first run only) ----------------------------------------------
if ($Pair) {
    Write-Host "==> Accoppiamento. Sull'orologio: Debug wireless -> 'Abbina dispositivo con codice'." -ForegroundColor Cyan
    $pairPort = Read-Host "    Porta di ABBINAMENTO mostrata sull'orologio (NON la $ConnectPort)"
    $pairCode = Read-Host "    Codice a 6 cifre mostrato sull'orologio"
    & $adb pair "$($WatchIp):$pairPort" $pairCode
    if ($LASTEXITCODE -ne 0) { throw "Accoppiamento fallito. Verifica IP/porta/codice e che PC e orologio siano sulla stessa Wi-Fi." }
}

# --- 3. Connect + install ---------------------------------------------------
Write-Host "==> Connetto a $($WatchIp):$ConnectPort ..." -ForegroundColor Cyan
& $adb connect "$($WatchIp):$ConnectPort"
if ($LASTEXITCODE -ne 0) { throw "Connessione fallita. Se e' la prima volta rilancia con -Pair." }

Write-Host "==> Installo Celestia..." -ForegroundColor Cyan
& $adb -s "$($WatchIp):$ConnectPort" install -r $apk
if ($LASTEXITCODE -ne 0) { throw "Installazione fallita (vedi output adb)." }

Write-Host ""
Write-Host "FATTO! Ora sull'orologio: tieni premuto sul quadrante -> galleria -> scegli 'Celestia'." -ForegroundColor Green
Write-Host "Ricorda di concedere i permessi BODY_SENSORS (battito) e Posizione (mappa siderale)." -ForegroundColor Yellow
