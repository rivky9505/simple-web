#!/usr/bin/env pwsh
<#
.SYNOPSIS
    SSH connection helper script for Azure VM
.DESCRIPTION
    Simplifies SSH connection to the Azure VM with the provided key file
.PARAMETER KeyFile
    Path to the SSH private key file
.PARAMETER Username
    SSH username (default: azureuser)
.PARAMETER IPAddress
    VM IP address (default: 108.143.33.48)
.EXAMPLE
    .\connect-vm.ps1 -KeyFile "C:\keys\mykey.pem"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$KeyFile,
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "azureuser",
    
    [Parameter(Mandatory=$false)]
    [string]$IPAddress = "108.143.33.48"
)

# Check if key file exists
if (-not (Test-Path $KeyFile)) {
    Write-Error "Key file not found: $KeyFile"
    exit 1
}

# Check if SSH is available
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Error "SSH client not found. Please install OpenSSH client."
    Write-Host "On Windows 10/11, you can install it via Settings > Apps > Optional Features > OpenSSH Client"
    exit 1
}

Write-Host "Connecting to Azure VM..." -ForegroundColor Green
Write-Host "IP Address: $IPAddress" -ForegroundColor Cyan
Write-Host "Username: $Username" -ForegroundColor Cyan
Write-Host "Key File: $KeyFile" -ForegroundColor Cyan
Write-Host ""

# Connect via SSH
ssh -i $KeyFile "$Username@$IPAddress"
