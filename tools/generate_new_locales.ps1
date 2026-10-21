param([string[]]$LanguagesToBuild, [switch]$FillMissingOnly)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$source = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'locales\en.json') | ConvertFrom-Json -AsHashtable
if ($source.help.schema -ge 2 -and -not $FillMissingOnly) {
    throw 'Complete Help is protected. Use tools/translate_help.py for Help-only updates; use -FillMissingOnly to fill UI keys without replacing Help.'
}
$languages = [ordered]@{
    'zh-CN' = '简体中文'
    nl = 'Nederlands'
    fr = 'Français'
    de = 'Deutsch'
    ja = '日本語'
    ko = '한국어'
    ru = 'Русский'
    es = 'Español'
    sv = 'Svenska'
    bg = 'Български'
    th = 'ไทย'
    id = 'Bahasa Indonesia'
    el = 'Ελληνικά'
    fil = 'Filipino'
    hi = 'हिन्दी'
    pl = 'Polski'
    it = 'Italiano'
    ar = 'العربية'
    vi = 'Tiếng Việt'
    uk = 'Українська'
    no = 'Norsk'
    fi = 'Suomi'
    da = 'Dansk'
    hu = 'Magyar'
    ro = 'Română'
    cs = 'Čeština'
    'pt-PT' = 'Português (Portugal)'
    'pt-BR' = 'Português (Brasil)'
    tr = 'Türkçe'
    'zh-TW' = '繁體中文'
    ms = 'Bahasa Melayu'
    he = 'עברית'
    bn = 'বাংলা'
    ur = 'اردو'
    fa = 'فارسی'
    sk = 'Slovenčina'
    hr = 'Hrvatski'
    sr = 'Српски'
    ca = 'Català'
    et = 'Eesti'
    lv = 'Latviešu'
    lt = 'Lietuvių'
}
$maxChars = 180

function New-TranslationSession {
    $session = [Microsoft.PowerShell.Commands.WebRequestSession]::new()
    $html = (Invoke-WebRequest -Uri 'https://www.bing.com/translator' -WebSession $session).Content
    $abuse = [regex]::Match($html, 'params_AbusePreventionHelper = \[(\d+),"([^"]+)"')
    $ig = [regex]::Match($html, 'IG:"([A-F0-9]+)"')
    $iid = [regex]::Match($html, 'data-iid="([^"]+)"')
    if (-not ($abuse.Success -and $ig.Success -and $iid.Success)) {
        throw 'Could not initialise the translation session.'
    }
    return [pscustomobject]@{
        Session = $session
        Key = $abuse.Groups[1].Value
        Token = $abuse.Groups[2].Value
        Uri = "https://www.bing.com/ttranslatev3?isVertical=1&IG=$($ig.Groups[1].Value)&IID=$([uri]::EscapeDataString($iid.Groups[1].Value))"
    }
}

function Invoke-Translation {
    param($Context, [string]$Text, [string]$Language)
    $serviceLanguage = if ($Language -eq 'no') { 'nb' } elseif ($Language -eq 'pt-BR') { 'pt' } elseif ($Language -eq 'sr') { 'sr-Cyrl' } elseif ($Language -eq 'zh-TW') { 'zh-Hant' } elseif ($Language -eq 'zh-CN') { 'zh-Hans' } else { $Language }
    $body = @{
        fromLang = 'en'
        text = $Text
        to = $serviceLanguage
        token = $Context.Token
        key = $Context.Key
        textType = 'html'
    }
    $result = Invoke-RestMethod -Method Post -Uri $Context.Uri -WebSession $Context.Session -Body $body
    $entry = if ($result.translations) { $result } else { $result[0] }
    if (-not $entry.translations) { throw "Translation service returned no result for $Language`: $($result | ConvertTo-Json -Depth 8 -Compress)" }
    return [string]$entry.translations[0].text
}

function Convert-Values {
    param($Context, [string[]]$Values, [string]$Language)
    $output = [string[]]::new($Values.Count)
    $groups = [System.Collections.Generic.List[object]]::new()
    $current = [System.Collections.Generic.List[object]]::new()
    $size = 0
    for ($index = 0; $index -lt $Values.Count; $index++) {
        $extra = $Values[$index].Length + 32
        if ($current.Count -gt 0 -and ($size + $extra) -gt $maxChars) {
            $groups.Add($current.ToArray())
            $current = [System.Collections.Generic.List[object]]::new()
            $size = 0
        }
        $current.Add([pscustomobject]@{ Index = $index; Value = $Values[$index] })
        $size += $extra
    }
    if ($current.Count -gt 0) { $groups.Add($current.ToArray()) }

    foreach ($group in $groups) {
        $parts = [System.Collections.Generic.List[string]]::new()
        for ($offset = 0; $offset -lt $group.Count; $offset++) {
            if ($offset -gt 0) { $parts.Add(('RFMSEP{0:D4}' -f $group[$offset].Index)) }
            $parts.Add([System.Net.WebUtility]::HtmlEncode($group[$offset].Value))
        }
        $response = Invoke-Translation -Context $Context -Text ($parts -join "`n") -Language $Language
        $markers = @($group | Select-Object -Skip 1 | ForEach-Object { 'RFMSEP{0:D4}' -f $_.Index })
        [string[]]$split = if ($markers.Count) { [regex]::Split($response, ($markers -join '|')) } else { @($response) }
        if ($split.Count -ne $group.Count) { throw "Translation separator mismatch for $Language`: $response" }
        for ($offset = 0; $offset -lt $group.Count; $offset++) {
            $output[$group[$offset].Index] = [System.Net.WebUtility]::HtmlDecode($split[$offset].Trim())
        }
        Start-Sleep -Milliseconds 150
    }
    return $output
}

$context = New-TranslationSession
$selectedLanguages = if ($LanguagesToBuild) { @($LanguagesToBuild) } else { @($languages.Keys) }
foreach ($language in $selectedLanguages) {
    if (-not $languages.Contains($language)) { throw "Unsupported target language: $language" }
    Write-Host "Translating $language..."
    $path = Join-Path $projectRoot "locales\$language.json"
    $existing = if ($FillMissingOnly -and (Test-Path -LiteralPath $path)) {
        Get-Content -Raw -LiteralPath $path | ConvertFrom-Json -AsHashtable
    } else { $null }
    $stringKeys = @($source.strings.Keys | Where-Object { -not $existing -or -not $existing.strings.ContainsKey($_) })
    $literalKeys = @($source.literals.Keys | Where-Object { -not $existing -or -not $existing.literals.ContainsKey($_) })
    $stringValues = @($stringKeys | ForEach-Object { [string]$source.strings[$_] })
    $literalValues = @($literalKeys | ForEach-Object { [string]$source.literals[$_] })
    $keepExistingHelp = $existing -and $existing.help -and ($source.help.schema -ge 2 -or $existing.help.chapters.Count -eq $source.help.chapters.Count)
    $helpValues = if ($keepExistingHelp) { @() } else { @($source.help.chapters | ForEach-Object { [string]$_.title; [string]$_.body }) }
    $translatedStrings = Convert-Values $context $stringValues $language
    $translatedLiterals = Convert-Values $context $literalValues $language
    $translatedHelp = Convert-Values $context $helpValues $language

    $strings = [ordered]@{}
    if ($existing) { foreach ($key in $existing.strings.Keys) { $strings[$key] = $existing.strings[$key] } }
    for ($i = 0; $i -lt $stringKeys.Count; $i++) { $strings[$stringKeys[$i]] = $translatedStrings[$i] }
    $literals = [ordered]@{}
    if ($existing) { foreach ($key in $existing.literals.Keys) { $literals[$key] = $existing.literals[$key] } }
    for ($i = 0; $i -lt $literalKeys.Count; $i++) { $literals[$literalKeys[$i]] = $translatedLiterals[$i] }
    $chapters = if ($keepExistingHelp) { $existing.help.chapters } else {
        $translatedChapters = [System.Collections.Generic.List[object]]::new()
        for ($i = 0; $i -lt $source.help.chapters.Count; $i++) {
            $translatedChapters.Add([ordered]@{
                id = $source.help.chapters[$i].id
                title = $translatedHelp[$i * 2]
                body = $translatedHelp[$i * 2 + 1]
            })
        }
        $translatedChapters
    }
    $pack = [ordered]@{
        meta = [ordered]@{ language = $languages[$language] }
        strings = $strings
        help = [ordered]@{ chapters = $chapters }
        literals = $literals
    }
    $json = $pack | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText($path, $json + "`n", [Text.UTF8Encoding]::new($false))
    Write-Host "Wrote $path"
}
