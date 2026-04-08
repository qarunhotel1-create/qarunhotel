/**
 * نظام الماسح الضوئي المتقدم
 * يدعم المسح من الطابعة مباشرة ومعالجة الصور
 */

class AdvancedScanner {
    constructor() {
        this.isScanning = false;
        this.scannedPages = [];
        this.currentMode = 'single'; // single, multi
        this.scanQuality = 'high';
        this.scanResolution = 300;
        
        // إعداد الأحداث
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // أحداث الماسح الضوئي
        document.addEventListener('scannerReady', this.onScannerReady.bind(this));
        document.addEventListener('scanComplete', this.onScanComplete.bind(this));
        document.addEventListener('scanError', this.onScanError.bind(this));
    }
    
    /**
     * بدء عملية المسح
     */
    async startScan(mode = 'single') {
        if (this.isScanning) {
            throw new Error('المسح قيد التشغيل بالفعل');
        }
        
        this.currentMode = mode;
        this.isScanning = true;
        this.scannedPages = [];
        
        try {
            // محاولة الاتصال بالماسح الضوئي
            const scannerAvailable = await this.checkScannerAvailability();
            
            if (scannerAvailable) {
                return await this.scanFromDevice();
            } else {
                // استخدام الكاميرا كبديل
                return await this.scanFromCamera();
            }
        } catch (error) {
            this.isScanning = false;
            throw error;
        }
    }
    
    /**
     * التحقق من توفر الماسح الضوئي
     */
    async checkScannerAvailability() {
        try {
            // محاولة الوصول للماسح عبر Web API
            if ('navigator' in window && 'mediaDevices' in navigator) {
                const devices = await navigator.mediaDevices.enumerateDevices();
                const scanners = devices.filter(device => 
                    device.kind === 'videoinput' && 
                    device.label.toLowerCase().includes('scanner')
                );
                return scanners.length > 0;
            }
            
            // محاولة الوصول عبر TWAIN (إذا كان متاحاً)
            if (window.DynamicWebTWAIN) {
                return window.DynamicWebTWAIN.SourceCount > 0;
            }
            
            return false;
        } catch (error) {
            console.warn('تعذر التحقق من الماسح الضوئي:', error);
            return false;
        }
    }
    
    /**
     * المسح من الجهاز المباشر
     */
    async scanFromDevice() {
        return new Promise((resolve, reject) => {
            try {
                // استخدام TWAIN إذا كان متاحاً
                if (window.DynamicWebTWAIN) {
                    this.scanWithTWAIN(resolve, reject);
                } else {
                    // محاولة استخدام Web API
                    this.scanWithWebAPI(resolve, reject);
                }
            } catch (error) {
                reject(error);
            }
        });
    }
    
    /**
     * المسح باستخدام TWAIN
     */
    scanWithTWAIN(resolve, reject) {
        const DWObject = window.DynamicWebTWAIN.GetWebTWAIN('dwtcontrolContainer');
        
        if (DWObject) {
            // إعداد خصائص المسح
            DWObject.IfShowUI = false;
            DWObject.Resolution = this.scanResolution;
            DWObject.PixelType = 2; // ملون
            
            // بدء المسح
            DWObject.AcquireImage(
                () => {
                    // نجح المسح
                    const imageCount = DWObject.HowManyImagesInBuffer;
                    const images = [];
                    
                    for (let i = 0; i < imageCount; i++) {
                        const imageData = DWObject.GetImageURL(i, 'image/jpeg');
                        images.push(imageData);
                    }
                    
                    this.scannedPages = images;
                    this.isScanning = false;
                    resolve(images);
                },
                (errorCode, errorString) => {
                    // فشل المسح
                    this.isScanning = false;
                    reject(new Error(`خطأ في المسح: ${errorString}`));
                }
            );
        } else {
            reject(new Error('تعذر الوصول للماسح الضوئي'));
        }
    }
    
    /**
     * المسح باستخدام Web API
     */
    async scanWithWebAPI(resolve, reject) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1920 },
                    height: { ideal: 1080 },
                    facingMode: 'environment'
                }
            });
            
            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();
            
            video.onloadedmetadata = () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                
                // التقاط الصورة
                ctx.drawImage(video, 0, 0);
                const imageData = canvas.toDataURL('image/jpeg', 0.8);
                
                // إيقاف الكاميرا
                stream.getTracks().forEach(track => track.stop());
                
                this.scannedPages = [imageData];
                this.isScanning = false;
                resolve([imageData]);
            };
            
        } catch (error) {
            reject(error);
        }
    }
    
    /**
     * المسح من الكاميرا كبديل
     */
    async scanFromCamera() {
        return new Promise((resolve, reject) => {
            // إنشاء واجهة الكاميرا
            const cameraModal = this.createCameraInterface();
            document.body.appendChild(cameraModal);
            
            // عرض الـ modal
            const modal = new bootstrap.Modal(cameraModal);
            modal.show();
            
            // إعداد الكاميرا
            this.setupCamera(cameraModal, resolve, reject);
        });
    }
    
    /**
     * إنشاء واجهة الكاميرا
     */
    createCameraInterface() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-camera me-2"></i>مسح ضوئي بالكاميرا
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <div class="camera-container">
                            <video id="cameraVideo" autoplay playsinline style="max-width: 100%; border-radius: 8px;"></video>
                            <canvas id="cameraCanvas" style="display: none;"></canvas>
                        </div>
                        <div class="camera-controls mt-3">
                            <button type="button" class="btn btn-primary btn-lg" id="captureBtn">
                                <i class="fas fa-camera me-2"></i>التقاط
                            </button>
                            <button type="button" class="btn btn-success btn-lg ms-2" id="confirmCaptureBtn" style="display: none;">
                                <i class="fas fa-check me-2"></i>تأكيد
                            </button>
                            <button type="button" class="btn btn-warning btn-lg ms-2" id="retakeBtn" style="display: none;">
                                <i class="fas fa-redo me-2"></i>إعادة التقاط
                            </button>
                        </div>
                        <div class="preview-container mt-3" id="previewContainer" style="display: none;">
                            <img id="previewImage" style="max-width: 100%; border-radius: 8px;">
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return modal;
    }
    
    /**
     * إعداد الكاميرا
     */
    async setupCamera(modal, resolve, reject) {
        const video = modal.querySelector('#cameraVideo');
        const canvas = modal.querySelector('#cameraCanvas');
        const captureBtn = modal.querySelector('#captureBtn');
        const confirmBtn = modal.querySelector('#confirmCaptureBtn');
        const retakeBtn = modal.querySelector('#retakeBtn');
        const previewContainer = modal.querySelector('#previewContainer');
        const previewImage = modal.querySelector('#previewImage');
        
        let stream = null;
        let capturedImage = null;
        
        try {
            // بدء الكاميرا
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1920 },
                    height: { ideal: 1080 },
                    facingMode: 'environment'
                }
            });
            
            video.srcObject = stream;
            
            // التقاط الصورة
            captureBtn.addEventListener('click', () => {
                const ctx = canvas.getContext('2d');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                
                ctx.drawImage(video, 0, 0);
                capturedImage = canvas.toDataURL('image/jpeg', 0.8);
                
                // عرض المعاينة
                previewImage.src = capturedImage;
                video.style.display = 'none';
                previewContainer.style.display = 'block';
                captureBtn.style.display = 'none';
                confirmBtn.style.display = 'inline-block';
                retakeBtn.style.display = 'inline-block';
            });
            
            // تأكيد الالتقاط
            confirmBtn.addEventListener('click', () => {
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
                
                this.scannedPages = [capturedImage];
                this.isScanning = false;
                
                // إغلاق الـ modal
                bootstrap.Modal.getInstance(modal).hide();
                modal.remove();
                
                resolve([capturedImage]);
            });
            
            // إعادة التقاط
            retakeBtn.addEventListener('click', () => {
                video.style.display = 'block';
                previewContainer.style.display = 'none';
                captureBtn.style.display = 'inline-block';
                confirmBtn.style.display = 'none';
                retakeBtn.style.display = 'none';
            });
            
            // إغلاق الـ modal
            modal.addEventListener('hidden.bs.modal', () => {
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
                modal.remove();
                
                if (!capturedImage) {
                    this.isScanning = false;
                    reject(new Error('تم إلغاء المسح'));
                }
            });
            
        } catch (error) {
            this.isScanning = false;
            modal.remove();
            reject(new Error('تعذر الوصول للكاميرا: ' + error.message));
        }
    }
    
    /**
     * إضافة صفحة جديدة (للمسح المتعدد)
     */
    async addPage() {
        if (!this.isScanning || this.currentMode !== 'multi') {
            throw new Error('المسح المتعدد غير نشط');
        }
        
        try {
            const newPages = await this.scanFromDevice();
            this.scannedPages.push(...newPages);
            return newPages;
        } catch (error) {
            throw error;
        }
    }
    
    /**
     * إنهاء المسح المتعدد
     */
    finishMultiScan() {
        if (this.currentMode !== 'multi') {
            throw new Error('المسح المتعدد غير نشط');
        }
        
        this.isScanning = false;
        return this.scannedPages;
    }
    
    /**
     * حذف صفحة
     */
    removePage(pageIndex) {
        if (pageIndex >= 0 && pageIndex < this.scannedPages.length) {
            this.scannedPages.splice(pageIndex, 1);
            return true;
        }
        return false;
    }
    
    /**
     * تحسين جودة الصورة
     */
    enhanceImage(imageData) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                canvas.width = img.width;
                canvas.height = img.height;
                
                // رسم الصورة
                ctx.drawImage(img, 0, 0);
                
                // تطبيق فلاتر التحسين
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const data = imageData.data;
                
                // تحسين التباين والسطوع
                for (let i = 0; i < data.length; i += 4) {
                    // تحسين السطوع
                    data[i] = Math.min(255, data[i] * 1.1);     // أحمر
                    data[i + 1] = Math.min(255, data[i + 1] * 1.1); // أخضر
                    data[i + 2] = Math.min(255, data[i + 2] * 1.1); // أزرق
                }
                
                ctx.putImageData(imageData, 0, 0);
                
                // إرجاع الصورة المحسنة
                const enhancedImage = canvas.toDataURL('image/jpeg', 0.9);
                resolve(enhancedImage);
            };
            img.src = imageData;
        });
    }
    
    /**
     * تحويل الصور إلى PDF
     */
    async convertToPDF(images, title = 'مستند ممسوح') {
        // استخدام jsPDF لإنشاء PDF
        if (typeof window.jsPDF !== 'undefined') {
            const { jsPDF } = window.jsPDF;
            const pdf = new jsPDF();
            
            for (let i = 0; i < images.length; i++) {
                if (i > 0) {
                    pdf.addPage();
                }
                
                // إضافة الصورة للصفحة
                const img = new Image();
                img.src = images[i];
                
                await new Promise((resolve) => {
                    img.onload = () => {
                        const imgWidth = 210; // A4 width in mm
                        const imgHeight = (img.height * imgWidth) / img.width;
                        
                        pdf.addImage(img, 'JPEG', 0, 0, imgWidth, imgHeight);
                        resolve();
                    };
                });
            }
            
            return pdf.output('datauristring');
        } else {
            throw new Error('مكتبة PDF غير متاحة');
        }
    }
    
    /**
     * أحداث الماسح الضوئي
     */
    onScannerReady(event) {
        console.log('الماسح الضوئي جاهز:', event.detail);
    }
    
    onScanComplete(event) {
        console.log('اكتمل المسح:', event.detail);
        this.isScanning = false;
    }
    
    onScanError(event) {
        console.error('خطأ في المسح:', event.detail);
        this.isScanning = false;
    }
    
    /**
     * الحصول على حالة الماسح
     */
    getStatus() {
        return {
            isScanning: this.isScanning,
            currentMode: this.currentMode,
            pagesCount: this.scannedPages.length,
            scanQuality: this.scanQuality,
            scanResolution: this.scanResolution
        };
    }
}

// إنشاء مثيل عام للماسح الضوئي
window.AdvancedScanner = AdvancedScanner;
window.scanner = new AdvancedScanner();

// تصدير للاستخدام في Node.js إذا لزم الأمر
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedScanner;
}