<#
.SYNOPSIS
    Polls a GitHub repo for new/updated issues, PRs, discussions, commits,
    releases, and wiki changes. Reports new activity to the console and an
    append-only log file.

.DESCRIPTION
    Uses the gh CLI (must be installed and authenticated: run `gh auth login`).
    Tracks a JSON state file of already-seen items so each poll only reports
    genuinely new activity. The first run establishes a baseline and prints a
    summary instead of flooding the console.

    Monitored sources:
      - Issues & PRs      (REST: repos/{repo}/issues, `since` filter)
      - Discussions       (REST: repos/{repo}/discussions)
      - Commits           (REST: repos/{repo}/commits on the default branch)
      - Releases          (REST: repos/{repo}/releases)
      - Wiki              (git ls-remote on https://github.com/{repo}.wiki.git)

.PARAMETER Repo
    owner/name of the repository to watch. Default: the collaboration repo.

.PARAMETER IntervalSeconds
    Seconds between polls when looping. Default 300 (5 minutes).

.PARAMETER Once
    Run a single poll and exit. Combine with Task Scheduler for a robust
    every-N-minutes setup (see .EXAMPLE).

.PARAMETER StateFile
    Path to the JSON state file. Default: %LOCALAPPDATA%\GitHubMonitor\state.json

.PARAMETER LogFile
    Path to the append-only activity log. Default: %LOCALAPPDATA%\GitHubMonitor\monitor.log

.EXAMPLE
    .\scripts\github_monitor.ps1

    Loop forever, polling every 5 minutes.

.EXAMPLE
    .\scripts\github_monitor.ps1 -Once -Repo "owner/other-repo"

    Single check, exit. Register in Task Scheduler as:
      schtasks /Create /SC MINUTE /MO 5 /TN "GitHubMonitor" /TR "powershell -NoProfile -File C:\path\to\github_monitor.ps1 -Once"
#>
[CmdletBinding()]
param(
    [string[]]$Repo = @("kooshikooo-lab/instrument-designer"),
    [int]$IntervalSeconds = 300,
    [switch]$Once,
    [string]$StateFile = (Join-Path $env:LOCALAPPDATA "GitHubMonitor\state.json"),
    [string]$LogFile   = (Join-Path $env:LOCALAPPDATA "GitHubMonitor\monitor.log")
)

$ErrorActionPreference = "Stop"
$env:GIT_TERMINAL_PROMPT = "0"
$ProgressPreference = "SilentlyContinue"

# Scheduled tasks run with a limited PATH; make sure gh is reachable.
$ghExe = "C:\Program Files\GitHub CLI\gh.exe"
if (-not (Get-Command gh -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath $ghExe)) {
    $env:PATH = (Split-Path -Parent $ghExe) + ";" + $env:PATH
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "gh CLI not found. Install it and run 'gh auth login'."
    exit 1
}

# ---------------------------------------------------------------- helpers

function To-UtcDate {
    param([string]$s)
    if (-not $s) { return $null }
    return [datetime]::Parse($s).ToUniversalTime()
}

function Now-Utc {
    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Log-Info {
    param([string]$msg)
    $stamp = Now-Utc
    $line = "[$stamp] $msg"
    Write-Host $line
    if ($LogFile) {
        $dir = Split-Path -Parent $LogFile
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        Add-Content -Path $LogFile -Value $line -Encoding UTF8
    }
}

function Get-GhApi {
    param([string]$Path, [switch]$Paginate)
    if ($Paginate) {
        $out = & gh api --paginate $Path 2>$null
    } else {
        $out = & gh api $Path 2>$null
    }
    if ($LASTEXITCODE -ne 0) {
        throw "gh api failed for '$Path' (exit $LASTEXITCODE)"
    }
    if (-not $out) { return @() }
    $json = ($out -join "`n") | ConvertFrom-Json
    if ($null -eq $json) { return @() }
    return @($json)
}

function ConvertTo-Hashtable {
    param($InputObject)
    if ($null -eq $InputObject) { return $null }
    if ($InputObject -is [string]) { return $InputObject }
    if ($InputObject -is [PSCustomObject]) {
        $h = @{}
        foreach ($p in $InputObject.PSObject.Properties) { $h[$p.Name] = ConvertTo-Hashtable $p.Value }
        return $h
    }
    if ($InputObject -is [System.Collections.IEnumerable]) {
        $arr = @()
        foreach ($item in $InputObject) { $arr += ConvertTo-Hashtable $item }
        return $arr
    }
    return $InputObject
}

function Get-State {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        return ConvertTo-Hashtable ($raw | ConvertFrom-Json)
    }
    return @{ repos = @{} }
}

function Save-State {
    param($State, [string]$Path)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $State | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Ensure-RepoState {
    param($State, [string]$RepoName)
    if (-not $State.repos.ContainsKey($RepoName)) {
        $State.repos[$RepoName] = @{
            last_check_utc = $null
            issues         = @{}
            discussions    = @{}
            commits        = @{ tip_sha = $null; tip_date = $null }
            releases       = @{}
            wiki_head      = $null
        }
    }
    return $State.repos[$RepoName]
}

function Report-CommentCount {
    param($Comments)
    if ($null -ne $Comments) { return "comments: $Comments" }
    return ""
}

# ---------------------------------------------------------------- sources

function Get-DefaultBranch {
    param([string]$RepoName)
    $r = gh api "repos/$RepoName" 2>$null | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or $null -eq $r) { return "main" }
    return $r.default_branch
}

function Get-WikiHead {
    param([string]$RepoName)
    $out = & git ls-remote "https://github.com/$RepoName.wiki.git" HEAD 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
    return ($out -split "`t")[0]
}

# ---------------------------------------------------------------- poll

function Invoke-Poll {
    param([string]$RepoName, [string]$StatePath)
    $state = Get-State $StatePath
    $rs = Ensure-RepoState $state $RepoName
    $nowUtc = Now-Utc
    $lastCheck = To-UtcDate $rs.last_check_utc
    $defaultBranch = Get-DefaultBranch $RepoName
    $newCount = 0

    if (-not $lastCheck) {
        # ------------------------------------------------ baseline (first run)
        $issues   = Get-GhApi "repos/$RepoName/issues?state=all&sort=updated&direction=desc&per_page=100"
        $discs    = Get-GhApi "repos/$RepoName/discussions?per_page=100"
        $commits  = Get-GhApi "repos/$RepoName/commits?sha=$([uri]::EscapeDataString($defaultBranch))&per_page=100"
        $releases = Get-GhApi "repos/$RepoName/releases?per_page=100"
        $wikiHead = Get-WikiHead $RepoName

        foreach ($i in $issues) { $rs.issues[[string]$i.number] = $i.updated_at }
        foreach ($d in $discs)  { $rs.discussions[[string]$d.number] = $d.updatedAt }
        if ($commits.Count -gt 0) {
            $rs.commits.tip_sha  = $commits[0].sha
            $rs.commits.tip_date = $commits[0].commit.author.date
        }
        foreach ($r in $releases) { $rs.releases[[string]$r.id] = $r.tag_name }
        $rs.wiki_head = $wikiHead

        $latestCommit = ""
        if ($commits.Count -gt 0) { $latestCommit = "latest commit $($commits[0].sha.Substring(0,7))" }
        $wikiStatus = if ($wikiHead) { "wiki head $($wikiHead.Substring(0,7))" } else { "no wiki" }
        Log-Info "BASELINE for ${RepoName}: $($issues.Count) issues/PRs, $($discs.Count) discussions, $($releases.Count) releases, $latestCommit, $wikiStatus"

        $rs.last_check_utc = $nowUtc
        Save-State $state $StatePath
        Log-Info "Poll complete ($RepoName): baseline recorded. Nothing reported as new."
        return
    }

    # ------------------------------------------------ issues & PRs (since last poll)
    $sinceIso = $lastCheck.ToString("yyyy-MM-ddTHH:mm:ssZ")
    $issues = Get-GhApi "repos/$RepoName/issues?state=all&since=$([uri]::EscapeDataString($sinceIso))&per_page=100" -Paginate
    foreach ($i in $issues) {
        $num = [string]$i.number
        $upd = $i.updated_at
        $kind = if ($i.PSObject.Properties.Name -contains "pull_request") { "PR" } else { "ISSUE" }
        if (-not $rs.issues.ContainsKey($num)) {
            Log-Info "NEW $kind #$num : $($i.title) (by $($i.user.login), state=$($i.state)) $($i.html_url)"
            $newCount++
        } elseif ($rs.issues[$num] -ne $upd) {
            Log-Info "UPDATED $kind #$num : $($i.title) (state=$($i.state)) $($i.html_url)"
            $newCount++
        }
        $rs.issues[$num] = $upd
    }

    # ------------------------------------------------ discussions (client-side filter)
    $discs = Get-GhApi "repos/$RepoName/discussions?per_page=100" -Paginate
    foreach ($d in $discs) {
        $num = [string]$d.number
        $upd = $d.updatedAt
        if (-not $rs.discussions.ContainsKey($num)) {
            $cmts = Report-CommentCount $d.comments
            Log-Info "NEW DISCUSSION #$num : $($d.title) ($cmts)"
            $newCount++
        } else {
            $prev = To-UtcDate $rs.discussions[$num]
            $cur  = To-UtcDate $upd
            if ($cur -gt $lastCheck -and $prev -ne $cur) {
                Log-Info "UPDATED DISCUSSION #$num : $($d.title) (comments: $($d.comments))"
                $newCount++
            }
        }
        $rs.discussions[$num] = $upd
    }

    # ------------------------------------------------ commits on default branch
    # Tip-tracking: only commits reachable between the stored tip and the new
    # tip are reported, so history depth never causes a replay flood.
    $commits = Get-GhApi "repos/$RepoName/commits?sha=$([uri]::EscapeDataString($defaultBranch))&per_page=1"
    if ($commits.Count -gt 0) {
        $tip = $commits[0]
        if (-not $rs.commits.tip_sha -or $tip.sha -ne $rs.commits.tip_sha) {
            $newCountLocal = 0
            $foundPrev = $false
            $hist = Get-GhApi "repos/$RepoName/commits?sha=$([uri]::EscapeDataString($defaultBranch))&per_page=100" -Paginate
            foreach ($c in $hist) {
                if ($c.sha -eq $rs.commits.tip_sha) { $foundPrev = $true; break }
                $firstLine = ($c.commit.message -split "`n")[0]
                if ($firstLine.Length -gt 120) { $firstLine = $firstLine.Substring(0, 117) + "..." }
                Log-Info "NEW COMMIT $($c.sha.Substring(0,7)) ($defaultBranch): $firstLine"
                $newCountLocal++
                if ($newCountLocal -ge 500) { break }  # force-push safety cap
            }
            $newCount += $newCountLocal
            if (-not $foundPrev -and $newCountLocal -gt 0) {
                Log-Info "NOTE ($RepoName): previous tip not found in history (rewrite/force-push); rebaselined at $($tip.sha.Substring(0,7))"
            }
            $rs.commits.tip_sha  = $tip.sha
            $rs.commits.tip_date = $tip.commit.author.date
        }
    }

    # ------------------------------------------------ releases
    $releases = Get-GhApi "repos/$RepoName/releases?per_page=100" -Paginate
    foreach ($r in $releases) {
        $id = [string]$r.id
        if (-not $rs.releases.ContainsKey($id)) {
            $name = if ($r.name) { ": $($r.name)" } else { "" }
            Log-Info "NEW RELEASE $($r.tag_name)$name"
            $newCount++
            $rs.releases[$id] = $r.tag_name
        }
    }

    # ------------------------------------------------ wiki
    $wikiHead = Get-WikiHead $RepoName
    if ($wikiHead) {
        if (-not $rs.wiki_head) {
            Log-Info "NEW WIKI CREATED (head $($wikiHead.Substring(0,7)))"
            $newCount++
        } elseif ($rs.wiki_head -ne $wikiHead) {
            Log-Info "WIKI UPDATED ($($rs.wiki_head.Substring(0,7)) -> $($wikiHead.Substring(0,7)))"
            $newCount++
        }
        $rs.wiki_head = $wikiHead
    } elseif ($rs.wiki_head) {
        Log-Info "WIKI no longer reachable (removed or private); cleared watch head"
        $rs.wiki_head = $null
    }

    $rs.last_check_utc = $nowUtc
    Save-State $state $StatePath

    if ($newCount -eq 0) {
        Log-Info "Poll complete ($RepoName): no new activity."
    } else {
        Log-Info "Poll complete ($RepoName): $newCount new item(s)."
    }
}

# ---------------------------------------------------------------- main

Log-Info "GitHub monitor starting. Repos: $($Repo -join ', '), interval: ${IntervalSeconds}s. State: $StateFile"
Log-Info "Log: $LogFile"

do {
    foreach ($r in $Repo) {
        try {
            Invoke-Poll -RepoName $r -StatePath $StateFile
        } catch {
            Log-Info "POLL ERROR ($r): $_"
        }
    }
    if ($Once) { break }
    Start-Sleep -Seconds $IntervalSeconds
} while ($true)
