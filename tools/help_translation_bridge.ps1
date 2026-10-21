param([string]$Language)
$ErrorActionPreference='Stop'
# Reuse the working PowerShell HTTP session implementation. No credentials are
# exported, persisted or printed. stdin/stdout carry only Help text and results.
$scriptText=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'generate_new_locales.ps1')
$tokens=$null; $parseErrors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseInput($scriptText,[ref]$tokens,[ref]$parseErrors)
foreach($name in @('New-TranslationSession','Invoke-Translation')) {
    $node=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true)
    Invoke-Expression $node.Extent.Text
}
$context=New-TranslationSession
while($null -ne ($line=[Console]::ReadLine())) {
    try {
        $request=$line | ConvertFrom-Json
        $result=Invoke-Translation -Context $context -Text ([string]$request.text) -Language $Language
        [Console]::WriteLine((@{text=[System.Net.WebUtility]::HtmlDecode($result)} | ConvertTo-Json -Compress))
        Start-Sleep -Milliseconds 200
    } catch {
        [Console]::WriteLine((@{error='Translation service failed; completed paragraphs remain cached.'} | ConvertTo-Json -Compress))
    }
}
