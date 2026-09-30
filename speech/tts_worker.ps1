param([string]$text, [string]$outFile)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.Rate = 1
$s.SetOutputToWaveFile($outFile)
$s.Speak($text)
$s.Dispose()
