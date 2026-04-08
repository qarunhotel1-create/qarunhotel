// دوال البحث والفلترة للعملاء

// دالة تأخير التنفيذ لتحسين الأداء
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// دالة عرض التنبيهات
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

// دالة إضافة وثيقة سريعة
window.quickAddDocument = function(customerId) {
    const modal = document.getElementById('quickAddDocModal');
    if (modal) {
        const customerIdInput = modal.querySelector('#quickAddCustomerId');
        if (customerIdInput) {
            customerIdInput.value = customerId;
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }
};

// تهيئة الصفحة عند التحميل
document.addEventListener('DOMContentLoaded', function() {
    // عناصر DOM
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const nationalityFilter = document.getElementById('nationalityFilter');
    const documentsFilter = document.getElementById('documentsFilter');
    const sortBy = document.getElementById('sortBy');
    const cardViewBtn = document.getElementById('cardViewBtn');
    const tableViewBtn = document.getElementById('tableViewBtn');
    const cardView = document.getElementById('cardView');
    const tableView = document.getElementById('tableView');
    const searchStatusContainer = document.getElementById('searchStatusContainer');
    
    // دالة فلترة العملاء
    function filterCustomers() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const nationalityValue = nationalityFilter ? nationalityFilter.value : '';
        const documentsValue = documentsFilter ? documentsFilter.value : '';
        
        // الحصول على حاوية حالة البحث
        if (searchStatusContainer) {
            const searchStatusSpan = searchStatusContainer.querySelector('span');
            
            // عرض حالة البحث إذا كان هناك مصطلح بحث
            if (searchTerm || nationalityValue || documentsValue !== '') {
                searchStatusContainer.classList.remove('d-none');
                if (searchStatusSpan) searchStatusSpan.textContent = 'جاري البحث...';
            } else {
                searchStatusContainer.classList.add('d-none');
            }
        }
        
        // فلترة الجدول
        const customerRows = document.querySelectorAll('.customer-row');
        let visibleCount = 0;
        
        customerRows.forEach(row => {
            const name = row.dataset.name.toLowerCase();
            const id = row.dataset.id.toLowerCase();
            const nationality = row.dataset.nationality;
            const hasDocs = row.dataset.hasDocs === 'true';
            
            let show = true;
            
            if (searchTerm && !name.includes(searchTerm) && !id.includes(searchTerm)) {
                show = false;
            }
            
            if (nationalityValue && nationality !== nationalityValue) {
                show = false;
            }
            
            if (documentsValue === 'with_docs' && !hasDocs) {
                show = false;
            } else if (documentsValue === 'without_docs' && hasDocs) {
                show = false;
            }
            
            row.style.display = show ? 'table-row' : 'none';
            if (show) visibleCount++;
        });
        
        // تحديث حالة البحث
        if (searchStatusContainer && (searchTerm || nationalityValue || documentsValue !== '')) {
            const searchStatusSpan = searchStatusContainer.querySelector('span');
            if (searchStatusSpan) {
                searchStatusSpan.textContent = `تم العثور على ${visibleCount} عميل`;
            }
        }
        
        // إظهار رسالة إذا لم يتم العثور على نتائج
        const noResultsMessage = document.getElementById('noResultsMessage');
        if (noResultsMessage) {
            if (visibleCount === 0 && (searchTerm || nationalityValue || documentsValue !== '')) {
                noResultsMessage.classList.remove('d-none');
            } else {
                noResultsMessage.classList.add('d-none');
            }
        }
    }
    
    // دالة ترتيب العملاء
    function sortCustomers() {
        if (!sortBy) return;
        
        const sortValue = sortBy.value;
        const customersGrid = document.getElementById('customersGrid');
        const customersTable = document.getElementById('customersTable');
        
        if (customersGrid) {
            const cards = Array.from(customersGrid.children);
            cards.sort((a, b) => {
                switch (sortValue) {
                    case 'name_asc':
                        return a.dataset.name.localeCompare(b.dataset.name, 'ar');
                    case 'name_desc':
                        return b.dataset.name.localeCompare(a.dataset.name, 'ar');
                    case 'oldest':
                        return parseInt(a.dataset.id) - parseInt(b.dataset.id);
                    case 'newest':
                    default:
                        return parseInt(b.dataset.id) - parseInt(a.dataset.id);
                }
            });
            
            cards.forEach(card => customersGrid.appendChild(card));
        }
        
        if (customersTable) {
            const rows = Array.from(customersTable.children);
            rows.sort((a, b) => {
                switch (sortValue) {
                    case 'name_asc':
                        return a.dataset.name.localeCompare(b.dataset.name, 'ar');
                    case 'name_desc':
                        return b.dataset.name.localeCompare(a.dataset.name, 'ar');
                    case 'oldest':
                        return parseInt(a.dataset.id) - parseInt(b.dataset.id);
                    case 'newest':
                    default:
                        return parseInt(b.dataset.id) - parseInt(a.dataset.id);
                }
            });
            
            rows.forEach(row => customersTable.appendChild(row));
        }
    }
    
    // دالة رفع الوثائق السريعة
    function uploadQuickDocuments(customerId, files) {
        const formData = new FormData();
        formData.append('customer_id', customerId);
        
        Array.from(files).forEach(file => {
            formData.append('documents', file);
        });
        
        fetch('/customers-new/api/upload-documents', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
                const quickAddDocModal = document.getElementById('quickAddDocModal');
                if (quickAddDocModal) {
                    const bsModal = bootstrap.Modal.getInstance(quickAddDocModal);
                    if (bsModal) bsModal.hide();
                }
                // إعادة تحميل الصفحة لتحديث الإحصائيات
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                showAlert(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('حدث خطأ في رفع الوثائق', 'error');
        });
    }
    
    // إعداد أزرار العرض
    function setupViewButtons() {
        if (cardViewBtn && tableViewBtn && cardView && tableView) {
            cardViewBtn.addEventListener('click', function() {
                cardView.classList.remove('d-none');
                tableView.classList.add('d-none');
                cardViewBtn.classList.add('active');
                tableViewBtn.classList.remove('active');
                localStorage.setItem('customerViewMode', 'card');
            });
            
            tableViewBtn.addEventListener('click', function() {
                cardView.classList.add('d-none');
                tableView.classList.remove('d-none');
                cardViewBtn.classList.remove('active');
                tableViewBtn.classList.add('active');
                localStorage.setItem('customerViewMode', 'table');
            });
            
            // استعادة وضع العرض المحفوظ
            const savedViewMode = localStorage.getItem('customerViewMode');
            if (savedViewMode === 'card') {
                cardViewBtn.click();
            } else if (savedViewMode === 'table') {
                tableViewBtn.click();
            }
        }
    }
    
    // إعداد الإضافة السريعة للوثائق
    function setupQuickAdd() {
        const uploadDocBtn = document.getElementById('uploadDocBtn');
        const scanDocBtn = document.getElementById('scanDocBtn');
        const docFileInput = document.getElementById('docFileInput');
        
        if (uploadDocBtn && docFileInput) {
            uploadDocBtn.addEventListener('click', function() {
                docFileInput.click();
            });
            
            docFileInput.addEventListener('change', function() {
                const customerId = document.getElementById('quickAddCustomerId')?.value;
                if (customerId && this.files.length > 0) {
                    uploadQuickDocuments(customerId, this.files);
                }
            });
        }
        
        if (scanDocBtn) {
            scanDocBtn.addEventListener('click', function() {
                // تنفيذ وظيفة المسح الضوئي هنا
                alert('وظيفة المسح الضوئي غير متاحة حاليًا');
            });
        }
    }
    
    // تطبيق دالة debounce على البحث لتحسين الأداء
    const debouncedFilter = debounce(filterCustomers, 300);
    
    // ربط الأحداث
    if (searchInput) {
        searchInput.addEventListener('input', debouncedFilter);
    }
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            if (searchInput) searchInput.value = '';
            if (nationalityFilter) nationalityFilter.value = '';
            if (documentsFilter) documentsFilter.value = '';
            filterCustomers();
        });
    }
    if (nationalityFilter) {
        nationalityFilter.addEventListener('change', filterCustomers);
    }
    if (documentsFilter) {
        documentsFilter.addEventListener('change', filterCustomers);
    }
    if (sortBy) {
        sortBy.addEventListener('change', sortCustomers);
    }
    
    // إعداد أزرار العرض
    setupViewButtons();
    
    // إعداد الإضافة السريعة
    setupQuickAdd();
    
    // تنفيذ البحث الأولي عند تحميل الصفحة
    filterCustomers();
});