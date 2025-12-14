function Normalize-Title {
    param([string]$s)
    if (-not $s) { return "" }
    $t = $s.ToLower() -replace '[^a-z0-9]+', ' '
    ($t -replace '\s+', ' ').Trim()
}

function Compact {
    param([string]$s)
    if (-not $s) { return "" }
    ($s -replace '\s+', '')
}

function Normalize-Url {
    param([string]$u)
    if (-not $u) { return "" }
    $u = $u.Trim()
    if ($u.EndsWith('/')) { $u = $u.TrimEnd('/') }
    $u.ToLower()
}

$catelogPath = 'catelog.md'
$csvPath = 'working_runs/Knowledge base - Categories and structure(Document inputs).csv'
$reportPath = 'working_runs/metadata_backfill_and_duplicate_guard_report_20251213.md'
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

$lines = Get-Content -Path $catelogPath -Encoding utf8

# Parse entries from catelog
$entries = @()
$current = [ordered]@{
    Title    = $null
    Filename = $null
    Orig     = $null
    OrgIdx   = $null
    Org      = $null
    PubIdx   = $null
    Pub      = $null
    TypeIdx  = $null
    Type     = $null
    KwIdx    = $null
    Kw       = $null
    Order    = $entries.Count
}

for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    if ($line -match '^####\s+(.*)$') {
        if ($current.Filename) { $entries += $current }
        $current = [ordered]@{
            Title    = $matches[1].Trim()
            Filename = $null
            Orig     = $null
            OrgIdx   = $null
            Org      = $null
            PubIdx   = $null
            Pub      = $null
            TypeIdx  = $null
            Type     = $null
            KwIdx    = $null
            Kw       = $null
            Order    = $entries.Count
        }
    } elseif ($line -match '^- \*\*File\*\*: `Knowledge_Base_MarkDown/([^`]+)`') {
        $current.Filename = $matches[1]
    } elseif ($line -match '^- \*\*Original Source\*\*: (.*)$') {
        $current.Orig = $matches[1].Trim()
    } elseif ($line -match '^- \*\*Organization\*\*: (.*)$') {
        $current.OrgIdx = $i; $current.Org = $matches[1]
    } elseif ($line -match '^- \*\*Publish Date\*\*: (.*)$') {
        $current.PubIdx = $i; $current.Pub = $matches[1]
    } elseif ($line -match '^- \*\*Document Type\*\*: (.*)$') {
        $current.TypeIdx = $i; $current.Type = $matches[1]
    } elseif ($line -match '^- \*\*Keywords\*\*: (.*)$') {
        $current.KwIdx = $i; $current.Kw = $matches[1]
    }
}
if ($current.Filename) { $entries += $current }

# Parse CSV (skip two leading header notes while preserving quoted newlines)
$rawText = Get-Content -Path $csvPath -Raw -Encoding utf8
$rawLines = $rawText -split "`r?`n"
$dataText = ($rawLines[2..($rawLines.Count - 1)] -join "`n")
$csvRows = ConvertFrom-Csv -InputObject $dataText

$urlMap = @{}
$titleMap = @{}
$csvList = @()
foreach ($row in $csvRows) {
    $url = Normalize-Url $row.'Web address'
    if ($url) {
        if ($urlMap.ContainsKey($url)) { $urlMap[$url] = $null } else { $urlMap[$url] = $row }
    }
    $tNorm = Normalize-Title $row.Title
    if ($tNorm) {
        if ($titleMap.ContainsKey($tNorm)) { $titleMap[$tNorm] = $null } else { $titleMap[$tNorm] = $row }
    }
    $csvList += [ordered]@{
        Row          = $row
        TitleNorm    = $tNorm
        TitleCompact = (Compact $tNorm)
    }
}

function Get-MatchRow {
    param($entry, $csvList, $titleMap, $urlMap)

    if ($entry.Orig) {
        $normOrig = Normalize-Url $entry.Orig
        if ($urlMap.ContainsKey($normOrig) -and $urlMap[$normOrig]) { return $urlMap[$normOrig] }
    }

    $tNorm = Normalize-Title $entry.Title
    if ($titleMap.ContainsKey($tNorm) -and $titleMap[$tNorm]) { return $titleMap[$tNorm] }

    $stemNorm = Normalize-Title ([System.IO.Path]::GetFileNameWithoutExtension($entry.Filename))
    $stemCompact = Compact $stemNorm
    $cands = $csvList | Where-Object {
        $_.TitleNorm -and (
            $_.TitleNorm -eq $stemNorm -or
            $_.TitleNorm -like "$stemNorm*" -or
            $stemNorm -like "$($_.TitleNorm)*" -or
            (
                $_.TitleCompact -and
                ($stemCompact -like "*$($_.TitleCompact)*" -or $_.TitleCompact -like "*$stemCompact*")
            )
        )
    }
    if ($cands.Count -eq 1) { return $cands[0].Row }
    return $null
}

$filledCounts = @{ Org = 0; Pub = 0; Type = 0; Kw = 0; Docs = 0 }
$notUpdated = @()

foreach ($e in $entries) {
    $matchRow = Get-MatchRow $e $csvList $titleMap $urlMap
    if (-not $matchRow) {
        $notUpdated += "`Knowledge_Base_MarkDown/$($e.Filename)` — no confident CSV match"
        continue
    }
    $docUpdated = $false
    if ($e.OrgIdx -ne $null -and [string]::IsNullOrWhiteSpace($e.Org)) {
        $orgVal = $matchRow.Organization
        if ($orgVal -and $orgVal.Trim() -ne '') {
            $lines[$e.OrgIdx] = "- **Organization**: $orgVal"
            $filledCounts['Org']++
            $docUpdated = $true
        }
    }
    if ($e.PubIdx -ne $null -and [string]::IsNullOrWhiteSpace($e.Pub)) {
        $pubVal = $matchRow.'Published date'
        if ($pubVal -and $pubVal.Trim() -ne '') {
            $lines[$e.PubIdx] = "- **Publish Date**: $pubVal"
            $filledCounts['Pub']++
            $docUpdated = $true
        }
    }
    if ($e.TypeIdx -ne $null -and [string]::IsNullOrWhiteSpace($e.Type)) {
        $typeVal = $matchRow.Category
        if ($typeVal -and $typeVal.Trim() -ne '') {
            $lines[$e.TypeIdx] = "- **Document Type**: $typeVal"
            $filledCounts['Type']++
            $docUpdated = $true
        }
    }
    if ($e.KwIdx -ne $null -and [string]::IsNullOrWhiteSpace($e.Kw)) {
        $kwVal = $matchRow.'Key words'
        if ($kwVal -and $kwVal.Trim() -ne '') {
            $kwNorm = ($kwVal -replace "`r?`n", '; ')
            $lines[$e.KwIdx] = "- **Keywords**: $kwNorm"
            $filledCounts['Kw']++
            $docUpdated = $true
        }
    }
    if ($docUpdated) { $filledCounts['Docs']++ }
}

[System.IO.File]::WriteAllLines($catelogPath, $lines, $utf8NoBom)

# Duplicate Guard
function Get-NormHash([string]$path) {
    $raw = Get-Content -Path $path -Raw -Encoding utf8
    $norm = ($raw.ToLower() -replace '\s+', ' ').Trim()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($norm)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hash = $sha.ComputeHash($bytes)
    ($hash | ForEach-Object { $_.ToString('x2') }) -join ''
}

$kbFiles = Get-ChildItem -Path 'Knowledge_Base_MarkDown' -Filter '*.md'
$entryMap = @{}
foreach ($e in $entries) { $entryMap[$e.Filename] = $e }

$fileInfos = @()
foreach ($f in $kbFiles) {
    $text = Get-Content -Path $f.FullName -Encoding utf8
    $h1 = ($text | Where-Object { $_.StartsWith('# ') } | Select-Object -First 1)
    $title = if ($h1) { $h1.Substring(2).Trim() } else { $f.BaseName }
    $orig = ''
    if ($entryMap.ContainsKey($f.Name)) { $orig = $entryMap[$f.Name].Orig }
    $fileInfos += [ordered]@{
        Name      = $f.Name
        Path      = $f.FullName
        Title     = $title
        TitleNorm = (Normalize-Title $title)
        Orig      = $orig
        OrigNorm  = (Normalize-Url $orig)
        Hash      = (Get-NormHash $f.FullName)
        Order     = if ($entryMap.ContainsKey($f.Name)) { $entryMap[$f.Name].Order } else { 9999 }
    }
}

$confirmed = @()
$potential = @()
$urlGroups = $fileInfos | Where-Object { $_.OrigNorm } | Group-Object OrigNorm
foreach ($g in $urlGroups) {
    if ($g.Count -lt 2) { continue }
    $hashSet = $g.Group | Group-Object Hash
    $titleSet = $g.Group | Group-Object TitleNorm
    $sameHash = ($hashSet.Count -eq 1)
    $sameTitle = ($titleSet.Count -eq 1)
    $evidence = @('URL match')
    if ($sameTitle) { $evidence += 'same title' }
    if ($sameHash) { $evidence += 'same content hash' }
    $canon = $g.Group | Sort-Object Order | Select-Object -First 1
    $rec = "Canonical: $($canon.Name) (catelog order)"
    $groupLine = "Files: " + ($g.Group.Name -join ', ') + " | Evidence: " + ($evidence -join '; ') + " | Recommendation: $rec"
    if ($sameHash -or $sameTitle) { $confirmed += $groupLine } else { $potential += $groupLine }
}

$titleGroups = $fileInfos | Group-Object TitleNorm
foreach ($g in $titleGroups) {
    if ($g.Count -lt 2) { continue }
    $names = $g.Group.Name
    $existing = $confirmed + $potential
    $already = $false
    foreach ($line in $existing) {
        foreach ($n in $names) { if ($line -like "*$n*") { $already = $true; break } }
        if ($already) { break }
    }
    if ($already) { continue }
    $hashSet = $g.Group | Group-Object Hash
    $evidence = @('title match')
    if ($hashSet.Count -eq 1) { $evidence += 'same content hash' }
    $canon = $g.Group | Sort-Object Order | Select-Object -First 1
    $rec = "Canonical: $($canon.Name) (catelog order)"
    $line = "Files: " + ($names -join ', ') + " | Evidence: " + ($evidence -join '; ') + " | Recommendation: $rec"
    if ($hashSet.Count -eq 1) { $confirmed += $line } else { $potential += $line }
}

$linesAfter = Get-Content -Path $catelogPath -Encoding utf8
$remainingOrg = ($linesAfter | Where-Object { $_ -match '^- \*\*Organization\*\*: \s*$' }).Count
$remainingPub = ($linesAfter | Where-Object { $_ -match '^- \*\*Publish Date\*\*: \s*$' }).Count
$remainingType = ($linesAfter | Where-Object { $_ -match '^- \*\*Document Type\*\*: \s*$' }).Count
$remainingKw = ($linesAfter | Where-Object { $_ -match '^- \*\*Keywords\*\*: \s*$' }).Count

$report = @(
    '# Metadata Backfill and Duplicate Guard',
    '',
    "Generated: $(Get-Date -Format s)",
    '',
    '## Metadata Backfill Summary',
    "- Documents updated: $($filledCounts['Docs'])",
    "- Organization fields filled: $($filledCounts['Org'])",
    "- Publish Date fields filled: $($filledCounts['Pub'])",
    "- Document Type fields filled: $($filledCounts['Type'])",
    "- Keywords fields filled: $($filledCounts['Kw'])",
    '',
    '### Documents not updated (no confident CSV match)'
)
if ($notUpdated.Count -eq 0) { $report += '- None' } else { $report += ($notUpdated | Sort-Object) }
$report += @(
    '',
    '### Remaining blank fields after backfill',
    "- Organization blank: $remainingOrg",
    "- Publish Date blank: $remainingPub",
    "- Document Type blank: $remainingType",
    "- Keywords blank: $remainingKw",
    '',
    '## Duplicate Guard',
    '### Confirmed duplicates'
)
if ($confirmed.Count -eq 0) { $report += '- None' } else { $report += ($confirmed | Sort-Object) }
$report += '### Potential duplicates'
if ($potential.Count -eq 0) { $report += '- None' } else { $report += ($potential | Sort-Object) }

[System.IO.File]::WriteAllLines($reportPath, $report, $utf8NoBom)
Write-Host 'Script finished.'
