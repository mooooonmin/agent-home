# claude-home의 규칙과 명령어를 ~/.claude/로 복사해 이 PC의 모든 프로젝트에서 쓰게 합니다.
# 같은 이름의 파일은 덮어쓰고, ~/.claude/에만 있는 파일은 지우지 않습니다.
#
# 실행: pwsh -File scripts/sync-local.ps1
#       pwsh -File scripts/sync-local.ps1 -WhatIf   # 복사할 파일만 보기

[CmdletBinding(SupportsShouldProcess)]
param()

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$userClaude = Join-Path $HOME '.claude'

foreach ($dir in 'rules', 'commands') {
    $src = Join-Path $repo ".claude/$dir"
    $dst = Join-Path $userClaude $dir
    Get-ChildItem $src -Recurse -File | ForEach-Object {
        $rel = [IO.Path]::GetRelativePath($src, $_.FullName)
        $target = Join-Path $dst $rel
        if ($PSCmdlet.ShouldProcess($target, "복사 ← $dir/$rel")) {
            New-Item -ItemType Directory -Force (Split-Path -Parent $target) | Out-Null
            Copy-Item $_.FullName $target -Force
            Write-Host "복사: ~/.claude/$dir/$rel"
        }
    }
}
