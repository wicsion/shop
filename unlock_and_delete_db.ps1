$dbPath = "C:\Users\goldi\PycharmProjects\study_projects\gifts_project\db.sqlite3"

if (!(Test-Path $dbPath)) {
    Write-Host "Database file not found: $dbPath"
    exit
}

$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($null -eq $pythonProcesses) {
    Write-Host "No python processes found. Trying to delete file..."
    Remove-Item $dbPath -Force
    Write-Host "File deleted successfully."
    exit
}

foreach ($proc in $pythonProcesses) {
    try {
        $modules = $proc.Modules | Where-Object { $_.FileName -like "*sqlite*" }
        if ($modules) {
            Write-Host "`nProcess PID $($proc.Id) might be locking SQLite file:"
            Write-Host "Process name: $($proc.ProcessName)"
            $answer = Read-Host "Kill process $($proc.Id)? (y/n)"
            if ($answer -eq 'y') {
                Stop-Process -Id $proc.Id -Force
                Write-Host "Process $($proc.Id) terminated."
            }
        }
    } catch {
        # Ignore errors accessing modules
    }
}

Start-Sleep -Seconds 1

try {
    Remove-Item $dbPath -Force
    Write-Host "`nFile deleted successfully."
} catch {
    Write-Host "`n❌ Could not delete file: $($_.Exception.Message)"
}
