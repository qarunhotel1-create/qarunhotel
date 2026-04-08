Local Scan Agent (example)

Purpose:
This is a minimal example of a local scan-agent that the web UI can call to perform "direct" scanning from a physical scanner.

Important note:
- Browsers cannot access local scanner drivers directly. This agent is a local service you run on the user's PC which interfaces with the scanner driver (TWAIN/WIA) or vendor SDK. For demo purposes this script returns simulated scanned images.

Files:
- `scan_agent.py`: Flask app exposing POST /scan
- `requirements.txt`: Python dependencies (Flask, Pillow)

Run (Windows PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r scan_agent\requirements.txt; python scan_agent\scan_agent.py
```

API:
POST http://localhost:5005/scan
Body (application/json): { "mode": "multi"|"single", "device": "Kyocera FS-3540MFP KX" }
Response: { "images": ["data:image/jpeg;base64,..."] }

Next steps to integrate with real scanner:
- Replace simulated image generation with calls to a TWAIN/WIA library or vendor SDK.
- If using TWAIN on Windows, consider the 'twain' or 'pytwain' wrappers or a small native helper.
- Ensure the agent runs with permissions to access the scanner and enable CORS for your web UI's origin.

FTP receive mode (Scan-to-FTP from Kyocera)

You can configure your Kyocera MFP to upload scanned files to this agent using FTP. The agent exposes an endpoint that starts a temporary FTP server and waits for uploads.

1) Start the agent (see above).
2) Configure Kyocera Scan-to-FTP with:
   - Host: the IP address of the PC running the agent
   - Port: 2121 (or the port you pass to /scan_ftp)
   - Username: scan
   - Password: scan
   - Remote Directory: / (or leave blank)
   - File Format: JPEG
3) Trigger scanning on the device. Then call the agent endpoint to collect the files:

POST http://localhost:5005/scan_ftp

Body (application/json) optional:
{ "timeout": 30, "username": "scan", "password": "scan", "port": 2121 }

The endpoint will return JSON with the uploaded images as data URLs.

Security note: FTP is unencrypted. For production consider using SFTP or a secure upload endpoint.
