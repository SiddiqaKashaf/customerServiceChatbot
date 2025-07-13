# TechCorp Solutions RAG Chatbot Server Startup Script
Write-Host "Starting TechCorp Solutions RAG Chatbot Server..." -ForegroundColor Green
Write-Host ""

# Set environment variables
$env:FLASK_SECRET_KEY = "your-secret-key-here-12345"
$env:FLASK_DEBUG = "False"

# Start the production server
Write-Host "Server will be available at:" -ForegroundColor Yellow
Write-Host "  - http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "  - http://localhost:5000" -ForegroundColor Cyan
Write-Host "  - http://[your-ip]:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host ""

python run_production.py 