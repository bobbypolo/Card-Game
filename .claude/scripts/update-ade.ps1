# update-ade.ps1 - Update existing project to latest Claude Workflow
# Usage: update-ade "C:\Path\To\ExistingProject"
#
# This script updates workflow infrastructure WITHOUT touching your:
# - prd.json (stories)
# - PLAN.md, HANDOFF.md, ARCHITECTURE.md (project docs)
# - lessons.md (knowledge)
# - config.yaml (project config)
# - Any ADRs you created (001-*.md, etc.)
#
# File ownership model:
#   Category A (overwrite)  — ADE infrastructure: hooks, agents, skills, settings.json
#   Category B (merge)      — Mixed ownership: CLAUDE.md, .gitignore (managed blocks),
#                             workflow.json (keyed merge)
#   Category C (never touch)— Project content: prd.json, PLAN.md, ARCHITECTURE.md, etc.

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$TargetPath
)

$WorkflowRepo = "https://github.com/bobbypolo/ClaudeWorkflow.git"
$TempDir = Join-Path $env:TEMP "claude-ade-update-$(Get-Random)"

Write-Host ""
Write-Host "Updating ADE workflow in: $TargetPath" -ForegroundColor Cyan
Write-Host ""

# Verify target exists and has .claude folder
if (-not (Test-Path "$TargetPath\.claude")) {
    Write-Error "No .claude folder found in $TargetPath. Use new-ade.ps1 for new projects."
    exit 1
}

# Clone latest workflow to temp
Write-Host "  Fetching latest workflow..." -ForegroundColor Gray
git clone --depth 1 --quiet $WorkflowRepo $TempDir 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to clone workflow repository"
    exit 1
}

# ── Category A: Files to overwrite (ADE infrastructure only) ──────────────
$FilesToUpdate = @(
    # Agents (6)
    ".claude\agents\architect.md",
    ".claude\agents\builder.md",
    ".claude\agents\librarian.md",
    ".claude\agents\ralph-worker.md",
    ".claude\agents\ralph-story.md",
    ".claude\agents\qa-reviewer.md",

    # Skills (11) + protocol card
    ".claude\skills\ralph\SKILL.md",
    ".claude\skills\ralph\PROTOCOL_CARD.md",
    ".claude\skills\brainstorm\SKILL.md",
    ".claude\skills\build-system\SKILL.md",
    ".claude\skills\plan\SKILL.md",
    ".claude\skills\verify\SKILL.md",
    ".claude\skills\handoff\SKILL.md",
    ".claude\skills\learn\SKILL.md",
    ".claude\skills\decision\SKILL.md",
    ".claude\skills\refresh\SKILL.md",
    ".claude\skills\health\SKILL.md",
    ".claude\skills\audit\SKILL.md",

    # Hooks
    ".claude\hooks\_lib.py",
    ".claude\hooks\_prod_patterns.py",
    ".claude\hooks\_qa_lib.py",
    ".claude\hooks\_audit_lib.py",
    ".claude\hooks\pre_bash_guard.py",
    ".claude\hooks\post_bash_capture.py",
    ".claude\hooks\post_format.py",
    ".claude\hooks\post_write_prod_scan.py",
    ".claude\hooks\stop_verify_gate.py",
    ".claude\hooks\post_compact_restore.py",

    # Quality utilities
    ".claude\hooks\qa_runner.py",
    ".claude\hooks\test_quality.py",
    ".claude\hooks\plan_validator.py",

    # Hook tests
    ".claude\hooks\tests\__init__.py",
    ".claude\hooks\tests\conftest.py",
    ".claude\hooks\tests\test_lib_quality.py",
    ".claude\hooks\tests\test_plan_validator.py",
    ".claude\hooks\tests\test_post_bash_capture.py",
    ".claude\hooks\tests\test_post_compact_restore.py",
    ".claude\hooks\tests\test_post_format.py",
    ".claude\hooks\tests\test_post_write_prod_scan.py",
    ".claude\hooks\tests\test_pre_bash_guard.py",
    ".claude\hooks\tests\test_qa_runner.py",
    ".claude\hooks\tests\test_stop_verify_gate.py",
    ".claude\hooks\tests\test_test_quality.py",
    ".claude\hooks\tests\test_qa_lib.py",
    ".claude\hooks\tests\test_verification_log.py",
    ".claude\hooks\tests\test_workflow_state.py",
    ".claude\hooks\tests\test_worktree_isolation.py",
    ".claude\hooks\tests\test_audit_lib.py",
    ".claude\hooks\tests\test_lean_skill.py",
    ".claude\hooks\tests\test_ralph_story_agent.py",
    ".claude\hooks\tests\test_story007_hardening.py",

    # Rules
    ".claude\rules\code-quality.md",
    ".claude\rules\production-standards.md",

    # Settings (hooks wiring — overwrites to ensure new hooks are wired)
    ".claude\settings.json",

    # Knowledge (conventions, shared definitions)
    ".claude\docs\knowledge\conventions.md",
    ".claude\docs\knowledge\planning-anti-patterns.md",
    ".claude\docs\knowledge\README.md",
    ".claude\docs\knowledge\state-ownership.md",

    # Doc templates (not project content)
    ".claude\docs\decisions\000-template.md",
    ".claude\docs\decisions\README.md",

    # Templates
    ".claude\templates\config.yaml",
    ".claude\templates\qa_receipt_fallback.json",

    # Root-level (ADE docs only — CLAUDE.md and .gitignore handled separately)
    "WORKFLOW.md",
    ".mcp.json.example"
)

Write-Host "  Updating workflow files..." -ForegroundColor Gray

$OverwriteCount = 0
foreach ($File in $FilesToUpdate) {
    $Source = Join-Path $TempDir $File
    $Dest = Join-Path $TargetPath $File

    if (Test-Path $Source) {
        # Ensure destination directory exists
        $DestDir = Split-Path $Dest -Parent
        if (-not (Test-Path $DestDir)) {
            New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
        }

        Copy-Item -Path $Source -Destination $Dest -Force
        Write-Host "    Overwritten: $File" -ForegroundColor DarkGray
        $OverwriteCount++
    }
}

# Also copy update script itself
$UpdateScript = Join-Path $TempDir ".claude\scripts\update-ade.ps1"
if (Test-Path $UpdateScript) {
    Copy-Item -Path $UpdateScript -Destination "$TargetPath\.claude\scripts\update-ade.ps1" -Force
}

# ── Category B: Managed-block merge (CLAUDE.md, .gitignore) ──────────────

function Update-ManagedBlock {
    param(
        [string]$RelPath,
        [string]$BeginMarker,
        [string]$EndMarker
    )

    $SourcePath = Join-Path $TempDir $RelPath
    $DestPath = Join-Path $TargetPath $RelPath

    if (-not (Test-Path $SourcePath)) { return }

    # Ensure destination directory exists
    $DestDir = Split-Path $DestPath -Parent
    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    }

    $SourceContent = Get-Content $SourcePath -Raw

    # Extract ADE block from source (including markers)
    $EscBegin = [regex]::Escape($BeginMarker)
    $EscEnd = [regex]::Escape($EndMarker)
    $Pattern = "(?s)$EscBegin.*?$EscEnd"

    if ($SourceContent -notmatch $Pattern) {
        # Source has no markers — full copy as fallback
        Copy-Item -Path $SourcePath -Destination $DestPath -Force
        Write-Host "    Overwritten: $RelPath (no markers in source)" -ForegroundColor DarkGray
        return
    }
    $SourceBlock = $Matches[0]

    if (-not (Test-Path $DestPath)) {
        # Target doesn't exist — full copy
        Copy-Item -Path $SourcePath -Destination $DestPath -Force
        Write-Host "    Added: $RelPath (with ADE markers)" -ForegroundColor DarkGray
        return
    }

    $DestContent = Get-Content $DestPath -Raw

    if ($DestContent -match $EscBegin) {
        # Target has markers — replace only the ADE block, preserve project content
        $NewContent = [regex]::Replace($DestContent, $Pattern, $SourceBlock)
        [System.IO.File]::WriteAllText($DestPath, $NewContent)
        Write-Host "    Merged: $RelPath (ADE block updated, project content preserved)" -ForegroundColor DarkCyan
    } else {
        # Target has no markers (legacy/first managed update) — full overwrite
        Copy-Item -Path $SourcePath -Destination $DestPath -Force
        Write-Host "    Overwritten: $RelPath (markers added for future merges)" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "  Merging managed files..." -ForegroundColor Gray

Update-ManagedBlock -RelPath "CLAUDE.md" `
    -BeginMarker "<!-- BEGIN ADE MANAGED" `
    -EndMarker "<!-- END ADE MANAGED -->"

Update-ManagedBlock -RelPath ".gitignore" `
    -BeginMarker "# BEGIN ADE MANAGED" `
    -EndMarker "# END ADE MANAGED"

# ── Category B: Keyed merge (workflow.json) ───────────────────────────────

$SourceWfJson = Join-Path $TempDir ".claude\workflow.json"
$DestWfJson = Join-Path $TargetPath ".claude\workflow.json"

if ((Test-Path $SourceWfJson) -and (Test-Path $DestWfJson)) {
    # Use Python for reliable JSON merge with consistent formatting
    $MergeScript = Join-Path $TempDir "_merge_workflow.py"

    @"
import json, sys

source_path = sys.argv[1]
target_path = sys.argv[2]

with open(source_path, encoding='utf-8') as f:
    source = json.load(f)
with open(target_path, encoding='utf-8') as f:
    target = json.load(f)

# ADE-owned top-level keys — always take from source
ade_keys = [
    'qa_runner', 'test_quality', 'verification_log', 'plan_sync',
    'agent_config', 'audit_modes'
]
for key in ade_keys:
    if key in source:
        target[key] = source[key]

# Commands — ADE owns regression*, project owns test/lint/format
if 'commands' in source:
    if 'commands' not in target:
        target['commands'] = source['commands']
    else:
        ade_cmd_keys = ['regression', 'regression_default_tier', 'regression_tiers']
        for key in ade_cmd_keys:
            if key in source['commands']:
                target['commands'][key] = source['commands'][key]
        # Add any new command keys from source that target doesn't have
        project_cmd_keys = {'test', 'lint', 'format'}
        for key in source['commands']:
            if key not in ade_cmd_keys and key not in project_cmd_keys:
                if key not in target['commands']:
                    target['commands'][key] = source['commands'][key]

# New top-level keys in source not in target — add them
for key in source:
    if key not in target:
        target[key] = source[key]

with open(target_path, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(target, f, indent=2, ensure_ascii=False)
    f.write('\n')
"@ | Set-Content -Path $MergeScript -Encoding UTF8

    python $MergeScript $SourceWfJson $DestWfJson

    if ($LASTEXITCODE -eq 0) {
        Write-Host "    Merged: .claude\workflow.json (ADE keys updated, project keys preserved)" -ForegroundColor DarkCyan
    } else {
        # Fallback: full overwrite
        Copy-Item -Path $SourceWfJson -Destination $DestWfJson -Force
        Write-Host "    Overwritten: .claude\workflow.json (merge failed, full overwrite)" -ForegroundColor DarkYellow
    }
} elseif (Test-Path $SourceWfJson) {
    Copy-Item -Path $SourceWfJson -Destination $DestWfJson -Force
    Write-Host "    Added: .claude\workflow.json" -ForegroundColor DarkGray
}

# ── Cleanup stale files from previous workflow versions ───────────────────

Write-Host ""
Write-Host "  Cleaning stale files..." -ForegroundColor Gray

$StaleFiles = @(
    ".claude\scripts\new-ade.ps1",             # Removed from deployments — only needed in source repo
    ".claude\rules\research-core.md",          # Moved to .claude\docs\ in v5.1
    "templates\SPEC.md",                        # Moved to .claude\templates\ in v6
    ".claude\.stop_block_count",                # Cleanup artifact from stop gate
    ".claude\agents\qa.md",                     # Replaced by /verify skill in v6
    ".claude\templates\SPEC.md",                # Moved to Research ADE
    ".claude\docs\research-core.md",            # Moved to Research ADE
    ".claude\docs\research-reference.md",       # Moved to Research ADE
    ".claude\docs\RESEARCH_SETUP.md",           # Moved to Research ADE
    ".claude\docs\MCP_TOOLS.md",                # Moved to Research ADE
    ".claude\commands\research.md",             # Moved to Research ADE
    ".claude\commands\research-resume.md",      # Moved to Research ADE
    ".claude\commands\research-status.md",      # Moved to Research ADE
    ".claude\commands\research-validate.md",    # Moved to Research ADE
    ".claude\commands\cite.md",                 # Moved to Research ADE
    "research\.gitkeep",                        # Research dir moved to Research ADE
    ".claude\ralph-sprint-state.json",          # Replaced by .workflow-state.json in v7
    ".claude\ralph-state.json",                 # Replaced by .workflow-state.json in v7
    ".claude\hooks\tests\test_handoff_skill.py",    # Deleted in research pipeline separation
    ".claude\hooks\tests\test_plan_smart_sizing.py" # Deleted in research pipeline separation
)

# Remove stale directories (recurse)
$StaleDirs = @(
    ".claude\commands\research-phases"          # Moved to Research ADE
)

$StaleCount = 0
foreach ($Dir in $StaleDirs) {
    $DirPath = Join-Path $TargetPath $Dir
    if (Test-Path $DirPath) {
        Remove-Item -Path $DirPath -Recurse -Force
        Write-Host "    Removed stale dir: $Dir" -ForegroundColor DarkYellow
        $StaleCount++
    }
}

foreach ($Stale in $StaleFiles) {
    $StalePath = Join-Path $TargetPath $Stale
    if (Test-Path $StalePath) {
        Remove-Item -Path $StalePath -Force
        Write-Host "    Removed stale: $Stale" -ForegroundColor DarkYellow
        $StaleCount++
    }
}

# Remove stale .claude\commands\ dir if now empty (replaced by skills/)
$StaleCommandsDir = Join-Path $TargetPath ".claude\commands"
if ((Test-Path $StaleCommandsDir) -and ((Get-ChildItem $StaleCommandsDir | Measure-Object).Count -eq 0)) {
    Remove-Item -Path $StaleCommandsDir -Force
    Write-Host "    Removed empty: .claude\commands\" -ForegroundColor DarkYellow
}

# Remove stale root templates/ dir if now empty
$StaleTemplatesDir = Join-Path $TargetPath "templates"
if ((Test-Path $StaleTemplatesDir) -and ((Get-ChildItem $StaleTemplatesDir | Measure-Object).Count -eq 0)) {
    Remove-Item -Path $StaleTemplatesDir -Force
    Write-Host "    Removed empty: templates\" -ForegroundColor DarkYellow
}

# Cleanup temp
Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue

# ── Summary ───────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Update complete!" -ForegroundColor Green
Write-Host "  Overwritten: $OverwriteCount files (ADE infrastructure)" -ForegroundColor DarkGray
Write-Host "  Merged: CLAUDE.md, .gitignore, workflow.json (project content preserved)" -ForegroundColor DarkCyan
if ($StaleCount -gt 0) {
    Write-Host "  Removed: $StaleCount stale files/dirs" -ForegroundColor DarkYellow
}
Write-Host ""
Write-Host "Files never touched:" -ForegroundColor Yellow
Write-Host "  - .claude/prd.json (your stories)"
Write-Host "  - .claude/docs/PLAN.md (your plan)"
Write-Host "  - .claude/docs/HANDOFF.md (your session state)"
Write-Host "  - .claude/docs/ARCHITECTURE.md (your architecture)"
Write-Host "  - .claude/docs/knowledge/lessons.md (your lessons)"
Write-Host "  - .mcp.json (your MCP server config)"
Write-Host "  - PROJECT_BRIEF.md (your project brief)"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. cd `"$TargetPath`""
Write-Host "  2. Run: claude"
Write-Host "  3. Type: /health"
Write-Host ""
