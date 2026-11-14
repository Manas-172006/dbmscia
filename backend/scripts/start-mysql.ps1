# Script to start the local MySQL 8.4 server for Found It
param (
    [int]$Port = 3307
)

$DataDir = Join-Path $PSScriptRoot "..\data\mysql"
$DataDir = (Resolve-Path $DataDir).Path

# Verify datadir exists
if (-not (Test-Path $DataDir)) {
    Write-Host "Initializing MySQL data directory..."
    & mysqld --initialize-insecure --datadir="$DataDir" --console
}

Write-Host "Starting MySQL Server 8.4 on port $Port..."
Write-Host "Data directory: $DataDir"
& mysqld --datadir="$DataDir" --port=$Port --console
