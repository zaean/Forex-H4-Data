# tools/run_fix_and_push.ps1
$ErrorActionPreference = "Stop"

# Repo = carpeta padre de /tools
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

Write-Host "Repo: $repo" -ForegroundColor Cyan

# --- localizar Python ---
$py = ""
try {
  $py = (Get-Command py -ErrorAction Stop).Source
} catch { }
if (-not $py) {
  $cand = "C:\Users\Usert\AppData\Local\Programs\Python\Python313\python.exe"
  if (Test-Path $cand) { $py = $cand }
}
if (-not $py) { throw "Python no encontrado. Instálalo o agrega a PATH." }

# --- localizar Git ---
function Find-Git {
  try {
    $g = (Get-Command git -ErrorAction Stop).Source
    if ($g) { return $g }
  } catch {}
  $cand1 = "C:\Program Files\Git\bin\git.exe"
  if (Test-Path $cand1) { return $cand1 }
  $ghd = Get-ChildItem "$env:LOCALAPPDATA\GitHubDesktop" -Filter "app-*" -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
  if ($ghd) {
    $cand2 = Join-Path $ghd.FullName "resources\app\git\mingw64\bin\git.exe"
    if (Test-Path $cand2) { return $cand2 }
  }
  return $null
}
$git = Find-Git
if (-not $git) { throw "Git no encontrado. Instala Git for Windows o GitHub Desktop (incluye git)." }

Write-Host "Usando Python: $py" -ForegroundColor DarkCyan
Write-Host "Usando Git: $git" -ForegroundColor DarkCyan

# --- ejecutar fix ---
Write-Host "== Ejecutando fix_mt5_csv_overwrite.py ==" -ForegroundColor Cyan
& $py ".\tools\fix_mt5_csv_overwrite.py"

# --- ver si hay cambios ---
$changes = & $git status --porcelain
if (-not [string]::IsNullOrWhiteSpace($changes)) {
  Write-Host "== Cambios detectados: commit & push ==" -ForegroundColor Green
  & $git add -A
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm"
  & $git commit -m "Auto-fix MT5 CSV ($ts)"
  & $git push
} else {
  Write-Host "== Sin cambios. Nada que publicar ==" -ForegroundColor Yellow
}
