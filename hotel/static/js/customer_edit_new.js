document.addEventListener('DOMContentLoaded', function() {
    // Form submission handler
    const editForm = document.querySelector('form[data-customer-id]');
    if (editForm) {
        editForm.addEventListener('submit', handleFormSubmit);
    }
    // DOM Elements
    const documentFileInput = document.getElementById('document_file');
    const documentPreview = document.getElementById('documentPreview');
    const noFileMessage = document.getElementById('noFileMessage');
    const viewDocumentBtn = document.getElementById('viewDocumentBtn');
    const downloadDocumentBtn = document.getElementById('downloadDocumentBtn');
    const removeDocumentBtn = document.getElementById('removeDocumentBtn');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = uploadProgress ? uploadProgress.querySelector('.progress-bar') : null;
    
    // Current document state
    let currentDocument = {
        url: null,
        type: null,
        name: '',
        file: null
    };

    // Initialize
    function init() {
        // Load existing document if any
        const existingDoc = document.querySelector('[data-document-url]');
        if (existingDoc) {
            const docUrl = existingDoc.getAttribute('data-document-url');
            const docType = existingDoc.getAttribute('data-document-type') || 'image';
            const docName = existingDoc.getAttribute('data-document-name') || 'document';
            
            currentDocument = {
                url: docUrl,
                type: docType,
                name: docName,
                file: null
            };
            
            updateDocumentPreview(docUrl, docType);
            updateDocumentActions();
        }
        
        // Event Listeners
        if (documentFileInput) {
            documentFileInput.addEventListener('change', handleFileUpload);
        }
        
        if (removeDocumentBtn) {
            removeDocumentBtn.addEventListener('click', removeDocument);
        }
        
        if (viewDocumentBtn) {
            viewDocumentBtn.addEventListener('click', function(e) {
                if (!currentDocument.url) e.preventDefault();
            });
        }
        
        if (downloadDocumentBtn) {
            downloadDocumentBtn.addEventListener('click', function(e) {
                if (!currentDocument.url) e.preventDefault();
            });
        }
    }
    
    // Handle file upload
    function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        // دعم أنواع الصور وPDF فقط
        const validImageTypes = ['image/jpeg', 'image/png', 'image/gif'];
        const validPdfTypes = ['application/pdf'];
        if (!validImageTypes.includes(file.type) && !validPdfTypes.includes(file.type)) {
            showStatus('نوع الملف غير مدعوم. يرجى رفع صورة أو ملف PDF', 'error');
            e.target.value = '';
            return;
        }

        const fileType = file.type.startsWith('image/') ? 'image' : 'pdf';
        const fileUrl = URL.createObjectURL(file);
        currentDocument = {
            url: fileUrl,
            type: fileType,
            name: file.name,
            file: file
        };

        // إظهار المعاينة مباشرة
        updateDocumentPreview(fileUrl, fileType);
        updateDocumentActions();
        showStatus('تم تحميل الملف بنجاح', 'success');

        // توليد data_url وتحديث الحقل المخفي newDocumentsData
        const reader = new FileReader();
        reader.onload = function(event) {
            const dataUrl = event.target.result;
            const docObj = {
                name: file.name,
                size: file.size,
                type: file.type,
                data: dataUrl,
                method: 'upload'
            };
            let docs = [];
            try {
                const val = document.getElementById('newDocumentsData').value;
                if (val) docs = JSON.parse(val);
            } catch (err) { docs = []; }
            docs = [docObj]; // حالياً وثيقة واحدة، يمكن دعم التعدد لاحقاً
            document.getElementById('newDocumentsData').value = JSON.stringify(docs);
        };
        reader.readAsDataURL(file);
    }
    
    // Upload document to server
    function uploadDocument(file) {
        if (!file) return;
        
        const formData = new FormData();
        formData.append('document_file', file);
        formData.append('customer_id', document.querySelector('form').getAttribute('data-customer-id'));
        
        // Show upload progress
        if (uploadProgress) {
            uploadProgress.classList.remove('d-none');
        }
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', 0);
        }
        
        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus('تم حفظ الوثيقة بنجاح', 'success');
                // Update document URL if filename was changed
                if (data.document_url) {
                    // Revoke old URL to free memory
                    if (currentDocument.url) {
                        URL.revokeObjectURL(currentDocument.url);
                    }
                    
                    currentDocument.url = data.document_url;
                    currentDocument.name = data.document_filename || file.name;
                    updateDocumentPreview(data.document_url, file.type.startsWith('image/') ? 'image' : 'pdf');
                }
            } else {
                showStatus(data.message || 'حدث خطأ أثناء رفع الملف', 'error');
            }
        })
        .catch(error => {
            console.error('Error uploading document:', error);
            showStatus('حدث خطأ في اتصال الشبكة', 'error');
        })
        .finally(() => {
            if (uploadProgress) {
                uploadProgress.classList.add('d-none');
            }
        });
    }
    
    // Update document preview
    // تحديث المعاينة بشكل فوري بعد رفع الملف
    function updateDocumentPreview(url, type) {
        if (!documentPreview) return;
        
        // Clear previous preview
        documentPreview.innerHTML = '';
        
        // Create preview container
        const previewContainer = document.createElement('div');
        previewContainer.className = 'document-preview-container';
        
        if (type === 'image') {
            const imgContainer = document.createElement('div');
            imgContainer.className = 'text-center';
            
            const img = document.createElement('img');
            img.src = url;
            img.className = 'img-fluid img-thumbnail';
            img.alt = 'معاينة الوثيقة';
            img.style.maxHeight = '400px';
            img.style.maxWidth = '100%';
            img.style.margin = '0 auto';
            img.style.display = 'block';
            
            img.onerror = function() {
                showPreviewError('خطأ في تحميل الصورة');
            };
            
            imgContainer.appendChild(img);
            previewContainer.appendChild(imgContainer);
            
            // Update view button
            if (viewDocumentBtn) {
                viewDocumentBtn.href = url;
                viewDocumentBtn.setAttribute('data-lightbox', 'document-preview');
                viewDocumentBtn.setAttribute('data-title', 'معاينة الوثيقة');
            }
            
        } else if (type === 'pdf') {
            const pdfContainer = document.createElement('div');
            pdfContainer.className = 'text-center p-3';
            
            const pdfIcon = document.createElement('i');
            pdfIcon.className = 'fas fa-file-pdf fa-4x text-danger mb-3';
            
            const pdfName = document.createElement('div');
            pdfName.className = 'mb-3 text-truncate';
            pdfName.textContent = currentDocument.name || 'document.pdf';
            pdfName.style.maxWidth = '300px';
            pdfName.style.margin = '0 auto';
            
            const btnGroup = document.createElement('div');
            btnGroup.className = 'btn-group';
            
            const viewBtn = document.createElement('a');
            viewBtn.href = url;
            viewBtn.className = 'btn btn-outline-primary btn-sm';
            viewBtn.target = '_blank';
            viewBtn.innerHTML = '<i class="fas fa-eye me-1"></i> معاينة';
            
            const downloadBtn = document.createElement('a');
            downloadBtn.href = url;
            downloadBtn.className = 'btn btn-outline-success btn-sm';
            downloadBtn.download = currentDocument.name || 'document.pdf';
            downloadBtn.innerHTML = '<i class="fas fa-download me-1"></i> تحميل';
            
            btnGroup.appendChild(viewBtn);
            btnGroup.appendChild(downloadBtn);
            
            pdfContainer.appendChild(pdfIcon);
            pdfContainer.appendChild(pdfName);
            pdfContainer.appendChild(btnGroup);
            previewContainer.appendChild(pdfContainer);
            
            // Try to show PDF preview
            try {
                const pdfPreviewContainer = document.createElement('div');
                pdfPreviewContainer.className = 'mt-3 border rounded';
                pdfPreviewContainer.style.overflow = 'hidden';
                
                const pdfPreview = document.createElement('iframe');
                pdfPreview.src = url + '#toolbar=0&navpanes=0&scrollbar=0';
                pdfPreview.width = '100%';
                pdfPreview.height = '500px';
                pdfPreview.style.border = 'none';
                
                pdfPreviewContainer.appendChild(pdfPreview);
                previewContainer.appendChild(pdfPreviewContainer);
                
                // Update view button
                if (viewDocumentBtn) {
                    viewDocumentBtn.href = url;
                    viewDocumentBtn.target = '_blank';
                    viewDocumentBtn.removeAttribute('data-lightbox');
                }
                
            } catch (e) {
                console.error('Error loading PDF preview:', e);
            }
        }
        
        documentPreview.appendChild(previewContainer);
        
        // Show preview and hide no file message
        documentPreview.classList.remove('d-none');
        if (noFileMessage) {
            noFileMessage.style.display = 'none';
        }
        
        // Update action buttons
        updateDocumentActions();
    }
    
    // Update document action buttons
    function updateDocumentActions() {
        const hasDocument = !!currentDocument.url;
        const actionButtons = [
            document.getElementById('viewDocumentBtn'),
            document.getElementById('downloadDocumentBtn'),
            document.getElementById('removeDocumentBtn')
        ];
        
        actionButtons.forEach(btn => {
            if (btn) {
                btn.disabled = !hasDocument;
                
                // Update view/download links if they exist
                if (hasDocument && currentDocument.url) {
                    if (btn.id === 'viewDocumentBtn' || btn.id === 'downloadDocumentBtn') {
                        btn.href = currentDocument.url;
                        if (btn.id === 'downloadDocumentBtn') {
                            btn.download = currentDocument.name || 'document';
                        }
                    }
                }
            }
        });
        
        // Show/hide no file message
        if (noFileMessage) {
            noFileMessage.style.display = hasDocument ? 'none' : 'block';
        }
        
        // Show/hide document preview
        if (documentPreview) {
            documentPreview.style.display = hasDocument ? 'block' : 'none';
        }
    }
    
    // Remove document
    function removeDocument() {
        if (!confirm('هل أنت متأكد من حذف هذه الوثيقة؟')) {
            return;
        }
        
        // Show loading state
        showStatus('جاري حذف الوثيقة...', 'info');
        
        // Send delete request to server
        const formData = new FormData();
        formData.append('action', 'delete_document');
        formData.append('customer_id', document.querySelector('form').getAttribute('data-customer-id'));
        
        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Free memory
                if (currentDocument.url) {
                    URL.revokeObjectURL(currentDocument.url);
                }
                
                // Reset document state
                currentDocument = { url: null, type: null, name: '', file: null };
                
                // Reset file input
                if (documentFileInput) {
                    documentFileInput.value = '';
                }
                
                // Hide preview and show no file message
                if (documentPreview) {
                    documentPreview.innerHTML = '';
                    documentPreview.classList.add('d-none');
                }
                
                if (noFileMessage) {
                    noFileMessage.style.display = 'block';
                    noFileMessage.innerHTML = `
                        <i class="fas fa-file-upload fa-3x text-muted mb-3"></i>
                        <p class="text-muted mb-0">لم يتم رفع أي وثيقة بعد</p>
                        <p class="text-muted small mt-2">يُسمح بملفات الصور (JPG, PNG) أو ملفات PDF</p>
                    `;
                }
                
                // Update UI
                updateDocumentActions();
                showStatus('تم حذف الوثيقة بنجاح', 'success');
            } else {
                showStatus(data.message || 'حدث خطأ أثناء حذف الوثيقة', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting document:', error);
            showStatus('حدث خطأ في اتصال الشبكة', 'error');
        });
    }
    
    // Show status message
    function showStatus(message, type = 'info') {
        // You can implement a status message system here
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Example: Show a toast notification
        const toastContainer = document.getElementById('toastContainer');
        if (toastContainer) {
            const toastId = 'status-toast-' + Date.now();
            const toastHtml = `
                <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">
                            ${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>
            `;
            
            const toastEl = document.createElement('div');
            toastEl.innerHTML = toastHtml.trim();
            const toastNode = toastEl.firstChild;
            
            toastContainer.appendChild(toastNode);
            
            const toast = new bootstrap.Toast(toastNode, {
                autohide: true,
                delay: 5000
            });
            
            toast.show();
            
            // Remove toast after it's hidden
            toastNode.addEventListener('hidden.bs.toast', function() {
                toastNode.remove();
            });
        }
    }
    
    // Show preview error message
    function showPreviewError(message) {
        if (!documentPreview) return;
        
        documentPreview.innerHTML = `
            <div class="alert alert-danger text-center" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
        
        documentPreview.classList.remove('d-none');
        
        if (noFileMessage) {
            noFileMessage.style.display = 'none';
        }
    }
    
    // Initialize the document preview system
    init();
    
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
    
    // إضافة معالج حدث لزر المسح الضوئي
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
                
                if (!response.ok) {
                    throw new Error('فشل الاتصال بوكيل المسح - تأكد من توصيل الماسح الضوئي وتشغيله');
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
                    alert(
                        'تعليمات تشغيل وكيل المسح الضوئي:\n\n' +
                        '1. تأكد من تشغيل برنامج وكيل المسح الضوئي (Scanner Bridge)\n' +
                        '2. يمكنك تشغيله من خلال ملف start_scanner_bridge.bat في مجلد النظام\n' +
                        '3. تأكد من توصيل طابعة Kyocera FS-3540MFP KX بالكمبيوتر\n' +
                        '4. تأكد من تثبيت برنامج Python على الكمبيوتر\n' +
                        '5. حاول مرة أخرى بعد التأكد من الخطوات السابقة'
                    );
                }
                
                // استخدام محاكاة للمسح الضوئي
                usedSimulation = true;
                
                // إنشاء صورة محاكاة بسيطة (مستطيل أبيض مع نص)
                const canvas = document.createElement('canvas');
                canvas.width = 1240;
                canvas.height = 1754;
                const ctx = canvas.getContext('2d');
                
                // خلفية بيضاء
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // إضافة نص
                ctx.fillStyle = 'black';
                ctx.font = '24px Arial';
                const now = new Date().toLocaleString('ar-EG');
                ctx.fillText(`صفحة محاكاة - تم إنشاؤها في: ${now}`, 50, 50);
                ctx.fillText('(وكيل المسح الضوئي غير متوفر)', 50, 100);
                ctx.fillText(`خطأ: ${scanError.message}`, 50, 150);
                
                // تحويل الصورة إلى base64
                scannedImage = canvas.toDataURL('image/jpeg').split(',')[1];
            }
            
            // استخدام الصورة الممسوحة
            const fileName = `scan_${new Date().getTime()}.jpg`;
            
            // تحديث حالة الوثيقة الحالية
            currentDocument = {
                url: scannedImage,
                type: 'image',
                name: fileName,
                file: null
            };
            
            // إظهار المعاينة
            updateDocumentPreview(scannedImage, 'image');
            updateDocumentActions();
            
            // تحديث البيانات المخفية
            const docObj = {
                name: fileName,
                size: 0, // غير معروف
                type: 'image/jpeg',
                data: scannedImage,
                method: 'scan'
            };
            
            let docs = [];
            try {
                const val = document.getElementById('newDocumentsData').value;
                if (val) docs = JSON.parse(val);
            } catch (err) { docs = []; }
            
            docs = [docObj]; // حالياً وثيقة واحدة
            document.getElementById('newDocumentsData').value = JSON.stringify(docs);
            
            if (usedSimulation) {
                 showToast('تم إنشاء صورة محاكاة (وكيل المسح غير متوفر)', 'warning');
             } else {
                 showToast('تم المسح الضوئي بنجاح', 'success');
             }
        } catch (error) {
            console.error('خطأ في المسح الضوئي:', error);
            showStatus(`فشل المسح الضوئي: ${error.message}`, 'error');
        } finally {
            // إعادة الزر إلى حالته الطبيعية
            scanDocumentBtn.disabled = false;
            scanDocumentBtn.innerHTML = '<i class="fas fa-scanner me-2"></i>مسح ضوئي مباشر';
        }
    }

    // Handle form submission
    function handleFormSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton ? submitButton.innerHTML : '';
        
        // Show loading state
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جاري الحفظ...';
        }
        
        // First upload the document if a new one was selected
        const fileInput = document.getElementById('document_file');
        const file = fileInput.files[0];
        
        if (file) {
            // Handle file upload first
            uploadDocument(file)
                .then(fileData => {
                    // Once file is uploaded, submit the form with the file info
                    return submitForm(form, formData, fileData);
                })
                .catch(error => {
                    showStatus('حدث خطأ أثناء رفع الملف: ' + (error.message || 'خطأ غير معروف'), 'error');
                    throw error;
                })
                .finally(() => {
                    // Restore button state
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.innerHTML = originalButtonText;
                    }
                });
        } else {
            // No file to upload, just submit the form
            submitForm(form, formData)
                .finally(() => {
                    // Restore button state
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.innerHTML = originalButtonText;
                    }
                });
        }
    }
    
    // Helper function to submit the form
    function submitForm(form, formData, fileData = null) {
        // Add file data to form data if provided
        if (fileData && fileData.filename) {
            formData.set('document_filename', fileData.filename);
        }
        
        // Add CSRF token if needed
        const csrfToken = document.querySelector('input[name="csrf_token"]');
        if (csrfToken) {
            formData.set('csrf_token', csrfToken.value);
        }
        
        // Submit form via AJAX
        return fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showStatus(data.message || 'تم حفظ التغييرات بنجاح', 'success');
                if (data.redirect) {
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 1500);
                }
            } else {
                showStatus(data.message || 'حدث خطأ غير معروف', 'error');
            }
            return data;
        })
        .catch(error => {
            const errorMessage = error.message || 'حدث خطأ في الاتصال بالخادم';
            showStatus(errorMessage, 'error');
            throw error;
        });
    }
});
