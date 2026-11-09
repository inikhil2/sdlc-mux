# sdlc-mux Windows helper. Windows support in v1 means WSL2 + Ubuntu (docs/adr/0005-wsl2-windows-path.md).
# This script does NOT install WSL: that needs an Administrator shell and a reboot.
# It only checks for WSL and prints what to do next. Safe to re-run.
$ErrorActionPreference = 'Stop'

Write-Host '==> Checking for WSL'
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    Write-Host 'wsl.exe not found. In an Administrator PowerShell run: wsl --install -d Ubuntu-24.04'
    Write-Host 'Reboot, create the Linux user, then re-run this script.'
    exit 1
}

Write-Host '==> Listing WSL distributions'
wsl.exe --list --quiet

Write-Host @'

==> Next, inside Ubuntu (not in PowerShell):
  git clone https://github.com/inikhil2/sdlc-mux ~/sdlc-mux   # keep it under ~, not /mnt/c
  cd ~/sdlc-mux
  bash scripts/install-wsl-ubuntu.sh

If no Ubuntu distribution is listed above, run in an Administrator PowerShell:
  wsl --install -d Ubuntu-24.04
'@
