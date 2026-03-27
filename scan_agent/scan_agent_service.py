from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
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
import platform
import socket
import random
from logging.handlers import RotatingFileHandler
import traceback
import signal
import ctypes

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
    FTP_AVAILABLE = True
except ImportError:
    write_log("pyftpdlib غير متوفر، لن يتم دعم المسح الضوئي عبر FTP", 'WARNING')
    FTP_AVAILABLE = False

# التحقق من توفر مكتبة WIA
try:
    import win32com.client
    import win32service
    import win32serviceutil
    import servicemanager
    import win32event
    import win32api
    WIA_AVAILABLE = True
except ImportError:
    write_log("win32com غير متوفر، لن يتم دعم المسح الضوئي عبر WIA", 'WARNING')
    WIA_AVAILABLE = False

# إعدادات الخادم
HTTP_PORT = 5005
FTP_PORT = 2121
FTP_USER = "scanner"
FTP_PASSWORD = "scanner123"
PREFERRED_SCANNER = "Kyocera"  # اسم الماسح الضوئي المفضل (جزئي)

# إنشاء تطبيق فلاسك
app = Flask(__name__)
CORS(app)  # تمكين CORS لجميع المسارات

def simulate_pages(num_pages=1, error_message=None):
    """محاكاة مسح ضوئي لعدد من الصفحات مع رسالة خطأ اختيارية"""
    write_log(f"محاكاة مسح ضوئي لـ {num_pages} صفحة" + (f" مع رسالة خطأ: {error_message}" if error_message else ""))
    images = []
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    for page in range(1, num_pages + 1):
        # إنشاء صورة بيضاء
        img = Image.new('RGB', (1654, 2339), color='white')  # حجم A4 بدقة 200 DPI
        draw = ImageDraw.Draw(img)

        # محاولة تحميل الخط
        try:
            # محاولة استخدام خط يدعم العربية
            font_path = None
            possible_fonts = [
                os.path.join(os.path.dirname(__file__), "arial.ttf"),
                "C:\\Windows\\Fonts\\arial.ttf",
                "C:\\Windows\\Fonts\\arialbd.ttf",
                "C:\\Windows\\Fonts\\tahoma.ttf",
                "C:\\Windows\\Fonts\\segoeui.ttf"
            ]

            for f in possible_fonts:
                if os.path.exists(f):
                    font_path = f
                    break

            if font_path:
                title_font = ImageFont.truetype(font_path, 40)
                header_font = ImageFont.truetype(font_path, 30)
                warning_font = ImageFont.truetype(font_path, 35)
            else:
                # استخدام الخط الافتراضي إذا لم يتم العثور على خط مناسب
                title_font = ImageFont.load_default()
                header_font = ImageFont.load_default()
                warning_font = ImageFont.load_default()
        except Exception as e:
            write_log(f"خطأ في تحميل الخط: {str(e)}", 'ERROR')
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            warning_font = ImageFont.load_default()

        # إضافة ترويسة
        draw.rectangle([(0, 0), (1654, 120)], fill='lightgray')
        draw.text((827, 40), "Kyocera FS-3540MFP KX - وكيل المسح الضوئي", fill='black', font=title_font, anchor="mm")

        # إضافة معلومات المسح
        draw.text((50, 150), f"التاريخ: {date_str}", fill='black', font=header_font)
        draw.text((50, 200), f"الوقت: {time_str}", fill='black', font=header_font)
        draw.text((50, 250), f"الجهاز: Kyocera FS-3540MFP KX", fill='black', font=header_font)
        draw.text((50, 300), f"الصفحة: {page} من {num_pages}", fill='black', font=header_font)

        # إضافة مربع تحذير إذا كان هناك رسالة خطأ
        if error_message:
            # مربع تحذير أحمر
            draw.rectangle([(100, 400), (1554, 600)], outline='red', fill='mistyrose', width=3)
            # نص التحذير
            draw.text((827, 450), "تحذير: محاكاة المسح الضوئي", fill='red', font=warning_font, anchor="mm")
            draw.text((827, 520), error_message, fill='red', font=warning_font, anchor="mm")

        # إضافة بعض الخطوط العشوائية لمحاكاة المستند
        for i in range(20):
            y_pos = 700 + i * 70
            line_length = random.randint(400, 1500)
            draw.line([(50, y_pos), (50 + line_length, y_pos)], fill='black', width=5)

        # إضافة تذييل
        draw.rectangle([(0, 2239-80), (1654, 2339)], fill='lightgray')
        draw.text((827, 2239-40), f"تمت المحاكاة بواسطة وكيل المسح الضوئي - {date_str} {time_str}", fill='black', font=header_font, anchor="mm")

        # تحويل الصورة إلى base64
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=80)
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        images.append(img_str)

    return images

def start_ftp_receiver(timeout=60):
    """بدء خادم FTP لاستقبال الملفات المسحوحة ضوئيًا"""
    if not FTP_AVAILABLE:
        write_log("لا يمكن بدء خادم FTP: pyftpdlib غير متوفر", 'ERROR')
        return None, None

    # إنشاء مجلد مؤقت لاستلام الملفات
    temp_dir = tempfile.mkdtemp()
    write_log(f"تم إنشاء مجلد مؤقت لاستلام الملفات: {temp_dir}")

    # إعداد خادم FTP
    authorizer = DummyAuthorizer()
    authorizer.add_user(FTP_USER, FTP_PASSWORD, temp_dir, perm="elradfmw")

    handler = FTPHandler
    handler.authorizer = authorizer
    handler.banner = "مرحبًا بك في خادم المسح الضوئي FTP"

    # الحصول على عنوان IP المحلي
    local_ip = socket.gethostbyname(socket.gethostname())
    write_log(f"بدء خادم FTP على {local_ip}:{FTP_PORT}")

    # إنشاء وبدء الخادم في خيط منفصل
    server = FTPServer((local_ip, FTP_PORT), handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # إنشاء قائمة لتخزين المسارات المستلمة
    received_files = []

    # وظيفة للانتظار حتى استلام الملفات
    def wait_for_files():
        start_time = time.time()
        while time.time() - start_time < timeout:
            # التحقق من الملفات في المجلد المؤقت
            files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
            if files:
                received_files.extend(files)
                write_log(f"تم استلام {len(files)} ملف عبر FTP")
                return True
            time.sleep(1)
        write_log(f"انتهت مهلة انتظار الملفات بعد {timeout} ثانية", 'WARNING')
        return False

    # بدء خيط الانتظار
    wait_thread = threading.Thread(target=wait_for_files)
    wait_thread.daemon = True
    wait_thread.start()

    return server, temp_dir, received_files

def try_wia_scan(num_pages=1):
    """محاولة المسح الضوئي باستخدام WIA"""
    if not WIA_AVAILABLE:
        write_log("لا يمكن استخدام WIA: win32com غير متوفر", 'ERROR')
        return None, "مكتبة WIA غير متوفرة. يرجى التأكد من تثبيت pywin32."

    try:
        write_log("بدء المسح الضوئي باستخدام WIA...")
        wia = win32com.client.Dispatch('WIA.DeviceManager')
        devices = wia.DeviceInfos

        # البحث عن الماسح الضوئي
        scanner = None
        scanner_name = ""

        # أولاً، البحث عن الماسح الضوئي المفضل
        for i in range(devices.Count):
            if devices[i].Type == 1:  # نوع الماسح الضوئي
                device_name = devices[i].Properties['Name'].Value
                write_log(f"تم العثور على ماسح ضوئي: {device_name}")
                if PREFERRED_SCANNER and PREFERRED_SCANNER.lower() in device_name.lower():
                    scanner = devices[i]
                    scanner_name = device_name
                    write_log(f"تم اختيار الماسح الضوئي المفضل: {scanner_name}")
                    break

        # إذا لم يتم العثور على الماسح الضوئي المفضل، استخدم أول ماسح ضوئي متاح
        if scanner is None:
            for i in range(devices.Count):
                if devices[i].Type == 1:  # نوع الماسح الضوئي
                    scanner = devices[i]
                    scanner_name = scanner.Properties['Name'].Value
                    write_log(f"استخدام أول ماسح ضوئي متاح: {scanner_name}")
                    break

        if scanner is None:
            write_log("لم يتم العثور على أي ماسح ضوئي", 'ERROR')
            return None, "لم يتم العثور على أي ماسح ضوئي متصل. يرجى التأكد من توصيل الماسح الضوئي وتثبيت برامج التشغيل الخاصة به."

        # اتصال بالماسح الضوئي
        device = scanner.Connect()
        write_log(f"تم الاتصال بالماسح الضوئي: {scanner_name}")

        # الحصول على خصائص المسح الضوئي
        properties = device.Properties

        # ضبط خصائص المسح الضوئي (قد تختلف حسب الماسح الضوئي)
        try:
            properties['Current Intent'].Value = 2  # Color
            properties['Horizontal Resolution'].Value = 200  # DPI
            properties['Vertical Resolution'].Value = 200  # DPI
        except Exception as e:
            write_log(f"تحذير: لا يمكن ضبط بعض خصائص المسح الضوئي: {str(e)}", 'WARNING')

        # قائمة لتخزين الصور المسحوحة ضوئيًا
        scanned_images = []

        # المسح الضوئي لكل صفحة
        for page in range(num_pages):
            try:
                write_log(f"مسح الصفحة {page+1} من {num_pages}...")
                item = device.Items[1]  # الحصول على العنصر الأول (الماسح الضوئي)
                image = item.Transfer()

                # تحويل الصورة إلى base64
                path = os.path.join(tempfile.gettempdir(), f"scan_{page}.jpg")
                image.SaveFile(path)

                # تحويل الصورة إلى base64
                with open(path, 'rb') as img_file:
                    img_data = img_file.read()
                    img_str = base64.b64encode(img_data).decode('utf-8')
                    scanned_images.append(img_str)

                # حذف الملف المؤقت
                os.remove(path)
            except Exception as e:
                write_log(f"خطأ أثناء مسح الصفحة {page+1}: {str(e)}", 'ERROR')
                return None, f"حدث خطأ أثناء مسح الصفحة {page+1}: {str(e)}"

        write_log(f"تم مسح {len(scanned_images)} صفحة بنجاح")
        return scanned_images, None

    except Exception as e:
        error_msg = str(e)
        write_log(f"خطأ أثناء المسح الضوئي: {error_msg}", 'ERROR')
        return None, f"حدث خطأ أثناء المسح الضوئي: {error_msg}"

@app.route('/health', methods=['GET'])
def health_check():
    """التحقق من حالة الخدمة"""
    return jsonify({"status": "running", "timestamp": datetime.datetime.now().isoformat()})

@app.route('/test_scanner.html', methods=['GET'])
def test_scanner_page():
    """صفحة اختبار الماسح الضوئي"""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'test_scanner.html')

@app.route('/scan', methods=['POST'])
def scan():
    """واجهة برمجة التطبيقات للمسح الضوئي"""
    try:
        data = request.get_json()
        num_pages = data.get('num_pages', 1) if data else 1

        # التحقق من صحة عدد الصفحات
        try:
            num_pages = int(num_pages)
            if num_pages < 1 or num_pages > 10:
                return jsonify({"error": "عدد الصفحات يجب أن يكون بين 1 و 10"}), 400
        except ValueError:
            return jsonify({"error": "عدد الصفحات يجب أن يكون رقمًا صحيحًا"}), 400

        # محاولة المسح الضوئي باستخدام WIA
        images, error = try_wia_scan(num_pages)

        # إذا فشل المسح الضوئي، استخدم المحاكاة
        if images is None:
            write_log(f"فشل المسح الضوئي باستخدام WIA: {error}. استخدام المحاكاة بدلاً من ذلك.")
            images = simulate_pages(num_pages, error)
            return jsonify({"images": images, "simulated": True, "error": error})

        return jsonify({"images": images, "simulated": False})

    except Exception as e:
        error_msg = str(e)
        write_log(f"خطأ في طلب المسح الضوئي: {error_msg}", 'ERROR')
        traceback.print_exc()
        # استخدام المحاكاة في حالة حدوث خطأ
        images = simulate_pages(1, f"خطأ غير متوقع: {error_msg}")
        return jsonify({"images": images, "simulated": True, "error": error_msg})

@app.route('/scan_ftp', methods=['POST'])
def scan_ftp():
    """واجهة برمجة التطبيقات للمسح الضوئي عبر FTP"""
    try:
        if not FTP_AVAILABLE:
            return jsonify({"error": "FTP غير متاح. يرجى تثبيت pyftpdlib."}), 500

        data = request.get_json()
        timeout = data.get('timeout', 60) if data else 60

        # بدء خادم FTP
        server, temp_dir, received_files = start_ftp_receiver(timeout)
        if server is None:
            return jsonify({"error": "فشل في بدء خادم FTP"}), 500

        # الحصول على عنوان IP المحلي
        local_ip = socket.gethostbyname(socket.gethostname())

        # إرجاع معلومات الاتصال بخادم FTP
        return jsonify({
            "ftp_server": local_ip,
            "ftp_port": FTP_PORT,
            "ftp_user": FTP_USER,
            "ftp_password": FTP_PASSWORD,
            "temp_dir": temp_dir,
            "timeout": timeout
        })

    except Exception as e:
        error_msg = str(e)
        write_log(f"خطأ في طلب المسح الضوئي عبر FTP: {error_msg}", 'ERROR')
        traceback.print_exc()
        return jsonify({"error": f"حدث خطأ: {error_msg}"}), 500

def start_server():
    """بدء خادم الويب"""
    try:
        # تسجيل معلومات النظام
        write_log(f"بدء وكيل المسح الضوئي على المنفذ {HTTP_PORT}")
        write_log(f"نظام التشغيل: {platform.system()} {platform.release()}")
        write_log(f"بايثون: {sys.version}")
        write_log(f"WIA متاح: {WIA_AVAILABLE}")
        write_log(f"FTP متاح: {FTP_AVAILABLE}")

        # الحصول على عنوان IP المحلي
        local_ip = socket.gethostbyname(socket.gethostname())
        write_log(f"عنوان IP المحلي: {local_ip}")

        # بدء الخادم
        app.run(host='0.0.0.0', port=HTTP_PORT, debug=False, threaded=True)
    except Exception as e:
        write_log(f"خطأ في بدء الخادم: {str(e)}", 'ERROR')
        traceback.print_exc()

# تنفيذ كخدمة Windows
if WIA_AVAILABLE:
    class ScanAgentService(win32serviceutil.ServiceFramework):
        _svc_name_ = "ScanAgentService"
        _svc_display_name_ = "Scanner Agent Service"
        _svc_description_ = "خدمة وكيل المسح الضوئي للاتصال بالماسحات الضوئية"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.is_running = False

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            self.is_running = False

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            self.is_running = True
            self.main()

        def main(self):
            # بدء خادم الويب في خيط منفصل
            server_thread = threading.Thread(target=start_server)
            server_thread.daemon = True
            server_thread.start()

            # انتظار إشارة التوقف
            while self.is_running:
                rc = win32event.WaitForSingleObject(self.hWaitStop, 1000)
                if rc == win32event.WAIT_OBJECT_0:
                    break

# معالجة إشارات التوقف
def signal_handler(sig, frame):
    write_log("تم استلام إشارة توقف، جاري إيقاف الخادم...")
    sys.exit(0)

if __name__ == '__main__':
    # تسجيل معالج الإشارة
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # التحقق مما إذا كان البرنامج يعمل كخدمة
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'install':
        if WIA_AVAILABLE:
            win32serviceutil.HandleCommandLine(ScanAgentService)
        else:
            write_log("لا يمكن تثبيت الخدمة: win32com غير متوفر", 'ERROR')
    elif len(sys.argv) > 1 and sys.argv[1].lower() in ['start', 'stop', 'remove', 'update']:
        if WIA_AVAILABLE:
            win32serviceutil.HandleCommandLine(ScanAgentService)
        else:
            write_log("لا يمكن إدارة الخدمة: win32com غير متوفر", 'ERROR')
    else:
        # تشغيل كتطبيق عادي
        start_server()