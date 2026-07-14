param(
    [int]$MaxRestarts = 5,
    [int]$PollSeconds = 60
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RunDir = Join-Path $RepoRoot "output\sp0_v1_1_cpu_full"
$ProcessFile = Join-Path $RunDir "process.json"
$WatchdogFile = Join-Path $RunDir "watchdog.json"
$ManifestFile = Join-Path $RepoRoot "results\sp0\SP0_PROTOCOL_v1_1\FINAL_RUN_MANIFEST.json"
$Python = (Get-Command python).Source
$Arguments = @(
    "-m", "experiments.sp0", "run-full",
    "--config", "configs/experiments/sp0/SP0_PROTOCOL_v1_1.yaml",
    "--repair-and-validate-b0",
    "--train-data-driven",
    "--freeze",
    "--run-b1-b7",
    "--extend-by-precision",
    "--analyze",
    "--render-figures",
    "--render-videos",
    "--resume",
    "--device", "cpu",
    "--allow-long-cpu-training",
    "--workers", "4"
)

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$restartCount = 0
while ($true) {
    $manifestStatus = $null
    if (Test-Path -LiteralPath $ManifestFile) {
        try {
            $manifestStatus = (Get-Content -LiteralPath $ManifestFile -Raw | ConvertFrom-Json).status
        } catch {
            $manifestStatus = "UNREADABLE"
        }
    }
    if ($manifestStatus -eq "SP0_COMPLETE") {
        [ordered]@{
            status = "COMPLETE"
            restarts = $restartCount
            completed_at = (Get-Date).ToUniversalTime().ToString("o")
            manifest = $ManifestFile
        } | ConvertTo-Json | Set-Content -LiteralPath $WatchdogFile -Encoding UTF8
        break
    }

    $record = $null
    if (Test-Path -LiteralPath $ProcessFile) {
        try {
            $record = Get-Content -LiteralPath $ProcessFile -Raw | ConvertFrom-Json
        } catch {
            $record = $null
        }
    }
    $running = $false
    if ($null -ne $record -and $null -ne $record.process_id) {
        $running = $null -ne (Get-Process -Id ([int]$record.process_id) -ErrorAction SilentlyContinue)
    }

    if (-not $running) {
        if ($restartCount -ge $MaxRestarts) {
            [ordered]@{
                status = "RESTART_LIMIT_REACHED"
                restarts = $restartCount
                stopped_at = (Get-Date).ToUniversalTime().ToString("o")
                last_manifest_status = $manifestStatus
            } | ConvertTo-Json | Set-Content -LiteralPath $WatchdogFile -Encoding UTF8
            break
        }
        $restartCount += 1
        $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
        $stdout = Join-Path $RunDir ("stdout-restart-{0:D2}-{1}.log" -f $restartCount, $stamp)
        $stderr = Join-Path $RunDir ("stderr-restart-{0:D2}-{1}.log" -f $restartCount, $stamp)
        $process = Start-Process -FilePath $Python -ArgumentList $Arguments -WorkingDirectory $RepoRoot -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
        [ordered]@{
            process_id = $process.Id
            started_at = (Get-Date).ToUniversalTime().ToString("o")
            command = ($Python + " " + ($Arguments -join " "))
            stdout = $stdout
            stderr = $stderr
            status = "RUNNING"
            restart = $restartCount
        } | ConvertTo-Json | Set-Content -LiteralPath $ProcessFile -Encoding UTF8
        $record = Get-Content -LiteralPath $ProcessFile -Raw | ConvertFrom-Json
    }

    [ordered]@{
        status = "MONITORING"
        process_id = $record.process_id
        restarts = $restartCount
        heartbeat_at = (Get-Date).ToUniversalTime().ToString("o")
        manifest_status = $manifestStatus
    } | ConvertTo-Json | Set-Content -LiteralPath $WatchdogFile -Encoding UTF8
    Start-Sleep -Seconds $PollSeconds
}