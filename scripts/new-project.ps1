# claude-home의 규칙·검사·문서 틀을 깐 새 프로젝트 폴더를 만듭니다.
# 언어별 뼈대(코드, 빌드 파일)는 만들지 않습니다. 그건 각 언어의 공식 도구로 만듭니다(new-project 스킬 참고).
# 공통 규칙·스킬·검사 도구는 마지막에 scripts/sync_rules.py가 넣습니다(Python 3.11 이상 필요).
#
# 실행: pwsh -File scripts/new-project.ps1 -Name my-app -Language python
#       pwsh -File scripts/new-project.ps1 -Name my-app -Language java -Description "반려동물 쇼핑몰 API" -WhatIf
#
# -Path        새 폴더를 만들 상위 폴더 (기본: claude-home이 있는 폴더, 예: C:\00.PROJECT)
# -Translation 번역 저장소용 규칙·스킬·TRANSLATION.md도 넣음
# -WhatIf      만들 파일만 보여 주고 아무것도 쓰지 않음

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')][string]$Name,
    [Parameter(Mandatory)][ValidateSet('java', 'python', 'typescript', 'dart', 'go')][string]$Language,
    [string]$Path,
    [string]$Description = '<이 저장소가 무엇인지 한두 문장>',
    [switch]$Translation
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)  # 한글 출력이 깨지지 않게
$repo = Split-Path -Parent $PSScriptRoot
if (-not $Path) { $Path = Split-Path -Parent $repo }
$target = Join-Path $Path $Name
$today = Get-Date -Format 'yyyy-MM-dd'
$script:cmd = $PSCmdlet
$script:written = @()

if ((Test-Path $target) -and (Get-ChildItem $target -Force | Select-Object -First 1)) {
    throw "이미 비어 있지 않은 폴더입니다: $target"
}

function Read-Template([string]$src) {
    return [IO.File]::ReadAllText((Join-Path $repo $src)) -replace "`r`n", "`n"
}

function Write-File([string]$dst, [string]$text) {
    $to = Join-Path $target $dst
    if ($script:cmd.ShouldProcess($dst, '만들기')) {
        New-Item -ItemType Directory -Force (Split-Path -Parent $to) | Out-Null
        [IO.File]::WriteAllText($to, ($text -replace "`r`n", "`n"), [Text.UTF8Encoding]::new($false))
    }
    $script:written += $dst
}

function Copy-File([string]$src, [string]$dst) {
    Write-File $dst (Read-Template $src)
}

# 언어별 설정
$lang = @{
    java       = @{ Lint = @{}; Commands = "./gradlew spotlessApply   # 포맷`n./gradlew test            # 테스트(ArchUnit 포함)`n./gradlew build           # 전체 빌드" }
    python     = @{ Lint = @{ 'python/ruff.toml' = 'ruff.toml' }; Commands = "ruff format .              # 포맷`nruff check --fix .         # 린트`npytest                     # 테스트" }
    typescript = @{ Lint = @{ 'typescript/eslint.config.js' = 'eslint.config.js'; 'typescript/.prettierrc.json' = '.prettierrc.json' }; Commands = "npx prettier --write .     # 포맷`nnpx eslint .               # 린트`nnpx tsc --noEmit           # 타입 검사`nnpm test                   # 테스트" }
    dart       = @{ Lint = @{ 'dart/analysis_options.yaml' = 'analysis_options.yaml' }; Commands = "dart format .              # 포맷`nflutter analyze            # 린트`nflutter test               # 테스트" }
    go         = @{ Lint = @{ 'go/.golangci.yml' = '.golangci.yml' }; Commands = "gofmt -w . && goimports -w .   # 포맷`ngolangci-lint run              # 린트`ngo test -race ./...            # 테스트" }
}[$Language]

# 1. 에이전트 설정 (공통 규칙·언어 규칙·스킬은 맨 끝의 sync_rules.py가 넣습니다)
Copy-File '.claude/settings.json' '.claude/settings.json'
if ($Translation) { Copy-File 'templates/translation-repo/TRANSLATION.md' 'TRANSLATION.md' }

# 2. 공통·언어별 린트 설정과 .gitignore
$ignore = @{
    java       = "out/`n*.iml`nbin/"
    python     = "*.egg-info/`n.coverage`nhtmlcov/"
    typescript = ".next/`n*.tsbuildinfo`n.turbo/"
    dart       = ".dart_tool/`n.flutter-plugins`n.flutter-plugins-dependencies`n*.iml`n.metadata"
    go         = "/bin/`n*.test`ncoverage.out"
}[$Language]
foreach ($f in '.editorconfig', '.gitattributes') { Copy-File "templates/lint/$f" $f }
Write-File '.gitignore' ((Read-Template 'templates/lint/.gitignore') + "`n# $Language`n$ignore`n")
foreach ($entry in $lang.Lint.GetEnumerator()) { Copy-File "templates/lint/$($entry.Key)" $entry.Value }

# 3. CI (검사 스크립트는 맨 끝의 sync_rules.py가 scripts/에 넣습니다)
Copy-File 'templates/ci/checks.yml' '.github/workflows/checks.yml'
Copy-File "templates/ci/lang/$Language.yml" ".github/workflows/$Language.yml"
Write-File '.env.example' "# 필요한 환경 변수를 값 없이 적습니다. 실제 값은 .env(커밋하지 않음)나 CI 비밀값에 둡니다.`n"

# 4. 문서
$agents = Read-Template 'templates/AGENTS.project.md'
$agents = $agents -replace '(?s)^<!--.*?-->\n\n', ''
$agents = $agents.Replace('<저장소 이름>', $Name).Replace('<이 저장소가 무엇인지 한두 문장>', $Description)
$agents = $agents.Replace("<테스트>`n<포맷·린트>", "$($lang.Commands)`npython -I scripts/repo_checks.py   # 저장소 규칙 검사")
if (-not $Translation) {
    $agents = $agents -replace '- 번역 저장소라면: [^\n]*\n', ''
}
Write-File 'AGENTS.md' $agents
Copy-File 'templates/CLAUDE.project.md' 'CLAUDE.md'
Copy-File '.github/pull_request_template.md' '.github/pull_request_template.md'

$readme = (Read-Template 'templates/docs/README.md').Replace('<프로젝트 이름>', $Name).Replace('<무엇을 하는 프로젝트인지 한두 문장>', $Description)
Write-File 'README.md' $readme
Copy-File 'templates/docs/CHANGELOG.md' 'CHANGELOG.md'
Copy-File 'templates/docs/adr/0001-template.md' 'docs/adr/template.md'
Copy-File 'templates/docs/exec-plans/plan-template.md' 'docs/exec-plans/plan-template.md'

Write-File 'docs/exec-plans/README.md' @"
# 실행 계획

여러 세션에 걸치는 작업의 계획과 기록입니다. 기능 동작은 ``README.md``와 ``docs/``, 설계 결정은 [ADR](../adr/)이 담당합니다.

## 진행 중

| 계획 | 목표 | 시작 |
|---|---|---|
| [초기 구축](active/0001-initial-setup.md) | 뼈대, 검사, 문서를 갖춘 첫 동작 버전 | $today |

## 완료

아직 없습니다.

## 관리 규칙

- 새 계획은 [plan-template.md](plan-template.md)를 복사해 ``active/``에 만들고 위 표에 추가합니다.
- 끝나면 최종 커밋과 검증 결과를 적고 ``completed/``로 옮긴 뒤 표를 옮깁니다.
- 당장 하지 않을 개선 후보가 생기면 ``tech-debt-tracker.md``를 만들어 적습니다.
"@

Write-File 'docs/exec-plans/active/0001-initial-setup.md' @"
# 초기 구축

- 상태: 진행 중
- 시작: $today
- 관련: 없음

## 목표

$Description

뼈대, 검사, 문서를 갖추고 CI가 통과하는 첫 동작 버전을 만듭니다.

## 현재 상태

다음 세션이 이 부분만 읽고 이어 갈 수 있게, 세션을 끝낼 때마다 덮어씁니다.

- 마지막 커밋: 없음
- 검사·테스트: 미확인
- 진행 중: 1단계
- 다음 할 일: 언어 공식 도구로 뼈대 생성
- 막힌 것: 없음

## 범위

- 하는 것: 언어 공식 도구로 뼈대 생성, 린트·포맷·계층 검사 적용, README·AGENTS.md 채우기, 기술 선택 ADR, 첫 기능 하나
- 안 하는 것: <이번에 하지 않을 것>

## 단계

- [ ] 1. 언어 공식 도구로 뼈대 생성 — 완료 조건: 빌드·테스트 명령이 로컬에서 동작
- [ ] 2. 린트·포맷·계층 검사 설정 적용 — 완료 조건: 포맷·린트 명령이 통과
- [ ] 3. 기술 선택을 ``docs/adr/0001-*.md``로 기록 — 완료 조건: 채택 상태의 ADR
- [ ] 4. README 시작하기와 AGENTS.md 명령어·동작 확인·구조 채우기 — 완료 조건: 자리표시(``<...>``) 없음
- [ ] 5. 첫 기능 하나와 테스트 — 완료 조건: 테스트 통과
- [ ] 6. GitHub 저장소에 올리고 CI 통과 — 완료 조건: ``checks``와 ``$Language`` 워크플로 성공

## 완료 조건

- 로컬과 CI에서 저장소 검사, 포맷·린트, 테스트가 모두 통과합니다.

## 검증

| 확인 | 명령·방법 | 결과 |
|---|---|---|
| 저장소 규칙 | ``python -I scripts/repo_checks.py`` | 미확인 |
| 언어 검사·테스트 | AGENTS.md의 명령어 | 미확인 |
| CI | GitHub Actions | 미확인 |

## 결정과 남은 문제

-

## 완료 기록

"@

# 5. Git 저장소
if ($script:cmd.ShouldProcess($target, 'git init -b main')) {
    git -C $target init -q -b main
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "git init이 실패했습니다(종료 코드 $LASTEXITCODE). 경로가 너무 길지 않은지 확인하고 직접 실행하세요: git -C `"$target`" init -b main"
    }
}

# 6. 공통 규칙·언어 규칙·스킬·검사 스크립트 (claude-home과 같은 내용을 유지하도록 한 곳에서 관리)
$sync = @('-I', (Join-Path $repo 'scripts/sync_rules.py'), '--target', $target, '--lang', $Language)
if ($Translation) { $sync += '--translation' }
if ($WhatIfPreference) {
    Write-Host "미리보기: 폴더를 만든 뒤 python $($sync -join ' ') --apply 로 규칙·스킬·검사 스크립트를 넣습니다"
}
else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw "python을 찾지 못했습니다. Python 3.11 이상을 설치한 뒤 직접 실행하세요: python $($sync -join ' ') --apply" }
    & $python.Source @sync --apply
    if ($LASTEXITCODE -ne 0) { throw "sync_rules.py가 실패했습니다(종료 코드 $LASTEXITCODE)" }
}

Write-Host ""
Write-Host "$($script:written.Count)개 파일$(if ($WhatIfPreference) { ' (미리보기, 쓰지 않음)' } else { '' }): $target"
Write-Host ""
Write-Host "다음 단계:"
Write-Host "  1. $Language 공식 도구로 뼈대 만들기 (기존 파일을 덮어쓰지 않게)"
Write-Host "  2. docs/exec-plans/active/0001-initial-setup.md의 단계를 따라 진행"
Write-Host "  3. 검사: python -I scripts/repo_checks.py"
