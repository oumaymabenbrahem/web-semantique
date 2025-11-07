# Script pour charger automatiquement l'ontologie dans Fuseki

$rdfFile = "$PWD\ws.rdf"
$fusekiEndpoint = "http://localhost:3030/tourisme/data"

Write-Host "Chargement de l'ontologie dans Fuseki..." -ForegroundColor Green

if (-not (Test-Path $rdfFile)) {
    Write-Host "ERREUR: Fichier ws.rdf introuvable!" -ForegroundColor Red
    exit 1
}

Write-Host "Fichier: $rdfFile" -ForegroundColor Cyan
Write-Host "Endpoint: $fusekiEndpoint" -ForegroundColor Cyan
Write-Host ""

try {
    # Verifier que Fuseki est demarre
    Write-Host "Verification que Fuseki est actif..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "http://localhost:3030" -Method GET -UseBasicParsing
    Write-Host "SUCCES: Fuseki est actif!" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Fuseki n'est pas demarre!" -ForegroundColor Red
    Write-Host "Executez d'abord: .\start-fuseki.ps1" -ForegroundColor Yellow
    exit 1
}

# Charger le fichier RDF
Write-Host "Upload du fichier RDF..." -ForegroundColor Yellow

try {
    $headers = @{
        "Content-Type" = "application/rdf+xml"
    }
    
    $rdfContent = Get-Content -Path $rdfFile -Raw
    
    Invoke-RestMethod -Uri $fusekiEndpoint `
                      -Method POST `
                      -Headers $headers `
                      -Body $rdfContent
    
    Write-Host ""
    Write-Host "SUCCES: Ontologie chargee avec succes dans Fuseki!" -ForegroundColor Green
    Write-Host "Interface web: http://localhost:3030" -ForegroundColor Cyan
    Write-Host "Dataset: /tourisme" -ForegroundColor Cyan
    Write-Host "Vous pouvez maintenant executer des requetes SPARQL" -ForegroundColor Yellow
} catch {
    Write-Host "ERREUR lors du chargement: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solution alternative:" -ForegroundColor Yellow
    Write-Host "1. Ouvrez http://localhost:3030" -ForegroundColor White
    Write-Host "2. Cliquez sur manage datasets" -ForegroundColor White
    Write-Host "3. Selectionnez le dataset tourisme" -ForegroundColor White
    Write-Host "4. Cliquez sur upload files" -ForegroundColor White
    Write-Host "5. Uploadez le fichier ws.rdf" -ForegroundColor White
}
