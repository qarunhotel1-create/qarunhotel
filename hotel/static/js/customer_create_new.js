// JavaScript لصفحة إنشاء عميل جديد
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 تحميل نظام إنشاء العميل الجديد...');
    
    // وظيفة لعرض رسائل الحالة للمستخدم
    function showStatus(message, type = 'info') {
        // إنشاء عنصر div لعرض الرسالة
        const statusDiv = document.createElement('div');
        statusDiv.className = `alert alert-${type} alert-dismissible fade show mt-2`;
        statusDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // إضافة العنصر إلى الصفحة
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(statusDiv, container.firstChild);
        
        // إزالة الرسالة بعد 5 ثوانٍ
        setTimeout(() => {
            statusDiv.classList.remove('show');
            setTimeout(() => statusDiv.remove(), 500);
        }, 5000);
    }
    
    // زر المسح الضوئي المباشر
    const scanDocumentBtn = document.getElementById('scanDocumentBtn');
    if (scanDocumentBtn) {
        scanDocumentBtn.addEventListener('click', startDirectScan);
    }
    
    // وظيفة بدء المسح الضوئي المباشر
    async function startDirectScan() {
        try {
            // تغيير حالة الزر إلى جاري المسح
            scanDocumentBtn.disabled = true;
            scanDocumentBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري المسح...';
            
            let scannedImage;
            let usedSimulation = false;
            
            try {
                // محاولة استدعاء وكيل المسح المحلي
                showStatus('جاري الاتصال بوكيل المسح الضوئي...', 'info');
                const response = await Promise.race([
                    fetch('http://localhost:5005/scan', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            device: 'Kyocera FS-3540MFP KX',
                            mode: 'single'
                        })
                    }),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('انتهت مهلة الاتصال - تأكد من تشغيل برنامج وكيل المسح الضوئي')), 3000)
                    )
                ]);
                showStatus('تم الاتصال بنجاح، جاري المسح...', 'success');
                
                if (!response.ok) {
                    throw new Error('فشل الاتصال بوكيل المسح - تأكد من توصيل الماسح الضوئي وتشغيله وتثبيت برامج التشغيل الخاصة به');
                }
                
                const data = await response.json();
                
                if (!data.images || data.images.length === 0) {
                    throw new Error('لم يتم استلام أي صور من الماسح الضوئي');
                }
                
                scannedImage = data.images[0];
            } catch (scanError) {
                console.warn('فشل المسح المباشر:', scanError);
                
                // عرض رسالة خطأ للمستخدم
                showStatus(`فشل المسح الضوئي: ${scanError.message}`, 'error');
                
                // عرض نافذة تأكيد للمستخدم
                if (confirm('فشل الاتصال بوكيل المسح الضوئي. هل تريد عرض تعليمات التشغيل؟')) {
                    // عرض تعليمات التشغيل
                    alert(`تعليمات تشغيل الماسح الضوئي:

1. تأكد من تشغيل وكيل المسح الضوئي (Scanner Bridge) باستخدام ملف تشغيل_وكيل_المسح_الضوئي.bat
2. تأكد من توصيل طابعة Kyocera FS-3540MFP KX بالكمبيوتر وتشغيلها
3. تأكد من تثبيت برامج تشغيل الطابعة
4. تأكد من عدم وجود جدار حماية يمنع الاتصال

للمزيد من المعلومات، راجع ملف تعليمات_المسح_الضوئي.txt`);
                }
                
                // استخدام محاكاة المسح الضوئي كحل بديل
                console.log('استخدام محاكاة المسح الضوئي كحل بديل');
                usedSimulation = true;
                
                // إنشاء صورة محاكاة مع رسالة توضح المشكلة
                const errorMessage = scanError.message;
                const canvas = document.createElement('canvas');
                canvas.width = 1240;
                canvas.height = 1754;
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = 'black';
                ctx.font = '24px Arial';
                ctx.textAlign = 'center';
                
                // إضافة عنوان
                ctx.font = 'bold 30px Arial';
                ctx.fillText('محاكاة المسح الضوئي', canvas.width/2, 100);
                
                // إضافة رسالة الخطأ
                ctx.font = '24px Arial';
                ctx.fillText(`خطأ: ${errorMessage}`, canvas.width/2, 150);
                
                // إضافة تعليمات
                ctx.font = '20px Arial';
                ctx.fillText('يرجى تشغيل وكيل المسح الضوئي باستخدام ملف:', canvas.width/2, 200);
                ctx.fillText('تشغيل_وكيل_المسح_الضوئي.bat', canvas.width/2, 230);
                
                // إضافة تاريخ ووقت المحاولة
                ctx.font = '16px Arial';
                ctx.fillText(`تاريخ المحاولة: ${new Date().toLocaleString()}`, canvas.width/2, 300);
                
                // إضافة نص
                ctx.fillStyle = 'black';
                ctx.font = '24px Arial';
                const now = new Date().toLocaleString('ar-EG');
                ctx.fillText(`صفحة محاكاة - تم إنشاؤها في: ${now}`, 50, 50);
                ctx.fillText('(وكيل المسح الضوئي غير متوفر)', 50, 100);
                
                // تحويل الصورة إلى base64
                scannedImage = canvas.toDataURL('image/jpeg').split(',')[1];
            }
            
            // استخدام الصورة الممسوحة
            const fileName = `scan_${new Date().getTime()}.jpg`;
            
            // إنشاء كائن الوثيقة
            const docObj = {
                id: 'scan_' + new Date().getTime(),
                name: fileName,
                size: 0, // غير معروف
                type: 'image/jpeg',
                data: scannedImage,
                method: 'scan'
            };
            
            // إضافة الوثيقة إلى القائمة
            if (typeof newDocumentsData !== 'undefined') {
                newDocumentsData.push(docObj);
            } else {
                window.newDocumentsData = [docObj];
            }
            
            // تحديث حقل البيانات المخفي
            document.getElementById('newDocumentsJsonInput').value = JSON.stringify(window.newDocumentsData);
            
            // تحديث واجهة المستخدم
            updateDocumentsList();
            updateDocumentCounts();
            
            if (usedSimulation) {
                showAlert('تم إنشاء صورة محاكاة (وكيل المسح غير متوفر)', 'warning');
            } else {
                showAlert('تم المسح الضوئي بنجاح', 'success');
            }
        } catch (error) {
            console.error('خطأ في المسح الضوئي:', error);
            showAlert(`فشل المسح الضوئي: ${error.message}`, 'error');
        } finally {
            // إعادة الزر إلى حالته الطبيعية
            scanDocumentBtn.disabled = false;
            scanDocumentBtn.innerHTML = '<i class="fas fa-scanner me-2"></i>مسح ضوئي مباشر';
        }
    }
    
    // وظيفة عرض رسالة تنبيه
    function showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.querySelector('.container-fluid').insertBefore(alertDiv, document.querySelector('.container-fluid').firstChild);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
});