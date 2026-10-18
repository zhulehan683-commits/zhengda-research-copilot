param(
  [string]$TargetRoot = (Join-Path $HOME '.agents\skills'),
  [string[]]$AgentRoot = @(),
  [ValidateSet('link', 'copy')][string]$Mode = 'link',
  [string]$Python = 'python',
  [switch]$Force,
  [switch]$Verify,
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$installer = Join-Path $PSScriptRoot 'install.py'
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
  throw 'install.py is missing; extract the complete repository.'
}
$arguments = @($installer, '--target-root', $TargetRoot, '--mode', $Mode)
foreach ($root in $AgentRoot) { $arguments += @('--agent-root', $root) }
if ($Force) { $arguments += '--force' }
if ($Verify) { $arguments += '--verify' }
if ($DryRun) { $arguments += '--dry-run' }
& $Python @arguments
if ($LASTEXITCODE -ne 0) { throw "Skill installer failed with exit code $LASTEXITCODE" }
