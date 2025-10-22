# tools/push_all.ps1
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

# localizar py
try { $py = (Get-Command py -ErrorAction Stop).Source } catch { $py = "" }
if (-not $py) { $py = "C:\Users\Usert\AppData\Local\Programs\Python\Python313\python.exe" }
if (-not (Test-Path $py)) { throw "Python no encontrado." }

# localizar git
try { $git = (Get-Command git -ErrorAction Stop).Source } catch { $git = "" }
if (-not $git) {
  $cand = "C:\Program Files\Git\bin\git.exe"
  if (Test-Path $cand) { $git = $cand } else { throw "Git no encontrado." }
}

Write-Host "== Normalizando CSVs (UTF-8, coma) ==" -ForegroundColor Cyan
& $py ".\tools\fix_mt5_csv_utf8.py"

Write-Host "== Publicando a GitHub ==" -ForegroundColor Cyan
& $git add -A
$pending = & $git status --porcelain
if ([string]::IsNullOrWhiteSpace($pending)) {
  Write-Host "Sin cambios que publicar." -ForegroundColor Yellow
  exit
}
$ts = Get-Date -Format "yyyy-MM-dd HH:mm"
& $git commit -m "Auto-publish CSVs ($ts)"
& $git push
Write-Host "✅ Listo. Revisa RAW en GitHub y carga en el HTML." -ForegroundColor Green
