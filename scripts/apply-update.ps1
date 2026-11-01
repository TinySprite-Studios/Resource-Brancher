param([int]$AppProcessId, [string]$Installer, [string]$InstallDirectory, [string]$LogFile)
$ErrorActionPreference = 'Stop'
try {
    $appProcess = Get-Process -Id $AppProcessId -ErrorAction SilentlyContinue
    if ($appProcess -and !$appProcess.WaitForExit(60000)) { throw 'Resource Brancher did not close. Please run the installer manually.' }
    $arguments = @('/SP-', '/SILENT', '/NORESTART', '/NORESTARTAPPLICATIONS', ('/LOG="' + $LogFile + '"'))
    if ($InstallDirectory) { $arguments += ('/DIR="' + $InstallDirectory + '"') }
    $setup = Start-Process -FilePath $Installer -ArgumentList $arguments -PassThru -Wait -WindowStyle Hidden
    if ($setup.ExitCode -notin @(0, 3010)) { throw "Installer failed ($($setup.ExitCode)). See $LogFile" }
    if (!$InstallDirectory) { $InstallDirectory = Join-Path $env:LOCALAPPDATA 'Programs\Resource Brancher' }
    Start-Process -FilePath (Join-Path $InstallDirectory 'Resource Brancher.exe') -WorkingDirectory $InstallDirectory
} catch {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($_.Exception.Message, 'Resource Brancher update') | Out-Null
}
