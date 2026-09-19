# AgentBetta Windows GUI acceptance test via UI Automation.
# Non-destructive: does not click Clear history / Delete keys / Clear browser data.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\gui_uat.ps1 [-DumpSettings]

param([switch]$DumpSettings)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes

$AE = [System.Windows.Automation.AutomationElement]
$CT = [System.Windows.Automation.ControlType]
$TS = [System.Windows.Automation.TreeScope]
$SIP = [System.Windows.Automation.SelectionItemPattern]
$results = New-Object System.Collections.ArrayList

function Add-Result($name, $ok, $detail) {
    [void]$results.Add([pscustomobject]@{ Check = $name; OK = [bool]$ok; Detail = [string]$detail })
}
function Get-AppWindow {
    return $AE::RootElement.FindFirst($TS::Children, [System.Windows.Automation.PropertyCondition]::new($AE::NameProperty, "AgentBetta"))
}
function Find-AllType($scope, $type) {
    return $scope.FindAll($TS::Descendants, [System.Windows.Automation.PropertyCondition]::new($AE::ControlTypeProperty, $type))
}
function Find-ByName($scope, $type, $name) {
    foreach ($e in (Find-AllType $scope $type)) { if ($e.Current.Name -eq $name) { return $e } }
    return $null
}
function Get-View($win, $view) {
    foreach ($g in (Find-AllType $win $CT::Group)) {
        if ($g.Current.AutomationId -like "*$view*" -and -not $g.Current.IsOffscreen) { return $g }
    }
    return $null
}
function Invoke-Button($scope, $name) {
    $b = Find-ByName $scope $CT::Button $name
    if (-not $b) { return $false }
    $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    return $true
}
function Select-Nav($win, $name) {
    foreach ($it in (Find-AllType $win $CT::ListItem)) {
        if ($it.Current.Name -eq $name) {
            $it.GetCurrentPattern($SIP::Pattern).Select()
            return $true
        }
    }
    return $false
}
function Normalize($s) { return ($s -replace '&', '' -replace '\s+', ' ').Trim() }
function Select-Tab($view, $name) {
    $target = Normalize $name
    foreach ($it in (Find-AllType $view $CT::TabItem)) {
        if ((Normalize $it.Current.Name) -eq $target) { $it.GetCurrentPattern($SIP::Pattern).Select(); return $true }
    }
    foreach ($e in (Find-AllType $view $CT::Text)) {
        if ((Normalize $e.Current.Name) -eq $target) {
            try { $e.GetCurrentPattern($SIP::Pattern).Select(); return $true } catch { }
        }
    }
    return $false
}
function Get-ComboItems($scope) {
    $out = @()
    foreach ($c in (Find-AllType $scope $CT::ComboBox)) {
        $items = @()
        try {
            $c.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Expand()
            Start-Sleep -Milliseconds 250
            $items = (Find-AllType $c $CT::ListItem | ForEach-Object { $_.Current.Name })
            $c.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Collapse()
        } catch { $items = @("<expand-failed>") }
        $out += , $items
    }
    return $out
}
function Get-BrowserText($scope) {
    $names = @()
    foreach ($type in @($CT::Document, $CT::Text)) {
        foreach ($e in (Find-AllType $scope $type)) {
            try {
                $tp = $e.GetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern)
                $t = $tp.DocumentRange.GetText(-1)
                if ($t -and $t.Trim()) { return $t }
            } catch { }
            if ($e.Current.Name) { $names += $e.Current.Name }
        }
    }
    return ($names -join "`n")
}
function Get-LabelTexts($scope) {
    return @((Find-AllType $scope $CT::Text | ForEach-Object { $_.Current.Name }) | Where-Object { $_ })
}

$win = Get-AppWindow
if (-not $win) { Write-Output "FAIL: AgentBetta window not found"; exit 1 }

# --- New Task ----------------------------------------------------------------
Select-Nav $win "New Task" | Out-Null
Start-Sleep -Milliseconds 700
$task = Get-View $win "TaskView"
if (-not $task) { $task = $win }
$items = Get-ComboItems $task
Add-Result "task.modelCombo.items" ($items.Count -ge 1 -and $items[0].Count -gt 1) ($items[0] -join " | ")
if ($items.Count -ge 2) { Add-Result "task.permissionCombo.items" ($items[1] -contains "Full Computer") ($items[1] -join " | ") }
if ($items.Count -ge 3) { Add-Result "task.modeCombo.items" (($items[2] -contains "adaptive") -and ($items[2] -contains "fixed")) ($items[2] -join " | ") }
Add-Result "task.localOnlyCheckbox" ($null -ne (Find-ByName $task $CT::CheckBox "Local only")) ""
foreach ($b in @("Choose folder...", "Clear", "Attach files...", "Run", "Stop")) { Add-Result "task.button.$b" ($null -ne (Find-ByName $task $CT::Button $b)) "" }
$details = Find-ByName $task $CT::CheckBox "Run details"; if (-not $details) { $details = Find-ByName $task $CT::Button "Run details" }
Add-Result "task.runDetailsToggle" ($null -ne $details) ""

# --- History -----------------------------------------------------------------
Select-Nav $win "History" | Out-Null
Start-Sleep -Milliseconds 900
$history = Get-View $win "HistoryView"
Add-Result "history.viewVisible" ($null -ne $history) ""
if ($history) {
    foreach ($b in @("Refresh", "Open details", "Rerun", "Copy result", "Open runs folder", "Clear history")) {
        Add-Result "history.button.$b" ($null -ne (Find-ByName $history $CT::Button $b)) ""
    }
    Invoke-Button $history "Refresh" | Out-Null
    Start-Sleep -Milliseconds 700
    $runCount = (Get-LabelTexts $history | Where-Object { $_ -match "run\(s\)" } | Select-Object -First 1)
    Add-Result "history.refresh" ($null -ne $runCount) "$runCount"
}

# --- Settings ----------------------------------------------------------------
Select-Nav $win "Settings" | Out-Null
Start-Sleep -Milliseconds 1200
$settings = Get-View $win "SettingsView"
Add-Result "settings.viewVisible" ($null -ne $settings) ""
if ($settings) {
    $tabs = (Find-AllType $settings $CT::TabItem | ForEach-Object { $_.Current.Name })
    Add-Result "settings.tabs" ($tabs.Count -ge 8) ($tabs -join ",")

    if ($DumpSettings) {
        Write-Output "=== SETTINGS DESCENDANTS ==="
        foreach ($e in $settings.FindAll($TS::Descendants, [System.Windows.Automation.Condition]::TrueCondition)) {
            $ct = $e.Current.ControlType.ProgrammaticName -replace "ControlType.", ""
            Write-Output ("{0} | {1} | {2}" -f $ct, $e.Current.AutomationId, $e.Current.Name)
        }
    }

    Select-Tab $settings "Providers & Models" | Out-Null
    Start-Sleep -Milliseconds 700
    foreach ($b in @("Add", "Edit", "Remove", "Toggle enabled", "Test connection", "Refresh models")) {
        Add-Result "settings.providers.button.$b" ($null -ne (Find-ByName $settings $CT::Button $b)) ""
    }
    Invoke-Button $settings "Test connection" | Out-Null
    Start-Sleep -Seconds 8
    $status = (Get-LabelTexts $settings | Where-Object { $_ -match "OK:|FAILED:|Select a provider|Testing" } | Select-Object -First 1)
    Add-Result "settings.providers.testConnection" ($null -ne $status) "$status"

    Select-Tab $settings "Local Models" | Out-Null
    Start-Sleep -Milliseconds 700
    Invoke-Button $settings "Test Ollama" | Out-Null
    Start-Sleep -Seconds 5
    $ostatus = (Get-LabelTexts $settings | Where-Object { $_ -match "Ollama reachable|FAILED:|Testing" } | Select-Object -First 1)
    Add-Result "settings.local.testOllama" ($null -ne $ostatus) "$ostatus"
    Invoke-Button $settings "Refresh installed models" | Out-Null
    Start-Sleep -Seconds 5
    $ollamaList = $null
    foreach ($lst in (Find-AllType $settings $CT::List)) { $ollamaList = $lst }
    $olCount = if ($ollamaList) { (Find-AllType $ollamaList $CT::ListItem).Count } else { 0 }
    Add-Result "settings.local.refreshOllama" ($olCount -ge 1) "models=$olCount"

    Select-Tab $settings "Model Tiers" | Out-Null
    Start-Sleep -Milliseconds 700
    $tierItems = Get-ComboItems $settings
    $populated = @($tierItems | Where-Object { $_.Count -ge 1 }).Count
    Add-Result "settings.tiers.combos" ($tierItems.Count -ge 3 -and $populated -ge 1) "combos=$($tierItems.Count) populated=$populated"

    Select-Tab $settings "Tools & Permissions" | Out-Null
    Start-Sleep -Milliseconds 700
    $perms = Get-BrowserText $settings
    Add-Result "settings.permissions.content" ($perms -match "Safe") ("chars=$($perms.Length)")

    Select-Tab $settings "Browser & Web" | Out-Null
    Start-Sleep -Milliseconds 700
    Add-Result "settings.browser.clearButton" ($null -ne (Find-ByName $settings $CT::Button "Clear AgentBetta browser data")) ""
    $bc = Get-ComboItems $settings
    Add-Result "settings.browser.engineCombo" ($bc.Count -ge 1) "combos=$($bc.Count)"

    Select-Tab $settings "Privacy & Data" | Out-Null
    Start-Sleep -Milliseconds 700
    foreach ($b in @("Clear run history", "Open runs folder", "Delete all stored API keys")) {
        Add-Result "settings.privacy.button.$b" ($null -ne (Find-ByName $settings $CT::Button $b)) ""
    }

    Select-Tab $settings "Diagnostics" | Out-Null
    Start-Sleep -Milliseconds 700
    Invoke-Button $settings "Refresh" | Out-Null
    Start-Sleep -Milliseconds 900
    $diag = Get-BrowserText $settings
    Add-Result "settings.diagnostics.content" ($diag -match "AgentBetta version") ("chars=$($diag.Length)")
    Add-Result "settings.diagnostics.openLogs" ($null -ne (Find-ByName $settings $CT::Button "Open logs folder")) ""

    Select-Tab $settings "General" | Out-Null
    Start-Sleep -Milliseconds 700
    $gen = Get-ComboItems $settings
    Add-Result "settings.general.controls" ($gen.Count -ge 3) "combos=$($gen.Count)"

    Select-Tab $settings "Memory" | Out-Null
    Start-Sleep -Milliseconds 700
    Add-Result "settings.memory.enableCheckbox" ($null -ne (Find-ByName $settings $CT::CheckBox "Enable global long-term memory")) ""
    foreach ($b in @("Add memory", "Refresh", "Forget selected", "Clear all", "Open memory folder")) {
        Add-Result "settings.memory.button.$b" ($null -ne (Find-ByName $settings $CT::Button $b)) ""
    }
    Invoke-Button $settings "Refresh" | Out-Null
    Start-Sleep -Milliseconds 700
    $memStatus = (Get-LabelTexts $settings | Where-Object { $_ -match "memory entries" } | Select-Object -First 1)
    Add-Result "settings.memory.refresh" ($null -ne $memStatus) "$memStatus"
}

# --- About -------------------------------------------------------------------
Select-Nav $win "About" | Out-Null
Start-Sleep -Milliseconds 900
$about = Get-View $win "AboutView"
$aboutText = if ($about) { Get-BrowserText $about } else { "" }
Add-Result "about.content" ($aboutText -match "AgentBetta") ("chars=$($aboutText.Length)")

# --- report ------------------------------------------------------------------
Write-Output ""
Write-Output "================ GUI UAT RESULTS ================"
$pass = 0; $fail = 0
foreach ($r in $results) {
    if ($r.OK) { $pass++ } else { $fail++ }
    Write-Output ("[{0}] {1}  {2}" -f $(if ($r.OK) { "PASS" } else { "FAIL" }), $r.Check, $r.Detail)
}
Write-Output ("TOTAL: {0} passed, {1} failed" -f $pass, $fail)
$results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot "..\docs\windows\GUI_UAT_RESULTS.json")
exit ([int]($fail -gt 0))
