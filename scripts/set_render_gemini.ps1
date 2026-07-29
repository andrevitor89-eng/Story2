# Configura GEMINI_API_KEY no Render (requer RENDER_API_KEY no ambiente).
# Uso:
#   $env:RENDER_API_KEY = "rnd_..."
#   powershell -File scripts/set_render_gemini.ps1

$ErrorActionPreference = "Stop"
if (-not $env:RENDER_API_KEY) {
  Write-Host "Defina RENDER_API_KEY (Dashboard Render -> Account Settings -> API Keys)"
  exit 1
}

$envFile = Join-Path $PSScriptRoot "..\backend\.env"
$geminiLine = Get-Content $envFile | Where-Object { $_ -match "^GEMINI_API_KEY=.+" } | Select-Object -First 1
if (-not $geminiLine) { throw "GEMINI_API_KEY ausente em backend/.env" }
$gemini = $geminiLine.Substring("GEMINI_API_KEY=".Length).Trim()

$headers = @{
  Authorization = "Bearer $($env:RENDER_API_KEY)"
  Accept = "application/json"
  "Content-Type" = "application/json"
}

$services = Invoke-RestMethod -Uri "https://api.render.com/v1/services?limit=50" -Headers $headers
$svc = @($services | ForEach-Object { $_.service } | Where-Object { $_.name -eq "story2-api" }) | Select-Object -First 1
if (-not $svc) { throw "Servico story2-api nao encontrado na conta Render" }

$id = $svc.id
Write-Host "Servico: $($svc.name) ($id)"

# Lista atual e faz merge (PUT substitui tudo ù nao apagar DATABASE_URL etc.)
$current = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$id/env-vars" -Headers $headers
$map = @{}
foreach ($item in @($current)) {
  $ev = if ($item.envVar) { $item.envVar } else { $item }
  if ($ev.key) { $map[$ev.key] = $ev.value }
}

$map["GEMINI_API_KEY"] = $gemini
$map["STORAGE_BACKEND"] = "db"
$map["OFFLINE_FALLBACK"] = "false"
$map["APP_ENV"] = "prod"
$map["GEMINI_MODEL"] = "gemini-2.5-flash-image"
$map["GEMINI_FALLBACK_MODELS"] = "gemini-2.0-flash-preview-image-generation"
$map["GEMINI_MAX_RETRIES"] = "6"
$map["GEMINI_RETRY_BASE_SECONDS"] = "5"

$payload = @($map.GetEnumerator() | ForEach-Object { @{ key = $_.Key; value = $_.Value } }) | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Put -Uri "https://api.render.com/v1/services/$id/env-vars" -Headers $headers -Body $payload | Out-Null
Invoke-RestMethod -Method Post -Uri "https://api.render.com/v1/services/$id/deploys" -Headers $headers -Body "{}" | Out-Null
Write-Host "Env atualizado (com merge) e deploy disparado."
