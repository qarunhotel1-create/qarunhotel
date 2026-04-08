// ===== إصلاح شامل لمشاكل Modal في النظام =====

document.addEventListener('DOMContentLoaded', function() {
    console.log('تم تحميل إصلاحات Modal');
    
    // إصلاح شامل لجميع الـ modals
    fixAllModals();
    
    // مراقبة إضافة modals جديدة
    observeNewModals();
});

function fixAllModals() {
    // البحث عن جميع الـ modals في الصفحة
    const modals = document.querySelectorAll('.modal');
    
    modals.forEach(modal => {
        setupModalFix(modal);
    });
}

function setupModalFix(modal) {
    console.log('إعداد إصلاحات للـ modal:', modal.id);
    
    // إصلاح z-index
    modal.style.zIndex = '10500';
    
    // معالج عند فتح الـ modal
    modal.addEventListener('show.bs.modal', function() {
        console.log('فتح modal:', this.id);
        
        // إصلاح z-index
        this.style.zIndex = '10500';
        
        // إصلاح backdrop
        setTimeout(() => {
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.style.zIndex = '10499';
            }
        }, 50);
    });
    
    // معالج عند اكتمال فتح الـ modal
    modal.addEventListener('shown.bs.modal', function() {
        console.log('تم فتح modal بالكامل:', this.id);
        
        // إصلاح جميع العناصر داخل الـ modal
        fixModalElements(this);
        
        // إضافة معالجات للأزرار
        setupModalButtons(this);
        
        // إصلاح مناطق الرفع
        setupUploadAreas(this);
        
        // إصلاح عناصر الإدخال
        setupInputElements(this);
    });
    
    // معالج عند إغلاق الـ modal
    modal.addEventListener('hidden.bs.modal', function() {
        console.log('تم إغلاق modal:', this.id);
        
        // تنظيف backdrop إضافية
        cleanupBackdrops();
        
        // إعادة تعيين حالة الصفحة
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    });
}

function fixModalElements(modal) {
    // إصلاح جميع العناصر
    const allElements = modal.querySelectorAll('*');
    allElements.forEach(element => {
        element.style.pointerEvents = 'auto';
    });
    
    // إصلاح الـ modal نفسه
    modal.style.pointerEvents = 'auto';
    
    // إصلاح modal-content
    const modalContent = modal.querySelector('.modal-content');
    if (modalContent) {
        modalContent.style.zIndex = '10502';
        modalContent.style.position = 'relative';
        modalContent.style.pointerEvents = 'auto';
    }
    
    // إصلاح modal-dialog
    const modalDialog = modal.querySelector('.modal-dialog');
    if (modalDialog) {
        modalDialog.style.zIndex = '10501';
        modalDialog.style.position = 'relative';
    }
}

function setupModalButtons(modal) {
    const buttons = modal.querySelectorAll('.btn');
    
    buttons.forEach(btn => {
        // إصلاح الخصائص الأساسية
        btn.style.pointerEvents = 'auto';
        btn.style.cursor = 'pointer';
        btn.style.zIndex = '10504';
        btn.style.position = 'relative';
        
        // إضافة معالج للنقر إذا لم يكن موجوداً
        if (!btn.hasAttribute('data-modal-fix-applied')) {
            btn.addEventListener('click', function(e) {
                console.log('تم النقـر على زر في modal:', this.textContent.trim());

                // Upload trigger: open file input inside the modal
                if (this.id === 'modalUploadBtn' || this.classList.contains('upload-trigger')) {
                    e.preventDefault();
                    e.stopPropagation();

                    const fileInput = modal.querySelector('input[type="file"]');
                    if (fileInput) {
                        fileInput.click();
                    }
                    return;
                }

                // Scan triggers: dispatch a custom event 'openPrinterScanner' (mode: multi by default)
                if (
                    this.id === 'modalScanBtn' ||
                    this.id === 'modalMultiScanBtn' ||
                    this.id === 'modalPrinterScanBtn' ||
                    this.classList.contains('scan-trigger') ||
                    this.classList.contains('multi-scan-trigger') ||
                    this.classList.contains('printer-scan-trigger')
                ) {
                    e.preventDefault();
                    e.stopPropagation();

                    const customEvent = new CustomEvent('openPrinterScanner', {
                        detail: { mode: 'multi' }
                    });
                    modal.dispatchEvent(customEvent);
                    return;
                }
            });

            btn.setAttribute('data-modal-fix-applied', 'true');
        }
    });
}

function setupUploadAreas(modal) {
    const uploadAreas = modal.querySelectorAll('.upload-area');
    
    uploadAreas.forEach(area => {
        area.style.pointerEvents = 'auto';
        area.style.cursor = 'pointer';
        area.style.zIndex = '10503';
        area.style.position = 'relative';
        
        // إضافة معالج للنقر إذا لم يكن موجوداً
        if (!area.hasAttribute('data-upload-fix-applied')) {
            area.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('تم النقر على منطقة الرفع');
                
                const fileInput = modal.querySelector('input[type="file"]');
                if (fileInput) {
                    fileInput.click();
                }
            });
            
            area.setAttribute('data-upload-fix-applied', 'true');
        }
    });
}

function setupInputElements(modal) {
    const inputs = modal.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.style.pointerEvents = 'auto';
        input.style.zIndex = '10504';
        input.style.position = 'relative';
        
        // إصلاح خاص لـ file inputs
        if (input.type === 'file') {
            input.style.pointerEvents = 'auto';
            
            if (!input.hasAttribute('data-file-fix-applied')) {
                input.addEventListener('change', function(e) {
                    console.log('تم اختيار ملفات:', this.files.length);
                    
                    // إطلاق حدث مخصص للتعامل مع الملفات
                    const customEvent = new CustomEvent('filesSelected', {
                        detail: { files: Array.from(this.files) }
                    });
                    modal.dispatchEvent(customEvent);
                });
                
                input.setAttribute('data-file-fix-applied', 'true');
            }
        }
    });
}

function cleanupBackdrops() {
    // إزالة جميع backdrop إضافية
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => {
        if (backdrop.parentNode) {
            backdrop.parentNode.removeChild(backdrop);
        }
    });
}

function observeNewModals() {
    // مراقبة إضافة modals جديدة للصفحة
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1 && node.classList && node.classList.contains('modal')) {
                    console.log('تم اكتشاف modal جديد:', node.id);
                    setupModalFix(node);
                }
            });
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// دالة مساعدة لعرض التنبيهات
function showAlert(message, type = 'info') {
    // البحث عن دالة showAlert موجودة
    if (typeof window.showAlert === 'function') {
        window.showAlert(message, type);
        return;
    }
    
    // إنشاء تنبيه بسيط
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '11000';
    alertDiv.style.minWidth = '300px';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // إزالة التنبيه تلقائياً بعد 5 ثوان
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// تصدير الدوال للاستخدام العام
window.modalFix = {
    fixAllModals: fixAllModals,
    setupModalFix: setupModalFix,
    showAlert: showAlert
};

console.log('تم تحميل إصلاحات Modal بنجاح');