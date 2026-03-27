from flask import Flask, request, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import datetime
import sys
import threading
import tempfile
import time
import os
import pathlib
import logging
from logging.handlers import RotatingFileHandler
import traceback
import socket

# تكوين التسجيل المتقدم
LOG_PATH = pathlib.Path(__file__).parent / 'scan_agent.log'
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

# إنشاء مسجل دوار للملفات (يحتفظ بـ 5 ملفات بحجم 5 ميجابايت لكل منها)
file_handler = RotatingFileHandler(LOG_PATH, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_formatter)

# إنشاء مسجل للطرفية
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# تكوين المسجل الرئيسي
logger = logging.getLogger('scan_agent')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def write_log(msg, level='INFO'):
    """وظيفة مساعدة للتسجيل متوافقة مع الإصدارات السابقة"""
    try:
        if level == 'ERROR':
            logger.error(msg)
        elif level == 'WARNING':
            logger.warning(msg)
        else:
            logger.info(msg)
    except Exception:
        print(f'Failed to write to log: {msg}')

# التحقق من توفر مكتبة FTP
try:
    from pyftpdlib.servers import FTPServer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.authorizers import DummyAuthorizer
    HAS_FTP = True
    write_log("FTP support is available")
except Exception as e:
    HAS_FTP = False
    write_log(f"FTP support is not available: {str(e)}", 'WARNING')

# التحقق من توفر مكتبة WIA للمسح الضوئي
HAS_WIA = False
if sys.platform == 'win32':
    try:
        import win32com.client
        HAS_WIA = True
        write_log("WIA support is available")
    except Exception as e:
        write_log(f"WIA support is not available: {str(e)}", 'WARNING')
else:
    write_log(f"WIA support is not available on this platform: {sys.platform}", 'WARNING')

# إنشاء تطبيق Flask
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# التحقق من حالة الشبكة
def check_network():
    try:
        # التحقق من توفر الشبكة المحلية
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        write_log(f"Network is available. Local IP: {local_ip}")
        return True, local_ip
    except Exception as e:
        write_log(f"Network check failed: {str(e)}", 'WARNING')
        return False, "127.0.0.1"


def simulate_pages(count, device_name='Local Agent', error_message=None):
    pages = []
    for i in range(count):
        # إنشاء صورة بحجم A4 بدقة 300 نقطة في البوصة
        img = Image.new('RGB', (2480, 3508), color='white')
        d = ImageDraw.Draw(img)
        
        # إضافة شعار وهمي للماسح الضوئي
        header_color = (0, 82, 156)  # لون أزرق داكن
        d.rectangle([(0, 0), (2480, 200)], fill=header_color)
        
        # إضافة عنوان
        try:
            # محاولة تحميل خط أكبر للعنوان
            title_font = ImageFont.load_default()
            normal_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        except Exception:
            title_font = None
            normal_font = None
            small_font = None
        
        # إضافة عنوان في الهيدر
        title_text = "Kyocera FS-3540MFP KX - وكيل المسح الضوئي"
        d.text((50, 50), title_text, fill=(255, 255, 255), font=title_font)
        
        # إضافة معلومات المسح
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        # إضافة معلومات في الصفحة
        d.text((50, 250), f"تاريخ المسح: {date_str}", fill=(0, 0, 0), font=normal_font)
        d.text((50, 300), f"وقت المسح: {time_str}", fill=(0, 0, 0), font=normal_font)
        d.text((50, 350), f"اسم الجهاز: {device_name}", fill=(0, 0, 0), font=normal_font)
        d.text((50, 400), f"رقم الصفحة: {i+1} من {count}", fill=(0, 0, 0), font=normal_font)
        
        # إضافة رسالة خطأ إذا كانت موجودة
        if error_message:
            # إضافة مربع تحذير
            warning_top = 500
            warning_height = 300
            d.rectangle([(50, warning_top), (2430, warning_top + warning_height)], fill=(255, 240, 240), outline=(255, 0, 0))
            
            # إضافة رسالة الخطأ
            d.text((100, warning_top + 50), "تنبيه: هذه صورة محاكاة", fill=(255, 0, 0), font=normal_font)
            
            # تقسيم رسالة الخطأ إلى أسطر
            lines = error_message.split('\n')
            for idx, line in enumerate(lines):
                d.text((100, warning_top + 100 + idx * 40), line, fill=(0, 0, 0), font=normal_font)
        
        # إضافة تذييل
        footer_top = 3300
        d.line([(50, footer_top), (2430, footer_top)], fill=(200, 200, 200), width=2)
        d.text((50, footer_top + 50), f"تم إنشاء هذه الصورة بواسطة وكيل المسح الضوئي - {now.isoformat()}", fill=(100, 100, 100), font=small_font)

        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=80)
        b64 = base64.b64encode(buffered.getvalue()).decode('ascii')
        data_url = f"data:image/jpeg;base64,{b64}"
        pages.append(data_url)
    return pages


def start_ftp_receiver(timeout=30, username='scan', password='scan', port=2121):
    if not HAS_FTP:
        raise RuntimeError('pyftpdlib not installed')

    tempdir = tempfile.mkdtemp(prefix='scan_agent_')

    authorizer = DummyAuthorizer()
    authorizer.add_user(username, password, tempdir, perm='elradfmw')

    handler = FTPHandler
    handler.authorizer = authorizer

    server = FTPServer(('0.0.0.0', port), handler)

    # run server in background thread
    thread = threading.Thread(target=server.serve_forever, kwargs={'timeout':1})
    thread.daemon = True
    thread.start()

    # wait for files to appear
    start = time.time()
    uploaded_files = []
    try:
        write_log(f"FTP receiver started on port {port}, waiting for uploads to {tempdir} (timeout {timeout}s)")
        print(f"FTP receiver started on port {port}, waiting for uploads to {tempdir} (timeout {timeout}s)")
        while time.time() - start < timeout:
            files = [os.path.join(tempdir, f) for f in os.listdir(tempdir)]
            if files:
                uploaded_files = files
                write_log(f'Files received via FTP: {uploaded_files}')
                print('Files received via FTP:', uploaded_files)
                break
            time.sleep(0.5)
        if not uploaded_files:
            write_log('No files uploaded via FTP within timeout')
            print('No files uploaded via FTP within timeout')
    finally:
        try:
            server.close_all()
        except Exception:
            pass

    # read uploaded files as data URLs
    images = []
    for fpath in uploaded_files:
        try:
            with open(fpath, 'rb') as fh:
                b64 = base64.b64encode(fh.read()).decode('ascii')
                images.append(f"data:image/jpeg;base64,{b64}")
        except Exception:
            continue

    return images




def try_wia_scan(count=1, preferred_device_name: str | None = None):
    # Attempt WIA scan on Windows using pywin32 without UI if possible
    try:
        import win32com.client
    except Exception:
        raise RuntimeError('pywin32 not available')

    try:
        wia_mgr = win32com.client.Dispatch('WIA.DeviceManager')
        device = None
        # Try to auto-pick device by name
        if preferred_device_name:
            for d in wia_mgr.DeviceInfos:
                name = ''
                try:
                    name = d.Properties('Name').Value
                except Exception:
                    pass
                if name and preferred_device_name.lower() in str(name).lower():
                    device = d.Connect()
                    break
        # Fallback: first available device
        if device is None:
            if wia_mgr.DeviceInfos.Count == 0:
                raise RuntimeError('No WIA devices found')
            device = wia_mgr.DeviceInfos(1).Connect()

        # Set common image acquisition settings
        # 6146 = FormatID (JPEG), 6147 = Intent, 6149 = Horizontal Resolution, 6150 = Vertical Resolution
        try:
            fmtJPEG = '{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}'
            # Some devices accept these item properties via the first item
            items = device.Items
            if items and items.Count >= 1:
                item = items(1)
                try:
                    item.Properties('6146').Value = fmtJPEG
                except Exception:
                    pass
        except Exception:
            pass

        images = []
        dlg = win32com.client.Dispatch('WIA.CommonDialog')
        for i in range(count):
            # Use ShowTransfer with device item to avoid selection UI
            try:
                item = device.Items(1)
                image = dlg.ShowTransfer(item, '{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}')
            except Exception:
                # Fallback to traditional acquire (may show UI depending on driver)
                image = dlg.ShowAcquireImage()
            ip = image.ImageFile
            temp_stream = io.BytesIO()
            ip.SaveFile(temp_stream)
            b64 = base64.b64encode(temp_stream.getvalue()).decode('ascii')
            images.append(f"data:image/jpeg;base64,{b64}")
        return images
    except Exception as e:
        raise RuntimeError('WIA scan failed: ' + str(e))


@app.route('/scan', methods=['POST'])
def scan():
    try:
        payload = request.get_json() or {}
        mode = payload.get('mode', 'multi')
        device = payload.get('device', '')
        # Allow frontend to specify count, default to 1 for single, or if not specified
        count = int(payload.get('count', 1))
        
        write_log(f"Scan request received: count={count}, device={device}, mode={mode}")

        # If running on Windows, try WIA first
        if sys.platform.startswith('win'):
            try:
                # For 'multi' mode from the old UI, we might still want to scan more than one page.
                # However, the new UI calls with 'single' for each page.
                # This logic keeps compatibility but prefers the explicit 'count'.
                scan_count = count
                if mode == 'multi' and 'count' not in payload:
                    scan_count = 1 # Always default to 1 unless specified
                
                write_log(f"Attempting WIA scan with device: {device or 'Kyocera FS-3540MFP KX'}")
                images = try_wia_scan(count=scan_count, preferred_device_name=(device or 'Kyocera FS-3540MFP KX'))
                if images:
                    write_log(f"WIA scan successful, returning {len(images)} pages")
                    return jsonify({ 'images': images })
            except Exception as e:
                # fallback to simulation
                error_msg = str(e)
                write_log(f'WIA scan failed, falling back to simulation: {error_msg}', 'WARNING')
                print('WIA scan failed, falling back to simulation:', e)
                
                # إنشاء رسالة خطأ مفصلة للمحاكاة
                error_message = f"فشل الاتصال بالماسح الضوئي\n"
                error_message += f"السبب: {error_msg}\n"
                error_message += f"\nللمساعدة:\n"
                error_message += f"1. تأكد من تشغيل الماسح الضوئي وتوصيله بالكمبيوتر\n"
                error_message += f"2. تأكد من تثبيت برامج التشغيل الخاصة بالماسح\n"
                error_message += f"3. قم بتشغيل ملف تثبيت_وكيل_المسح_كخدمة.bat\n"

        # Default: simulated pages with error message
        error_message = "لم يتم العثور على ماسح ضوئي متصل\n"
        error_message += "يرجى التأكد من:\n"
        error_message += "1. تشغيل الماسح الضوئي وتوصيله بالكمبيوتر\n"
        error_message += "2. تثبيت برامج التشغيل الخاصة بالماسح\n"
        error_message += "3. تشغيل ملف تثبيت_وكيل_المسح_كخدمة.bat\n"
        
        pages = simulate_pages(count, device_name=device or 'Kyocera FS-3540MFP KX', error_message=error_message)
        return jsonify({ 'images': pages })
    except Exception as e:
        write_log(f'Scan endpoint error: {e}')
        return jsonify({ 'error': str(e) }), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({ 'status': 'ok' })


@app.route('/test_scanner.html')
def test_scanner_html():
    return send_from_directory('static', 'test_scanner.html')


# وظيفة بدء التشغيل الرئيسية
def start_server(host='0.0.0.0', port=5005, debug=False):
    try:
        # التحقق من حالة الشبكة
        network_available, local_ip = check_network()
        
        # تسجيل معلومات بدء التشغيل
        write_log(f"Starting scan_agent HTTP server on {host}:{port}")
        write_log(f"System platform: {sys.platform}")
        write_log(f"Python version: {sys.version}")
        write_log(f"WIA support: {'Available' if HAS_WIA else 'Not available'}")
        write_log(f"FTP support: {'Available' if HAS_FTP else 'Not available'}")
        
        if network_available:
            write_log(f"Server will be accessible at http://{local_ip}:{port}/")
            write_log(f"Health check URL: http://{local_ip}:{port}/health")
        
        # بدء تشغيل الخادم
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        error_details = traceback.format_exc()
        write_log(f"Server failed to start: {str(e)}\n{error_details}", 'ERROR')
        sys.exit(1)

if __name__ == '__main__':
    # تحديد ما إذا كان يعمل في وضع التصحيح
    debug_mode = '--debug' in sys.argv
    
    # بدء تشغيل الخادم
    start_server(debug=debug_mode)





@app.route('/scan_ftp', methods=['POST'])
def scan_ftp():
    """
    Start a temporary FTP server and wait for the MFP to upload scanned files.
    Request JSON body (optional): { "timeout": 30, "username": "scan", "password": "scan", "port": 2121 }
    Response: { "images": [dataUrl,...] } or { "error": "..." }
    """
    try:
        if not HAS_FTP:
            return jsonify({ 'error': 'FTP receiver not available (pyftpdlib not installed)'}), 500

        payload = request.get_json() or {}
        timeout = int(payload.get('timeout', 30))
        username = payload.get('username', 'scan')
        password = payload.get('password', 'scan')
        port = int(payload.get('port', 2121))

        images = start_ftp_receiver(timeout=timeout, username=username, password=password, port=port)
        if images:
            return jsonify({ 'images': images })
        else:
            return jsonify({ 'images': [] })
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500
