param(
  [string]$TargetRoot = (Join-Path $HOME '.agents\skills'),
  [switch]$Force
)
$ErrorActionPreference = 'Stop'
$source = (Split-Path -Parent $MyInvocation.MyCommand.Path)
$target = Join-Path $TargetRoot 'market-survey-competition'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$staging = "$target.staging-$stamp"
$backup = $null

if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
  throw 'SKILL.md is missing; extract the complete ZIP before installation.'
}
if (-not (Test-Path -LiteralPath (Join-Path $source 'scripts\workflow.py') -PathType Leaf)) {
  throw 'scripts\workflow.py is missing; the distribution appears incomplete.'
}
if ((Test-Path -LiteralPath $target) -and -not $Force) {
  throw "Skill already exists: $target. Review current files first; add -Force to replace intentionally."
}

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
try {
  New-Item -ItemType Directory -Path $staging | Out-Null
  # Copy the source directory's contents, not the source directory as an extra nested level.
  Get-ChildItem -LiteralPath $source -Force | Copy-Item -Destination $staging -Recurse -Force
  if (-not (Test-Path -LiteralPath (Join-Path $staging 'SKILL.md') -PathType Leaf)) {
    throw 'Staging validation failed: SKILL.md missing.'
  }
  if (-not (Test-Path -LiteralPath (Join-Path $staging 'references\stages.md') -PathType Leaf)) {
    throw 'Staging validation failed: references\stages.md missing.'
  }
  if (-not (Test-Path -LiteralPath (Join-Path $staging 'scripts\workflow.py') -PathType Leaf)) {
    throw 'Staging validation failed: scripts\workflow.py missing.'
  }

  if (Test-Path -LiteralPath $target) {
    $backup = "$target.backup-$stamp"
    Move-Item -LiteralPath $target -Destination $backup
    Write-Host "Previous version backed up to $backup"
  }
  try {
    Move-Item -LiteralPath $staging -Destination $target
  }
  catch {
    if ($backup -and (Test-Path -LiteralPath $backup) -and -not (Test-Path -LiteralPath $target)) {
      Move-Item -LiteralPath $backup -Destination $target
    }
    throw
  }
}
finally {
  if (Test-Path -LiteralPath $staging) {
    Remove-Item -LiteralPath $staging -Recurse -Force
  }
}

Write-Host "Installed: $target"
Write-Host 'Open a new Codex session and mention $market-survey-competition.'
Write-Host 'Local Python scripts require Python 3.10+; they use the standard library only.'
