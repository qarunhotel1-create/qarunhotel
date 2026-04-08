# Run the scan agent in a virtualenv and print logs
$venv = ".\.venv"
if (-Not (Test-Path $venv)) {
    python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1
pip install -r .\scan_agent\requirements.txt
python .\scan_agent\scan_agent.py
