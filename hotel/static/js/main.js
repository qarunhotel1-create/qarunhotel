// ===== نظام إدارة الفندق - ملف JavaScript الرئيسي =====

document.addEventListener('DOMContentLoaded', function() {
    // ===== تهيئة Bootstrap Components =====
    initializeBootstrapComponents();

    // ===== التحقق من صحة النماذج =====
    initializeFormValidation();

    // ===== إدارة التنبيهات =====
    initializeAlerts();

    // ===== إدارة النوافذ المنبثقة للمرفقات =====
    initializeAttachmentModals();

    // ===== ضبط الإزاحة العلوية للمحتوى بحسب ارتفاع الشريط (للجوال) =====
    adjustNavbarOffset();
    window.addEventListener('resize', adjustNavbarOffset);
    window.addEventListener('load', adjustNavbarOffset);
    // إعادة الحساب بعد التحميل بقليل لضمان تحميل الخطوط/الأنماط
    setTimeout(adjustNavbarOffset, 100);
    setTimeout(adjustNavbarOffset, 300);
    const navCollapse = document.getElementById('navbarNav');
    if (navCollapse) {
        navCollapse.addEventListener('shown.bs.collapse', adjustNavbarOffset);
        navCollapse.addEventListener('hidden.bs.collapse', adjustNavbarOffset);
    }
});

// ===== تهيئة Bootstrap Components =====
function initializeBootstrapComponents() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// ===== تأثيرات الانيميشن - تم إزالتها =====
// تم إزالة جميع التأثيرات المتحركة لجعل العناصر مرئية دائماً

// ===== التحقق من صحة النماذج =====
function initializeFormValidation() {

    // التحقق من صحة تواريخ الحجز
    const checkInDateInput = document.getElementById('check_in_date');
    const checkOutDateInput = document.getElementById('check_out_date');

    if (checkInDateInput && checkOutDateInput) {
        // إزالة قيود التاريخ - يمكن اختيار أي تاريخ
        // const today = new Date().toISOString().split('T')[0];
        // checkInDateInput.setAttribute('min', today);

        // إزالة قيود تاريخ المغادرة
        checkInDateInput.addEventListener('change', function() {
            // إزالة القيود - يمكن اختيار أي تاريخ
            // if (checkInDateInput.value) {
            //     checkOutDateInput.setAttribute('min', checkInDateInput.value);
            //     if (checkOutDateInput.value && checkOutDateInput.value < checkInDateInput.value) {
            //         checkOutDateInput.value = checkInDateInput.value;
            //     }
            // }

                // تم إزالة التأثير البصري المتحرك
                // checkInDateInput.style.borderColor = '#10b981';
                // setTimeout(() => {
                //     checkInDateInput.style.borderColor = '';
                // }, 1000);
            }
        });
    }

    // التحقق من توفر الغرف
    const roomSelect = document.getElementById('room_id');
    if (roomSelect) {
        roomSelect.addEventListener('change', function() {
            // تم إزالة التأثير البصري المؤقت
            console.log('تم اختيار الغرفة:', this.value);
        });
    }
}

// ===== التأثيرات التفاعلية - تم إزالتها =====
// تم إزالة جميع التأثيرات التفاعلية والمتحركة لجعل الواجهة ثابتة ومرئية

// ===== إدارة التنبيهات =====
function initializeAlerts() {
    // إضافة أزرار إغلاق للتنبيهات التي لا تحتوي عليها
    var alerts = document.querySelectorAll('.alert:not(.alert-dismissible)');
    alerts.forEach(function(alert) {
        // تحويل التنبيه إلى قابل للإغلاق
        alert.classList.add('alert-dismissible', 'fade', 'show');

        // إضافة زر الإغلاق إذا لم يكن موجوداً
        if (!alert.querySelector('.btn-close')) {
            var closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'btn-close';
            closeButton.setAttribute('data-bs-dismiss', 'alert');
            closeButton.setAttribute('aria-label', 'إغلاق');
            alert.appendChild(closeButton);
        }
    });

    // إضافة تأثيرات انيميشن للتنبيهات الجديدة
    var allAlerts = document.querySelectorAll('.alert');
    allAlerts.forEach(function(alert) {
        // إضافة تأثير الظهور
        alert.style.animation = 'slideInDown 0.5s ease-out';

        // إضافة مستمع لحدث الإغلاق
        alert.addEventListener('closed.bs.alert', function() {
            console.log('تم إغلاق التنبيه');
        });
    });

    // إضافة خيار الإغلاق الجماعي للتنبيهات المتعددة
    addBulkDismissOption();
}

// دالة لإضافة خيار الإغلاق الجماعي
function addBulkDismissOption() {
    var alerts = document.querySelectorAll('.alert');
    if (alerts.length > 2) {
        // إنشاء زر الإغلاق الجماعي
        var bulkDismissContainer = document.createElement('div');
        bulkDismissContainer.className = 'text-end mb-3';
        bulkDismissContainer.innerHTML = `
            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="dismissAllAlerts()">
                <i class="fas fa-times me-1"></i>إغلاق جميع التنبيهات
            </button>
        `;

        // إدراج الزر قبل أول تنبيه
        var firstAlert = alerts[0];
        firstAlert.parentNode.insertBefore(bulkDismissContainer, firstAlert);
    }
}

// دالة لإغلاق جميع التنبيهات
function dismissAllAlerts() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        var closeButton = alert.querySelector('.btn-close');
        if (closeButton) {
            closeButton.click();
        }
    });
}

// ===== CSS أساسي بدون تأثيرات متحركة =====
const style = document.createElement('style');
style.textContent = `
    /* تنسيق أساسي للتنبيهات بدون تأثيرات */
    .alert {
        position: relative;
        margin-bottom: 1rem;
    }

    .alert .btn-close {
        position: absolute;
        top: 0.5rem;
        left: 0.5rem;
        z-index: 2;
    }

    .alert-dismissible {
        padding-left: 3rem;
    }

    /* تحسين مظهر الجداول بدون تأثيرات */
    .table tbody tr:hover {
        background-color: rgba(59, 130, 246, 0.05) !important;
    }
`;
document.head.appendChild(style);

// ===== دالة لضبط إزاحة المحتوى تحت الشريط العلوي على الشاشات الصغيرة فقط =====
function adjustNavbarOffset() {
    try {
        const navbar = document.querySelector('.navbar.fixed-top');
        const pageContainer = document.querySelector('.container-fluid.page-container');
        if (!pageContainer) return;

        // قياس الارتفاع الفعلي للنافبار
        const navHeight = navbar ? navbar.getBoundingClientRect().height : 0;

        // نطبق الإزاحة فقط عندما يكون العرض <= 768px
        if (window.innerWidth <= 768) {
            // إضافة مسافة إضافية 32px لضمان عدم تغطية الأزرار
            const offset = Math.ceil(navHeight + 32);
            // نستخدم !important لتجاوز قواعد CSS الحالية
            pageContainer.style.setProperty('margin-top', offset + 'px', 'important');
        } else {
            // لا نغير وضع سطح المكتب
            pageContainer.style.removeProperty('margin-top');
        }
    } catch (e) {
        console.warn('adjustNavbarOffset failed:', e);
    }
}

// ===== إدارة النوافذ المنبثقة للمرفقات =====
function initializeAttachmentModals() {
    // إصلاح مشاكل z-index لجميع النوافذ المنبثقة
    document.querySelectorAll('.modal').forEach(function(modal) {
        modal.addEventListener('show.bs.modal', function() {
            // تأكيد أن النافذة تظهر فوق كل شيء
            this.style.zIndex = '10500';

            // إصلاح backdrop
            setTimeout(() => {
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.style.zIndex = '10499';
                }
            }, 100);
        });

        modal.addEventListener('shown.bs.modal', function() {
            console.log('تم فتح modal:', this.id);
            
            // التأكد من أن جميع العناصر قابلة للنقر
            const allElements = this.querySelectorAll('*');
            allElements.forEach(element => {
                element.style.pointerEvents = 'auto';
            });
            
            // التأكد من أن الأزرار قابلة للنقر
            const buttons = this.querySelectorAll('.btn');
            buttons.forEach(btn => {
                btn.style.pointerEvents = 'auto';
                btn.style.position = 'relative';
                btn.style.zIndex = '10504';
                btn.style.cursor = 'pointer';
                
                // إضافة معالج للنقر إذا لم يكن موجوداً
                if (!btn.hasAttribute('data-click-handler-added')) {
                    btn.addEventListener('click', function(e) {
                        console.log('تم النقر على زر:', this.textContent.trim());
                        // السماح للحدث بالمرور بشكل طبيعي
                    });
                    btn.setAttribute('data-click-handler-added', 'true');
                }
            });
            
            // إصلاح عناصر الإدخال
            const inputs = this.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.style.pointerEvents = 'auto';
                input.style.zIndex = '10504';
            });
            
            // إصلاح مناطق الرفع
            const uploadAreas = this.querySelectorAll('.upload-area');
            uploadAreas.forEach(area => {
                area.style.pointerEvents = 'auto';
                area.style.cursor = 'pointer';
                area.style.zIndex = '10503';
            });
            
            // التأكد من تحميل الصورة بشكل صحيح وإضافة معالج للصور التي تفشل في التحميل
            const imgElement = this.querySelector('img');
            if (imgElement) {
                imgElement.style.display = 'inline-block';
                imgElement.onerror = function() {
                    console.error('فشل تحميل الصورة:', this.src);
                    this.src = '/static/img/image-error.png'; // صورة بديلة في حالة الفشل
                    console.log('تم عرض صورة بديلة بسبب فشل تحميل الصورة الأصلية');
                };
            }
        });

        modal.addEventListener('hidden.bs.modal', function() {
            // إعادة تعيين z-index
            this.style.zIndex = '';
        });
    });

    // تم إزالة المعالج المخصص لفتح النوافذ المنبثقة للسماح لـ Bootstrap بالتعامل معها
    // هذا يمنع إنشاء مثيلات متعددة من النوافذ المنبثقة ويحل مشكلة التجميد
    // document.querySelectorAll('[data-bs-toggle="modal"]').forEach(function(button) {
    //     button.addEventListener('click', function(e) {
    //         e.preventDefault();
    //         e.stopPropagation();
    //
    //         const targetModal = document.querySelector(this.getAttribute('data-bs-target'));
    //         if (targetModal) {
    //             const modal = new bootstrap.Modal(targetModal, {
    //                 backdrop: true,
    //                 keyboard: true,
    //                 focus: true
    //             });
    //             modal.show();
    //         }
    //     });
    // });

    // معالج خاص لأزرار الطباعة في النوافذ المنبثقة
    document.querySelectorAll('[id^="imageModal"] .btn-primary, [id^="pdfModal"] .btn-primary').forEach(function(printBtn) {
        printBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            // السماح للرابط بالعمل بشكل طبيعي
            return true;
        });
    });

    // إضافة معالج لضمان إغلاق النوافذ المنبثقة بشكل صحيح
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
    });

    // إضافة معالج للنقر خارج النافذة المنبثقة
    document.querySelectorAll('[id^="imageModal"], [id^="pdfModal"]').forEach(function(modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                const modalInstance = bootstrap.Modal.getInstance(this);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        });
        
        // إضافة معالج خاص لأزرار الإغلاق لمنع التجميد
        const closeButton = modal.querySelector('.btn-close');
        if (closeButton) {
            closeButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // إزالة backdrop يدوياً لمنع التجميد
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop && backdrop.parentNode) {
                    backdrop.parentNode.removeChild(backdrop);
                }
                
                // إغلاق النافذة المنبثقة
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
                
                // إعادة تعيين حالة الصفحة
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
            });
        }
    });
}

// دالة مساعدة لفتح النوافذ المنبثقة برمجياً
function openAttachmentModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const modalInstance = new bootstrap.Modal(modal, {
            backdrop: true,
            keyboard: true,
            focus: true
        });
        modalInstance.show();
    }
}
