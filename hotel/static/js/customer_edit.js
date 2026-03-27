// Customer Edit Page - Document Management
// This file contains all the JavaScript functionality for the customer edit page

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const documentForm = document.getElementById('documentForm');
    const documentFileInput = document.getElementById('document_file');
    const documentPreview = document.getElementById('documentPreview');
    const noFileMessage = document.getElementById('noFileMessage');
    const scannerModal = document.getElementById('scannerModal');
    const scannerVideo = document.getElementById('scannerVideo');
    const scannerCanvas = document.getElementById('scannerCanvas');
    const captureBtn = document.getElementById('captureBtn');
    const useImageBtn = document.getElementById('useImageBtn');
    const resetScannerBtn = document.getElementById('resetScannerBtn');
    const removeDocBtn = document.getElementById('removeDocBtn');
    const downloadDocBtn = document.getElementById('downloadDocBtn');
    const printDocBtn = document.getElementById('printDocBtn');
    const scannerStatus = document.getElementById('scannerStatus');

    // State
    let stream = null;
    let currentDocument = {
        url: null,
        type: null,
        name: ''
    };

    // Initialize the page
    function init() {
        setupEventListeners();
        updateUIState();
    }

    // Set up event listeners
    function setupEventListeners() {
        // Document file input change
        if (documentFileInput) {
            documentFileInput.addEventListener('change', handleFileUpload);
        }

        // Scanner modal events
        if (scannerModal) {
            scannerModal.addEventListener('hidden.bs.modal', stopCamera);
            scannerModal.addEventListener('show.bs.modal', startScanner);
        }

        // Scanner buttons
        if (captureBtn) captureBtn.addEventListener('click', captureImage);
        if (useImageBtn) useImageBtn.addEventListener('click', useCapturedImage);
        if (resetScannerBtn) resetScannerBtn.addEventListener('click', resetScanner);
        if (removeDocBtn) removeDocBtn.addEventListener('click', removeDocument);
        if (downloadDocBtn) downloadDocBtn.addEventListener('click', downloadDocument);
        if (printDocBtn) printDocBtn.addEventListener('click', printDocument);
    }

    // Update UI state based on current document
    function updateUIState() {
        const hasDocument = !!currentDocument.url;
        
        if (noFileMessage) {
            noFileMessage.style.display = hasDocument ? 'none' : 'block';
        }
        
        if (documentPreview) {
            documentPreview.style.display = hasDocument ? 'block' : 'none';
        }
        
        // Enable/disable action buttons
        const actionButtons = [removeDocBtn, downloadDocBtn, printDocBtn];
        actionButtons.forEach(btn => {
            if (btn) btn.disabled = !hasDocument;
        });
    }

    // Handle file upload
    function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file type
        const validImageTypes = ['image/jpeg', 'image/png', 'image/gif'];
        const validPdfTypes = ['application/pdf'];
        
        if (!validImageTypes.includes(file.type) && !validPdfTypes.includes(file.type)) {
            showStatus('نوع الملف غير مدعوم. يرجى رفع صورة أو ملف PDF', 'error');
            e.target.value = ''; // Clear the file input
            return;
        }

        const fileType = file.type.startsWith('image/') ? 'image' : 'pdf';
        const fileUrl = URL.createObjectURL(file);
        
        currentDocument = {
            url: fileUrl,
            type: fileType,
            name: file.name,
            file: file  // حفظ كائن الملف الأصلي للاستخدام لاحقاً
        };

        // Show loading state
        if (noFileMessage) {
            noFileMessage.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">جاري التحميل...</span></div><p class="mt-2">جاري معالجة الملف...</p>';
            noFileMessage.style.display = 'block';
        }
        
        // Small delay to allow UI to update
        setTimeout(() => {
            updateDocumentPreview(fileUrl, fileType);
            updateUIState();
            showStatus('تم تحميل الملف بنجاح', 'success');
            
            // إرسال الملف تلقائياً بعد المعاينة
            uploadDocument(file);
        }, 100);
    }
    
    // Upload document to server
    function uploadDocument(file) {
        if (!file) return;
        
        const formData = new FormData();
        formData.append('document_file', file);
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
                showStatus('تم حفظ الوثيقة بنجاح', 'success');
                // تحديث رابط المستند إذا تم تغيير اسم الملف
                if (data.document_url) {
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
        });
    }

    // Start scanner (webcam)
    async function startScanner() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'environment' 
                } 
            });
            
            if (scannerVideo) {
                scannerVideo.srcObject = stream;
                scannerStatus.textContent = 'جاري التشغيل';
            }
        } catch (err) {
            console.error('Error accessing camera:', err);
            showStatus('فشل في الوصول إلى الكاميرا', 'error');
        }
    }

    // Capture image from camera
    function captureImage() {
        if (!scannerVideo || !scannerCanvas) return;
        
        const context = scannerCanvas.getContext('2d');
        context.drawImage(scannerVideo, 0, 0, scannerCanvas.width, scannerCanvas.height);
        
        // Show the capture button and hide the video
        scannerVideo.style.display = 'none';
        scannerCanvas.style.display = 'block';
        captureBtn.style.display = 'none';
        useImageBtn.style.display = 'inline-block';
        resetScannerBtn.style.display = 'inline-block';
        
        showStatus('تم التقاط الصورة بنجاح', 'success');
    }

    // Use the captured image
    function useCapturedImage() {
        if (!scannerCanvas) return;
        
        scannerCanvas.toBlob((blob) => {
            const fileUrl = URL.createObjectURL(blob);
            
            currentDocument = {
                url: fileUrl,
                type: 'image',
                name: 'document_' + new Date().getTime() + '.jpg'
            };
            
            updateDocumentPreview(fileUrl, 'image');
            updateUIState();
            
            // Close the scanner modal
            const modal = bootstrap.Modal.getInstance(scannerModal);
            if (modal) modal.hide();
            
            showStatus('تم تحميل الصورة بنجاح', 'success');
        }, 'image/jpeg', 0.9);
    }

    // Reset scanner
    function resetScanner() {
        if (scannerVideo) {
            scannerVideo.style.display = 'block';
            scannerVideo.srcObject = stream;
        }
        
        if (scannerCanvas) {
            scannerCanvas.style.display = 'none';
            const context = scannerCanvas.getContext('2d');
            context.clearRect(0, 0, scannerCanvas.width, scannerCanvas.height);
        }
        
        if (captureBtn) captureBtn.style.display = 'inline-block';
        if (useImageBtn) useImageBtn.style.display = 'none';
        if (resetScannerBtn) resetScannerBtn.style.display = 'none';
    }
}

// Remove document
function removeDocument() {
    if (!confirm('هل أنت متأكد من حذف هذه الوثيقة؟')) {
        return;
    }
    
    // إظهار حالة التحميل
    showStatus('جاري حذف الوثيقة...', 'info');
    
    // إرسال طلب حذف الوثيقة إلى الخادم
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
            // تحرير الذاكرة
            if (currentDocument.url) {
                URL.revokeObjectURL(currentDocument.url);
            }
            
            // إعادة تعيين حالة المستند
            currentDocument = { url: null, type: null, name: '', file: null };
            
            // إعادة تعيين حقل رفع الملف
            if (documentFileInput) {
                documentFileInput.value = '';
            }
            
            // إخفاء المعاينة وإظهار رسالة عدم وجود ملف
            if (documentPreview) {
                documentPreview.innerHTML = '';
                documentPreview.classList.add('d-none');
            }
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        padding: 20px;
                        text-align: center;
                    }
                    img, iframe { 
                        max-width: 100%; 
                        height: auto;
                        margin: 0 auto;
                        display: block;
                    }
                    @media print {
                        .no-print { display: none; }
                        body { padding: 0; }
                    }
                </style>
            </head>
            <body>
                <h2>${document.title}</h2>
                <p>${new Date().toLocaleString()}</p>
                ${currentDocument.type === 'image' 
                    ? `<img src="${currentDocument.url}" alt="Document">` 
                    : `<iframe src="${currentDocument.url}" style="width: 100%; height: 90vh; border: none;"></iframe>`
                }
                <div class="no-print" style="margin-top: 20px;">
                    <button onclick="window.print()">طباعة</button>
                    <button onclick="window.close()">إغلاق</button>
                </div>
            </body>
            </html>
        `);
        
        printWindow.document.close();
        
        // Auto-print after a short delay to ensure content is loaded
        setTimeout(() => {
            printWindow.print();
        }, 500);
    }

    // Update document preview
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
            
            // تحديث زر المعاينة ليفتح الصورة في نافذة جديدة
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
            
            // إضافة معاينة PDF باستخدام iframe
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
                
                // تحديث زر المعاينة ليفتح PDF في نافذة جديدة
                if (viewDocumentBtn) {
                    viewDocumentBtn.href = url;
                    viewDocumentBtn.target = '_blank';
                    viewDocumentBtn.removeAttribute('data-lightbox');
                }
                
            } catch (e) {
                console.error('خطأ في تحميل معاينة PDF:', e);
            }
        }
        
        documentPreview.appendChild(previewContainer);
        
        // إظهار حاوية المعاينة وإخفاء رسالة عدم وجود ملف
        documentPreview.classList.remove('d-none');
        if (noFileMessage) {
            noFileMessage.style.display = 'none';
        }
        
        // تفعيل أزرار التحكم
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
                
                // تحديث روابط التحميل والمعاينة إذا كانت موجودة
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
        
        // إظهار أو إخفاء رسالة عدم وجود ملف
        if (noFileMessage) {
            noFileMessage.style.display = hasDocument ? 'none' : 'block';
        }
        
        // إظهار أو إخفاء معاينة المستند
        if (documentPreview) {
            documentPreview.style.display = hasDocument ? 'block' : 'none';
        }
    }
    
    // Show preview error message
    function showPreviewError(message) {
        if (!documentPreview) return;
        
        documentPreview.innerHTML = `
            <div class="alert alert-danger text-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
        documentPreview.style.display = 'block';
        if (noFileMessage) {
            noFileMessage.style.display = 'none';
        }
    }

    // Show status message
    function showStatus(message, type = 'info') {
        if (!scannerStatus) return;
        
        scannerStatus.textContent = message;
        scannerStatus.className = 'badge ' + (
            type === 'error' ? 'bg-danger' :
            type === 'success' ? 'bg-success' : 'bg-primary'
        );
        
        // Auto-clear status after 3 seconds
        setTimeout(() => {
            scannerStatus.textContent = 'جاهز';
            scannerStatus.className = 'badge bg-primary';
        }, 3000);
    }

    // Initialize the page
    init();
});

// Toggle nationality input field based on selection
function toggleNationalityInput() {
    const nationalitySelect = document.getElementById('nationality-select');
    const nationalityOtherDiv = document.getElementById('nationality-other-div');
    const nationalityOtherInput = document.getElementById('nationality-other-input');
    
    if (!nationalitySelect || !nationalityOtherDiv || !nationalityOtherInput) return;
    
    if (nationalitySelect.value === 'other') {
        nationalityOtherDiv.style.display = 'block';
        nationalityOtherInput.required = true;
    } else {
        nationalityOtherDiv.style.display = 'none';
        nationalityOtherInput.required = false;
        nationalityOtherInput.value = '';
    }
}

// Initialize the nationality input when the page loads
document.addEventListener('DOMContentLoaded', function() {
    toggleNationalityInput();
});
