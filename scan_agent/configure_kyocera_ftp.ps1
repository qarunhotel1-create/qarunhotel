<#
PowerShell helper: configure Kyocera FS-3540MFP KX to send scans to local agent (Scan-to-FTP)

Usage (run as Administrator):
.
cd 'E:\1\QARUN HOTEL\scan_agent'
.\configure_kyocera_ftp.ps1

The script will:
- Ensure the local scan agent is running (calls install_and_run_agent.ps1)
- Try to auto-login to the printer web UI (best-effort) and POST FTP settings
- If automation fails, it opens the printer admin page in the default browser and prints manual steps

Notes:
- Auto-configuration depends on the printer web UI structure; many Kyocera models vary. This script uses best-effort heuristics.
- You will need the printer's admin username/password.
- After successful configuration, pressing the web app's "ماسح ضوئي" button should trigger the scan via FTP.
#>

param()

function Write-Ok($msg){ Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warn($msg){ Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg){ Write-Host "[ERR] $msg" -ForegroundColor Red }

# Prompt user for printer info
$printerIP = Read-Host 'أدخل عنوان IP الخاص بالطابعة (مثال: 192.168.1.50)'
if (-not $printerIP) { Write-Err 'لم تُدخل IP. إلغاء.'; exit 1 }
$adminUser = Read-Host 'أدخل اسم مستخدم مسؤول الطابعة (عادة admin)'
$adminPass = Read-Host 'أدخل كلمة مرور المسؤول للطابعة' -AsSecureString
$adminPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminPass))

# Start local agent (install_and_run_agent.ps1) if not running
$healthUrl = 'http://localhost:5005/health'
function Ensure-AgentRunning {
    try {
        $ok = Invoke-RestMethod -Uri $healthUrl -Method GET -TimeoutSec 3 -ErrorAction Stop
        if ($ok.status -eq 'ok') { Write-Ok 'الوكيل المحلي يعمل.'; return $true }
    } catch {
        Write-Warn 'الوكيل المحلي غير متاح. سأحاول تشغيله الآن...'
        $install = Join-Path (Get-Location) 'install_and_run_agent.ps1'
        if (Test-Path $install) {
            Start-Process powershell -ArgumentList "-NoExit -Command `. .\\.venv\\Scripts\\Activate.ps1; & '$install'" -WindowStyle Normal
            Start-Sleep -Seconds 5
            # retry health
            try { Start-Sleep -Seconds 3; $ok = Invoke-RestMethod -Uri $healthUrl -Method GET -TimeoutSec 5 -ErrorAction Stop; if ($ok.status -eq 'ok') { Write-Ok 'الوكيل بدأ ويعمل.'; return $true } } catch {}
            Write-Warn 'تعذر بدء الوكيل تلقائياً؛ تأكد من تشغيل install_and_run_agent.ps1 يدوياً.'
            return $false
        } else {
            Write-Err 'ملف install_and_run_agent.ps1 غير موجود. شغّل التثبيت يدوياً.'; return $false
        }
    }
}

$agentReady = Ensure-AgentRunning
if (-not $agentReady) { Write-Err 'الوكيل غير جاهز، لا يمكن المتابعة.'; exit 1 }

# Attempt auto-configuration
$adminUrl = "http://$printerIP/"
Write-Host "محاولة الوصول إلى واجهة الطابعة: $adminUrl"
try {
    $resp = Invoke-WebRequest -Uri $adminUrl -UseBasicParsing -ErrorAction Stop -TimeoutSec 8 -SessionVariable sess
    Write-Ok 'تم الوصول إلى صفحة الإدارة.'
} catch {
    Write-Warn "تعذر الوصول إلى واجهة الويب على $adminUrl. افتح الواجهة يدوياً وتأكد من الاتصال بالشبكة والطابعة."
    Start-Process "http://$printerIP/"
    exit 1
}

# Heuristic: find login form and try to submit credentials
$loggedIn = $false
if ($resp.Forms.Count -gt 0) {
    foreach ($form in $resp.Forms) {
        # duplicate fields to a mutable hashtable
        $fields = @{}
        foreach ($k in $form.Fields.Keys) { $fields[$k] = $form.Fields[$k] }
        # try common username/password field names
        if ($fields.ContainsKey('username')) { $fields['username'] = $adminUser }
        if ($fields.ContainsKey('userid')) { $fields['userid'] = $adminUser }
        if ($fields.ContainsKey('user')) { $fields['user'] = $adminUser }
        if ($fields.ContainsKey('password')) { $fields['password'] = $adminPassPlain }
        if ($fields.ContainsKey('passwd')) { $fields['passwd'] = $adminPassPlain }
        if ($fields.ContainsKey('passwd1')) { $fields['passwd1'] = $adminPassPlain }

        try {
            $action = $form.Action
            if (-not $action) { $action = $adminUrl }
            if ($action -notlike 'http*') { $action = [Uri]::new($adminUrl, $action).AbsoluteUri }
            $loginResp = Invoke-WebRequest -Uri $action -Method POST -Body $fields -WebSession $sess -UseBasicParsing -ErrorAction Stop
            # naive check for login success: response doesn't contain password input
            if ($loginResp.Content -notmatch 'password' -and $loginResp.StatusCode -eq 200) {
                Write-Ok 'تم تسجيل الدخول تلقائياً إلى واجهة الطابعة (منهج تخميني).'
                $loggedIn = $true; break
            }
        } catch {
            # ignore and continue
        }
    }
} else {
    Write-Warn 'لا توجد نماذج HTML في الصفحة؛ قد يكون الطابعة تستخدم إطار عمل JS متقدم. سنحاول فتح الواجهة يدويًا.'
}

if (-not $loggedIn) {
    Write-Warn 'فشل تسجيل الدخول التلقائي. سأفتح واجهة الإدارة في المتصفح مع تعليمات يدوية.'
    Start-Process "http://$printerIP/"
    Write-Host "
تعليمات يدوية سريعة لإعداد Scan-to-FTP على Kyocera FS-3540MFP KX:
1) افتح واجهة الويب: http://$printerIP/
2) سجل الدخول كمسؤول (اسم المستخدم: $adminUser)
3) ابحث عن: "Scan" -> "Scan to FTP" أو "Address Book" -> Add FTP Target
4) أنشئ هدف FTP جديد:
   - Host: PUT_IP_OF_COMPUTER (مثال: 192.168.1.100)
   - Port: 2121
   - Username: scan
   - Password: scan
   - Remote directory: /
   - File format: JPEG
5) من الطابعة، نفّذ اختبار المسح إلى FTP. ثم عد إلى التطبيق واضغط "ماسح ضوئي".
"
    exit 0
}

# If logged in, try to find FTP-setting forms on the returned page(s)
Write-Host 'محاولة إيجاد نموذج إعداد FTP على الصفحة الحالية (محاولة تلقائية)...'
try {
    $pages = @($loginResp, $resp) | Where-Object { $_ -ne $null }
    $configured = $false
    foreach ($p in $pages) {
        if ($p.Forms.Count -gt 0) {
            foreach ($f in $p.Forms) {
                # check if this form mentions ftp or scan
                $content = $f.InnerHtml + ' ' + ($p.Content -as [string])
                if ($content -match 'ftp' -or $content -match 'Scan') {
                    # fill common fields
                    $fields = @{}
                    foreach ($k in $f.Fields.Keys) { $fields[$k] = $f.Fields[$k] }
                    foreach ($key in $fields.Keys) {
                        if ($key -match 'host|server') { $fields[$key] = $printerIP } # may be ignored
                        if ($key -match 'port') { $fields[$key] = '2121' }
                        if ($key -match 'user|userid|username') { $fields[$key] = 'scan' }
                        if ($key -match 'pass|passwd') { $fields[$key] = 'scan' }
                    }
                    try {
                        $action = $f.Action; if (-not $action) { $action = $adminUrl }
                        if ($action -notlike 'http*') { $action = [Uri]::new($adminUrl, $action).AbsoluteUri }
                        $setResp = Invoke-WebRequest -Uri $action -Method POST -Body $fields -WebSession $sess -UseBasicParsing -ErrorAction Stop
                        if ($setResp.StatusCode -eq 200) { Write-Ok 'تم إرسال إعدادات FTP (قد تحتاج لمراجع الطابعة للتأكد)'; $configured = $true; break }
                    } catch {
                        # ignore
                    }
                }
            }
        }
        if ($configured) { break }
    }
    if (-not $configured) {
        Write-Warn 'لم نتمكن من اكتشاف نموذج إعداد FTP تلقائياً. سنفتح واجهة الإدارة لتكمل الإعداد يدوياً.'
        Start-Process "http://$printerIP/"
        exit 0
    } else {
        Write-Ok 'حاولت إعداد الطابعة لإرسال FTP إلى الوكيل. الآن جرب عملية المسح من الطابعة ثم اضغط زر "ماسح ضوئي" في الويب.'
        exit 0
    }
} catch {
    Write-Warn 'حدث خطأ أثناء محاولة إعداد FTP تلقائياً.'
    Start-Process "http://$printerIP/"
    exit 1
}
