# Dumps the OpenAPI schema and regenerates packages/api-client types (Windows equivalent of `make gen-client`).
# Usage: .\scripts\gen-client.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$client = Join-Path $root "packages/api-client"

Push-Location $root
try {
    $lines = docker compose run --rm --no-deps -T api python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))"
    if ($LASTEXITCODE -ne 0) { throw "Failed to dump OpenAPI schema" }
    # Write with LF so the file is byte-identical to the one CI generates on Linux.
    [IO.File]::WriteAllText((Join-Path $client "openapi.json"), (($lines -join "`n") + "`n"))

    npx --yes pnpm@10 -C $client install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw "pnpm install failed" }
    npx --yes pnpm@10 -C $client run generate
    if ($LASTEXITCODE -ne 0) { throw "Type generation failed" }
}
finally {
    Pop-Location
}
