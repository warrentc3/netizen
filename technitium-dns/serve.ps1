#Requires -Version 7.0
<#
.SYNOPSIS
    Serve the Swagger UI locally and open a browser. Downloads Swagger UI assets on first run if missing.
    Auto-shuts down when the browser tab closes (no requests for 10 seconds after initial load).
.PARAMETER Port
    Port to serve on. Defaults to 8080. If in use, walks up to Port+10.
#>
param(
    [int]$Port = 8080,
    [switch]$KeepAlive
)
$ErrorActionPreference = 'Stop'
$port = $Port
$dir = $PSScriptRoot
$url = "http://127.0.0.1:$port/index.html"
$idleTimeout = 120
$cts = [System.Threading.CancellationTokenSource]::new()

$assets = @{
    'swagger-ui.css'                   = 'https://unpkg.com/swagger-ui-dist@5/swagger-ui.css'
    'swagger-ui-bundle.js'             = 'https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js'
    'swagger-ui-standalone-preset.js'  = 'https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js'
}

foreach ($file in $assets.GetEnumerator()) {
    $path = Join-Path $dir $file.Key
    if (-not (Test-Path $path)) {
        Write-Host "Downloading $($file.Key)..."
        Invoke-WebRequest -Uri $file.Value -OutFile $path -UseBasicParsing
        Write-Host "  Saved $($file.Key) ($((Get-Item $path).Length.ToString('N0')) bytes)"
    }
}

$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add("http://127.0.0.1:$port/")

try {
    $listener.Start()
}
catch {
    $maxPort = $port + 10
    $found = $false
    for ($p = $port + 1; $p -le $maxPort; $p++) {
        try {
            $listener.Close()
            $listener = [System.Net.HttpListener]::new()
            $listener.Prefixes.Add("http://127.0.0.1:$p/")
            $listener.Start()
            $port = $p
            $url = "http://127.0.0.1:$port/index.html"
            $found = $true
            break
        }
        catch { continue }
    }
    if (-not $found) {
        Write-Error "Could not bind to any port in range 8080-$maxPort."
        exit 1
    }
}

Write-Host "`nServing $dir"
Write-Host "Open: $url"
if ($KeepAlive) {
    Write-Host "KeepAlive enabled — Ctrl+C to stop."
} else {
    Write-Host "Auto-stops after ${idleTimeout}s of inactivity. Use -KeepAlive to disable. Ctrl+C to stop manually."
}

Start-Process $url

$lastRequest = [DateTime]::UtcNow
$initialLoad = $false

try {
    while ($listener.IsListening) {
        $task = $listener.GetContextAsync()

        while (-not $task.Wait(1000)) {
            if ($cts.Token.IsCancellationRequested) { break }
            if ($initialLoad -and -not $KeepAlive) {
                $idle = ([DateTime]::UtcNow - $lastRequest).TotalSeconds
                if ($idle -ge $idleTimeout) {
                    Write-Host "`nNo activity for ${idleTimeout}s — shutting down."
                    break
                }
            }
        }

        if (-not $task.IsCompleted) { break }

        $context = $task.Result
        $request = $context.Request
        $response = $context.Response
        $lastRequest = [DateTime]::UtcNow

        $relativePath = $request.Url.LocalPath.TrimStart('/')
        if ([string]::IsNullOrEmpty($relativePath)) { $relativePath = 'index.html' }
        if ($relativePath -eq 'index.html') { $initialLoad = $true }

        $filePath = Join-Path $dir $relativePath

        if (Test-Path $filePath -PathType Leaf) {
                $bytes = [System.IO.File]::ReadAllBytes($filePath)
                $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
                $response.ContentType = switch ($ext) {
                    '.html' { 'text/html; charset=utf-8' }
                    '.json' { 'application/json; charset=utf-8' }
                    '.js'   { 'application/javascript; charset=utf-8' }
                    '.css'  { 'text/css; charset=utf-8' }
                    '.png'  { 'image/png' }
                    '.svg'  { 'image/svg+xml' }
                    default { 'application/octet-stream' }
                }
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            }
            else {
                $response.StatusCode = 404
                $msg = [System.Text.Encoding]::UTF8.GetBytes('Not found')
                $response.ContentLength64 = $msg.Length
                $response.OutputStream.Write($msg, 0, $msg.Length)
            }

        $response.OutputStream.Close()
    }
}
finally {
    $cts.Cancel()
    $listener.Stop()
    $listener.Close()
    Write-Host "Stopped."
}
