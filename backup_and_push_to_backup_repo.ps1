#!/usr/bin/env powershell

param(
    [string]$SourceRepo = "kooshikooo-lab/instrument-designer",
    [string]$BackupRepo = "kooshikooo-lab/instrument-designer-backup",
    [string]$GitHubToken = $env:GITHUB_TOKEN,
    [string]$CommitMessage = "Weekly backup to repository"
)

set -ErrorAction Stop

# Authenticate to GitHub
$authHeader = @{"Authorization" = "token $GitHubToken"}
$apiBaseUrl = "https://api.github.com"

# Create git bundle
$dateTag = "backup-$(Get-Date -Format 'yyyy-MM-dd-HHmmss')"
$bundlePath = "$dateTag.bundle"

Write-Host "Creating git bundle: $bundlePath" -ForegroundColor Green

# Copy the entire repo to a temporary directory
$tempRepoDir = Join-Path $env:TEMP "instrument-designer-backup-$dateTag"
if (Test-Path $tempRepoDir) { Remove-Item $tempRepoDir -Recurse -Force }

Copy-Item -Path "*" -Destination $tempRepoDir -Recurse -Exclude "*.bundle",".git"

Push-Location $tempRepoDir

git init
Set-Content -Path ".git/config" @"
[remote "origin"]
	url = https://github.com/$BackupRepo.git
	fetch = +refs/heads/*:refs/remotes/origin/*
"
git add .

# Set up git config
git config user.email "github-actions@github.com"
git config user.name "github-actions"

Write-Host "Pushing bundle to local repository" -ForegroundColor Green
git bundle create "$bundlePath" --all

Pop-Location

Write-Host "Bundle created successfully: $bundlePath" -ForegroundColor Green

# Upload bundle to backup repo
Write-Host "Uploading bundle to backup repository..." -ForegroundColor Green

# Create tag in backup repo
$tagPath = "${dateTag}-bundle"

# Create a tag in the backup repo
$tagApiUrl = "$apiBaseUrl/repos/$BackupRepo/git/refs"
$createTagBody = @{
    "ref" = "refs/tags/$tagPath"
    "sha" = "045914bad0ff16e4f02d3e485bb83a1b9255c944"
    "force" = $false
}

$response = Invoke-RestMethod -Uri $tagApiUrl -Method Post -Headers $authHeader -Body ($createTagBody | ConvertTo-Json) -ContentType "application/json"

Write-Host "Tag created successfully: $tagPath" -ForegroundColor Green

# Get the commit SHA we're tagging
$infoResponse = Invoke-RestMethod -Uri "$apiBaseUrl/repos/$SourceRepo/commits?per_page=1" -Headers $authHeader -Method Get

$latestCommit = $infoResponse[0]
$commitSha = $latestCommit.sha

# Update the tag with the actual commit SHA (this overwrites the previous placeholder)
$response2 = Invoke-RestMethod -Uri "$tagApiUrl/refs/tags/$tagPath" -Method Patch -Headers $authHeader -Body (@{
    "sha" = $commitSha
} | ConvertTo-Json) -ContentType "application/json"

Write-Host "Tag updated with commit SHA: $commitSha" -ForegroundColor Green

# Create an annotated tag for clarity
$createAnnotatedTagBody = @{
    "tag" = $tagPath
    "message" = "Repository backup created on $(Get-Date)"
    "object" = $commitSha
    "type" = "commit"
}

$tagApiUrl2 = "$apiBaseUrl/repos/$BackupRepo/git/tags"
$response3 = Invoke-RestMethod -Uri $tagApiUrl2 -Method Post -Headers $authHeader -Body ($createAnnotatedTagBody | ConvertTo-Json) -ContentType "application/json"

Write-Host "Annotated tag created: $tagPath" -ForegroundColor Green

# Push bundle to GitHub releases
$uploadApiUrl = "$apiBaseUrl/repos/$BackupRepo/releases"
$getReleasesApiUrl = "$apiBaseUrl/repos/$BackupRepo/releases?per_page=1"

$getReleasesResponse = Invoke-RestMethod -Uri $getReleasesApiUrl -Headers $authHeader -Method Get

$latestRelease = $getReleasesResponse
$releaseId = $latestRelease.id

$releaseApiUrl = "$apiBaseUrl/repos/$BackupRepo/releases/$releaseId"
Update the release to add the bundle as an asset
$updateReleaseBody = @{
    "name" = "Repository Backup Bundle $dateTag"
    "body" = "Weekly backup of instrument-designer containing full repository history."
    "draft" = $false
    "prerelease" = $false
}

Invoke-RestMethod -Uri $releaseApiUrl -Method Patch -Headers $authHeader -Body ($updateReleaseBody | ConvertTo-Json) -ContentType "application/json"

# Actually upload the file
$fileStream = [System.IO.File]::OpenRead((Join-Path $tempRepoDir "$(Join-Path \"\" \"$bundlePath\")"))
$formData = [System.Net.Http.HttpRequestMessage]::New([System.Net.Http.HttpMethod]::Post, "$uploadApiUrl/assets?name=$bundlePath")

$content = [System.Net.Http.MultipartFormDataContent]::New()
$fileContent = [System.Net.Http.StreamContent]::New($fileStream)
$content.Add($fileContent, "file", "$bundlePath")
$formData.Content = $content

$handler = [System.Net.Http.HttpClientHandler]::New()
$client = [System.Net.Http.HttpClient]::New($handler)
$client.DefaultRequestHeaders.Authorization = [System.Net.Http.AuthenticationHeaderValue]::New("token", $GitHubToken)

$response = $client.PostAsync($uploadApiUrl, $content).Result
$response.EnsureSuccessStatusCode()

Write-Host "Bundle uploaded to GitHub releases" -ForegroundColor Green

# Clean up
Remove-Item -Path $tempRepoDir -Recurse -Force

Write-Host "Backup process completed successfully" -ForegroundColor Green