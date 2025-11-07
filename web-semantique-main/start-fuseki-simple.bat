@echo off
echo ========================================
echo Demarrage de Fuseki sur port 3030
echo Dataset: /tourisme
echo ========================================
echo.

cd fuseki\apache-jena-fuseki-5.6.0
fuseki-server.bat --mem /tourisme

pause
