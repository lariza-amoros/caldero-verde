$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "No existe .venv. Crea el entorno e instala requirements.txt."
}

$requiredVariables = @("SUPABASE_URL", "SUPABASE_SECRET_KEY", "APP_ACCESS_PIN")
$envNames = Get-Content (Join-Path $projectRoot ".env") |
    ForEach-Object { if ($_ -match '^([^#=]+)=') { $matches[1] } }
$missing = $requiredVariables | Where-Object { $_ -notin $envNames }
if ($missing) {
    throw "Faltan variables locales: $($missing -join ', ')"
}

Push-Location $projectRoot
try {
    & $python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Fallaron las pruebas Python." }

    node --experimental-strip-types --test tests-js/*.test.mjs
    if ($LASTEXITCODE -ne 0) { throw "Fallaron las pruebas de la Function." }

    node scripts/build-functions.mjs
    if ($LASTEXITCODE -ne 0) { throw "Falló la compilación de la Function." }

    node --check frontend/app.js
    if ($LASTEXITCODE -ne 0) { throw "El JavaScript del frontend no es válido." }

    $health = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health" -TimeoutSec 15
    if ($health.status -ne "ok" -or $health.supabase -ne "connected") {
        throw "El backend local no confirmó la conexión con Supabase."
    }

    Write-Host "PRE-FLIGHT OK: Caldero Verde está listo para crear un deploy preview." -ForegroundColor Green
}
finally {
    Pop-Location
}
