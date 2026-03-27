// JavaScript محسن لصفحة إنشاء الحجز
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 تحميل صفحة الحجز المحسنة...');
    
    // العناصر الأساسية
    const customerSearch = document.getElementById('customerSearch');
    const customerSearchResults = document.getElementById('customerSearchResults');
    const selectedCustomerInfo = document.getElementById('selectedCustomerInfo');
    const customerDetails = document.getElementById('customerDetails');
    
    // عناصر الغرفة
    const roomSelect = document.getElementById('roomSelect');
    const roomAvailabilityMessage = document.getElementById('roomAvailabilityMessage');
    const selectedRoomInfo = document.getElementById('selectedRoomInfo');
    const roomDetails = document.getElementById('roomDetails');
    const occupancyTypeSection = document.getElementById('occupancyTypeSection');
    const occupancyType = document.getElementById('occupancyType');
    const occupancyPriceInfo = document.getElementById('occupancyPriceInfo');
    const discountSection = document.getElementById('discountSection');
    const discountPercentage = document.getElementById('discountPercentage');

    // عناصر الضريبة
    const includeTax = document.getElementById('includeTax');
    const taxRow = document.getElementById('taxRow');
    const afterDiscountAmount = document.getElementById('afterDiscountAmount');
    const taxAmount = document.getElementById('taxAmount');

    // عناصر الديوز
    const isDeus = document.getElementById('isDeus');
    
    // عناصر التواريخ
    const datesSection = document.getElementById('datesSection');
    const checkInDate = document.getElementById('checkInDate');
    const checkOutDate = document.getElementById('checkOutDate');
    const daysInfo = document.getElementById('daysInfo');
    const numberOfDays = document.getElementById('numberOfDays');
    
    // ملخص الحجز
    const finalBookingSummary = document.getElementById('finalBookingSummary');
    const summaryContent = document.getElementById('summaryContent');
    const baseAmount = document.getElementById('baseAmount');
    const discountAmount = document.getElementById('discountAmount');
    const totalAmount = document.getElementById('totalAmount');
    
    // بيانات الحجز
    let selectedCustomer = null;
    let selectedRoom = null;
    let currentPrice = 0;
    let currentDays = 0;
    let roomPrices = {};
    
    // إزالة قيود التاريخ - يمكن اختيار أي تاريخ
    // const today = new Date().toISOString().split('T')[0];
    // checkInDate.setAttribute('min', today);

    // ===== دوال مساعدة =====
    function updateStep(stepNumber, completed) {
        const step = document.getElementById(`step${stepNumber}`);
        if (step) {
            const badge = step.querySelector('.badge');
            const checkIcon = step.querySelector('.fas.fa-check');

            if (completed) {
                badge.className = 'badge bg-success rounded-pill me-2';
                checkIcon.style.display = 'inline';
            } else {
                badge.className = 'badge bg-secondary rounded-pill me-2';
                checkIcon.style.display = 'none';
            }
        }
    }

    function updateHiddenFields() {
        const hiddenCustomerId = document.getElementById('hiddenCustomerId');
        const hiddenRoomNumber = document.getElementById('hiddenRoomNumber');
        const hiddenOccupancyType = document.getElementById('hiddenOccupancyType');
        const hiddenCheckInDate = document.getElementById('hiddenCheckInDate');
        const hiddenCheckOutDate = document.getElementById('hiddenCheckOutDate');
        const hiddenDiscountPercentage = document.getElementById('hiddenDiscountPercentage');
        const hiddenIncludeTax = document.getElementById('hiddenIncludeTax');
        const hiddenIsDeus = document.getElementById('hiddenIsDeus');
        const hiddenNotes = document.getElementById('hiddenNotes');

        if (hiddenCustomerId && selectedCustomer) {
            hiddenCustomerId.value = selectedCustomer.id;
        }
        if (hiddenRoomNumber && selectedRoom) {
            hiddenRoomNumber.value = selectedRoom.number;
        }
        if (hiddenOccupancyType) {
            hiddenOccupancyType.value = occupancyType.value;
        }
        if (hiddenCheckInDate) {
            hiddenCheckInDate.value = checkInDate.value;
        }
        if (hiddenCheckOutDate) {
            hiddenCheckOutDate.value = checkOutDate.value;
        }
        if (hiddenDiscountPercentage) {
            hiddenDiscountPercentage.value = discountPercentage.value || 0;
        }
        if (hiddenIncludeTax) {
            hiddenIncludeTax.value = (includeTax && includeTax.checked) ? "1" : "0";
        }
        if (hiddenIsDeus) {
            hiddenIsDeus.value = (isDeus && isDeus.checked) ? "1" : "0";
        }
        if (hiddenNotes) {
            const notesField = document.getElementById('notes');
            hiddenNotes.value = notesField ? notesField.value : '';
        }
    }

    function calculateFinalTotal() {
        if (!currentPrice || !currentDays) return 0;

        const baseTotal = currentPrice * currentDays;
        const discountPercent = parseFloat(discountPercentage.value) || 0;
        const discountValue = (baseTotal * discountPercent) / 100;
        return baseTotal - discountValue;
    }
    
    // ===== البحث الجديد عن العملاء =====
    const newCustomerSearch = document.getElementById('newCustomerSearch');
    const newSearchResults = document.getElementById('newSearchResults');
    let newSearchTimeout;
    let selectedCustomerData = null;

    if (newCustomerSearch) {
        // البحث عند الكتابة
        newCustomerSearch.addEventListener('input', function() {
            const query = this.value.trim();
            console.log('🔍 البحث عن:', query);

            if (query.length === 0) {
                newSearchResults.innerHTML = '';
                return;
            }

            // عرض النتائج فوراً
            performNewSearch(query);
        });

        // عرض العميل الموجود عند التركيز على الحقل
        newCustomerSearch.addEventListener('focus', function() {
            if (this.value.trim() === '') {
                showAllCustomers();
            }
        });
    }

    function showAllCustomers() {
        console.log('📋 عرض جميع العملاء');

        // عرض مؤشر التحميل
        newSearchResults.innerHTML = '<div class="p-2 text-center"><i class="fas fa-spinner fa-spin"></i> جاري التحميل...</div>';

        // جلب جميع العملاء
        fetch('/bookings/new-search-customers')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('📊 جميع العملاء:', data);
                if (data.customers && data.customers.length > 0) {
                    displayNewSearchResults(data.customers);
                } else {
                    newSearchResults.innerHTML = '<div class="alert alert-info">لا يوجد عملاء مسجلين</div>';
                }
            })
            .catch(error => {
                console.error('❌ خطأ في جلب العملاء:', error);
                newSearchResults.innerHTML = '<div class="alert alert-danger">خطأ في جلب البيانات</div>';
            });
    }

    function performNewSearch(query) {
        console.log('🔍 تنفيذ البحث عن:', query);

        // عرض مؤشر التحميل
        newSearchResults.innerHTML = '<div class="p-2 text-center"><i class="fas fa-spinner fa-spin"></i> جاري البحث...</div>';

        // استدعاء API للبحث
        fetch(`/bookings/new-search-customers?q=${encodeURIComponent(query)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('📊 البيانات المستلمة:', data);
                if (data.customers && data.customers.length > 0) {
                    console.log('📋 عدد النتائج:', data.customers.length);
                    displayNewSearchResults(data.customers);
                } else {
                    newSearchResults.innerHTML = '<div class="alert alert-warning">لا توجد نتائج</div>';
                }
            })
            .catch(error => {
                console.error('❌ خطأ في البحث:', error);
                newSearchResults.innerHTML = '<div class="alert alert-danger">خطأ في البحث</div>';
            });
    }

    function displayNewSearchResults(customers) {
        if (customers.length === 0) {
            newSearchResults.innerHTML = '<div class="alert alert-warning">لا توجد نتائج</div>';
            return;
        }

        let html = '<div class="list-group">';
        customers.forEach(customer => {
            html += `
                <button type="button" class="list-group-item list-group-item-action" onclick="selectNewCustomer(${customer.id}, '${customer.name}', '${customer.id_number}', '${customer.phone}')">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h6 class="mb-1">${customer.name}</h6>
                            <p class="mb-1 text-muted">رقم الهوية: ${customer.id_number}</p>
                            <small class="text-muted">الهاتف: ${customer.phone}</small>
                        </div>
                        <i class="fas fa-user-plus text-primary"></i>
                    </div>
                </button>
            `;
        });
        html += '</div>';
        newSearchResults.innerHTML = html;
    }

    // اختيار العميل
    window.selectNewCustomer = function(id, name, idNumber, phone) {
        selectedCustomerData = { id, name, idNumber, phone };

        // إخفاء نتائج البحث وعرض بيانات العميل المختار
        newSearchResults.innerHTML = `
            <div class="alert alert-success">
                <h6>✅ تم اختيار العميل:</h6>
                <p><strong>الاسم:</strong> ${name}</p>
                <p><strong>رقم الهوية:</strong> ${idNumber}</p>
                <p><strong>الهاتف:</strong> ${phone}</p>
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="clearNewSelection()">
                    <i class="fas fa-times"></i> إلغاء الاختيار
                </button>
            </div>
        `;

        // تحديث الحقل المخفي
        const customerIdField = document.getElementById('customer_id');
        if (customerIdField) {
            customerIdField.value = id;
        }

        // مسح حقل البحث
        newCustomerSearch.value = name;
    };

    // إلغاء الاختيار
    window.clearNewSelection = function() {
        selectedCustomerData = null;
        newSearchResults.innerHTML = '';
        newCustomerSearch.value = '';
        const customerIdField = document.getElementById('customer_id');
        if (customerIdField) {
            customerIdField.value = '';
        }
    };
    
    // ===== اختيار العميل =====
    window.selectCustomer = function(id, name, idNumber, phone, email) {
        selectedCustomer = { id, name, idNumber, phone, email };

        customerSearch.value = name;
        customerSearchResults.style.display = 'none';

        // عرض بيانات العميل
        customerDetails.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>الاسم:</strong> جنيه{name}<br>
                    <strong>رقم الهوية:</strong> جنيه{idNumber}
                </div>
                <div class="col-md-6">
                    <strong>الهاتف:</strong> جنيه{phone || 'غير محدد'}<br>
                    <strong>البريد:</strong> جنيه{email || 'غير محدد'}
                </div>
            </div>
        `;

        selectedCustomerInfo.style.display = 'block';

        // إظهار قسم اختيار الغرفة
        const roomSelectionSection = document.getElementById('roomSelectionSection');
        if (roomSelectionSection) {
            roomSelectionSection.style.display = 'block';
        }

        // تحديث الخطوة 1
        updateStep(1, true);

        // تحديث الحقل المخفي
        updateHiddenFields();

        console.log('✅ تم اختيار العميل:', name);
    };
    
    // ===== اختيار الغرفة =====
    roomSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        
        if (!selectedOption.value) {
            // لا نخفي البيانات، فقط نعيد تعيين المحتوى
            roomDetails.innerHTML = '';
            updateStep(2, false);
            return;
        }
        
        const roomData = {
            id: selectedOption.value,
            number: selectedOption.dataset.roomNumber,
            type: selectedOption.dataset.roomType,
            price: parseFloat(selectedOption.dataset.price),
            capacity: selectedOption.dataset.capacity,
            description: selectedOption.dataset.description
        };
        
        selectedRoom = roomData;
        
        // فحص توفر الغرفة
        checkRoomAvailability(roomData);
    });
    
    function checkRoomAvailability(roomData) {
        console.log('🏨 فحص توفر الغرفة:', roomData.number);
        
        roomAvailabilityMessage.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>جاري فحص التوفر...</div>';
        
        // محاكاة فحص التوفر (يمكن استبدالها بـ API call)
        setTimeout(() => {
            const isAvailable = Math.random() > 0.3; // 70% احتمال التوفر
            
            if (isAvailable) {
                showRoomAvailable(roomData);
            } else {
                showRoomUnavailable(roomData);
            }
        }, 1000);
    }
    
    function showRoomAvailable(roomData) {
        roomAvailabilityMessage.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-check-circle me-2"></i>الغرفة متاحة للحجز
            </div>
        `;

        // عرض تفاصيل الغرفة
        roomDetails.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>رقم الغرفة:</strong> ${roomData.number}<br>
                    <strong>النوع:</strong> ${roomData.type}<br>
                    <strong>السعة:</strong> ${roomData.capacity} أشخاص
                </div>
                <div class="col-md-6">
                    <strong>السعر الأساسي:</strong> ${roomData.price} جنيه/ليلة<br>
                    <strong>الوصف:</strong> ${roomData.description || 'غير متوفر'}
                </div>
            </div>
        `;

        selectedRoomInfo.style.display = 'block';
        occupancyTypeSection.style.display = 'block';

        // تحديد أسعار أنواع الإقامة (افتراضي 2026)
        roomPrices = {
            single: 900,
            double: 1250,
            triple: 1500
        };

        updateOccupancyPrices();

        // تحديث الخطوة 2
        updateStep(2, true);

        // تحديث الحقل المخفي
        updateHiddenFields();
    }
    
    function showRoomUnavailable(roomData) {
        roomAvailabilityMessage.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle me-2"></i>الغرفة غير متاحة حالياً
            </div>
        `;
        
        // لا نخفي البيانات، فقط نعرض رسالة عدم التوفر
    }
    
    // ===== نوع الإقامة =====
    occupancyType.addEventListener('change', function() {
        if (!this.value) {
            // لا نخفي البيانات، فقط نعيد تعيين السعر
            currentPrice = 0;
            updateStep(3, false);
            return;
        }

        currentPrice = roomPrices[this.value] || 0;
        updateOccupancyPrices();

        discountSection.style.display = 'block';
        datesSection.style.display = 'block';

        // تحديث الخطوة 3
        updateStep(3, true);

        // تحديث الحقل المخفي
        updateHiddenFields();

        calculateTotal();
    });
    
    function updateOccupancyPrices() {
        const selectedType = occupancyType.value;
        const isDeusChecked = isDeus && isDeus.checked;

        // الحصول على تاريخ الوصول لتحديد الأسعار
        const checkInVal = checkInDate.value;
        let is2026OrLater = true; // افتراضي: الأسعار الجديدة
        
        if (checkInVal) {
            // استخراج السنة مباشرة من النص لتجنب مشاكل التوقيت
            const year = parseInt(checkInVal.substring(0, 4));
            if (!isNaN(year) && year < 2026) {
                is2026OrLater = false;
            }
        }

        let priceInfo = `<div class="alert alert-info"><strong>أسعار أنواع الإقامة ${isDeusChecked ? '(ديوز)' : '(عادي)'}:</strong><br>`;

        let normalPrices;
        if (is2026OrLater) {
             normalPrices = {
                single: 900,
                double: 1250,
                triple: 1500
            };
        } else {
             normalPrices = {
                single: 800,
                double: 1100,
                triple: 1400
            };
        }

        const deusPrices = {
            single: 500,
            double: 700,
            triple: 900
        };

        const typeNames = {
            single: 'Single - إقامة مفردة',
            double: 'Double - إقامة مزدوجة',
            triple: 'Triple - إقامة ثلاثية'
        };

        const currentPrices = isDeusChecked ? deusPrices : normalPrices;

        Object.keys(currentPrices).forEach(type => {
            const isSelected = type === selectedType;
            const className = isSelected ? 'text-success fw-bold' : 'text-muted';
            const typeName = typeNames[type] || type;
            priceInfo += `<span class="${className}">${typeName}: ${currentPrices[type]} جنيه/ليلة</span><br>`;
        });

        priceInfo += '</div>';
        occupancyPriceInfo.innerHTML = priceInfo;

        // تحديث السعر الحالي
        if (selectedType && currentPrices[selectedType]) {
            currentPrice = currentPrices[selectedType];
        }
    }
    
    // ===== التواريخ =====
    checkInDate.addEventListener('change', function() {
        // إزالة قيود التاريخ - يمكن اختيار أي تاريخ
        // if (this.value) {
        //     checkOutDate.setAttribute('min', this.value);
        //     if (checkOutDate.value && checkOutDate.value <= this.value) {
        //         const nextDay = new Date(this.value);
        //         nextDay.setDate(nextDay.getDate() + 1);
        //         checkOutDate.value = nextDay.toISOString().split('T')[0];
        //     }
        // }
        calculateDays();
        updateOccupancyPrices(); // تحديث الأسعار بناءً على التاريخ الجديد
        calculateTotal(); // إعادة حساب الإجمالي
    });
    
    checkOutDate.addEventListener('change', calculateDays);
    
    function calculateDays() {
        if (checkInDate.value && checkOutDate.value) {
            const startDate = new Date(checkInDate.value);
            const endDate = new Date(checkOutDate.value);
            const diffTime = endDate - startDate;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            // السماح بأي عدد من الأيام (حتى لو كان سالباً)
            currentDays = Math.abs(diffDays) || 1; // استخدام القيمة المطلقة أو 1 كحد أدنى
            numberOfDays.textContent = currentDays;
            daysInfo.style.display = 'block';

            // تحديث الخطوة 4
            updateStep(4, true);

            // إظهار قسم الملاحظات
            const notesSection = document.getElementById('notesSection');
            if (notesSection) {
                notesSection.style.display = 'block';
            }

            calculateTotal();
        }
    }
    
    // ===== الخصم =====
    discountPercentage.addEventListener('input', calculateTotal);

    // ===== الضريبة =====
    if (includeTax) {
        includeTax.addEventListener('change', calculateTotal);
    }

    // ===== الديوز =====
    if (isDeus) {
        isDeus.addEventListener('change', function() {
            updateOccupancyPrices();
            calculateTotal();
        });
    }
    
    // ===== حساب الإجمالي =====
    function calculateTotal() {
        if (!currentPrice || !currentDays) {
            // لا نخفي البيانات، فقط نعرض رسالة
            document.getElementById('finalBookingSummary').innerHTML = `
                <div class="card border-warning">
                    <div class="card-header bg-warning text-dark">
                        <h6 class="mb-0"><i class="fas fa-exclamation-triangle me-2"></i>ملخص الحجز</h6>
                    </div>
                    <div class="card-body">
                        <p class="text-muted">يرجى اختيار جميع البيانات المطلوبة لعرض ملخص الحجز</p>
                    </div>
                </div>
            `;
            updateStep(5, false);
            return;
        }

        const baseTotal = currentPrice * currentDays;

        // حساب الضريبة أولاً على المبلغ الأساسي
        const isTaxIncluded = includeTax && includeTax.checked;
        const taxValue = isTaxIncluded ? (baseTotal * 14) / 100 : 0;
        const totalWithTax = baseTotal + taxValue;

        // تطبيق الخصم على الإجمالي (شامل الضريبة)
        const discountPercent = parseFloat(discountPercentage.value) || 0;
        const discountValue = (totalWithTax * discountPercent) / 100;
        const finalTotal = totalWithTax - discountValue;
        const afterDiscount = finalTotal - taxValue; // للعرض فقط

        // تحديث الملخص
        summaryContent.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>العميل:</strong> ${selectedCustomer?.name || 'غير محدد'}<br>
                    <strong>الغرفة:</strong> رقم ${selectedRoom?.number || 'غير محدد'}<br>
                    <strong>نوع الإقامة:</strong> ${occupancyType.options[occupancyType.selectedIndex]?.text || 'غير محدد'}
                </div>
                <div class="col-md-6">
                    <strong>تاريخ الوصول:</strong> ${checkInDate.value || 'غير محدد'}<br>
                    <strong>تاريخ المغادرة:</strong> ${checkOutDate.value || 'غير محدد'}<br>
                    <strong>عدد الليالي:</strong> ${currentDays} ليلة
                </div>
            </div>
        `;

        // تحديث المبالغ
        baseAmount.textContent = baseTotal.toFixed(2);
        discountAmount.textContent = discountValue.toFixed(2);

        // إظهار أو إخفاء صف الضريبة
        if (isTaxIncluded && taxRow) {
            taxRow.style.display = 'block';
            afterDiscountAmount.textContent = afterDiscount.toFixed(2);
            taxAmount.textContent = taxValue.toFixed(2);
        } else if (taxRow) {
            taxRow.style.display = 'none';
        }

        totalAmount.textContent = finalTotal.toFixed(2);

        finalBookingSummary.style.display = 'block';

        // إظهار زر التأكيد
        const submitSection = document.getElementById('submitSection');
        if (submitSection) {
            submitSection.style.display = 'block';
        }

        // تحديث الخطوة 5
        updateStep(5, true);

        // تحديث الحقول المخفية
        updateHiddenFields();

        console.log('💰 تم حساب الإجمالي:', finalTotal);
    }
    
    // إضافة مستمع لإرسال النموذج
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            console.log('📝 إرسال النموذج...');

            // تحديث الحقول المخفية قبل الإرسال
            updateHiddenFields();

            // التحقق من البيانات المطلوبة
            const requiredFields = [
                { id: 'hiddenCustomerId', name: 'العميل' },
                { id: 'hiddenRoomNumber', name: 'رقم الغرفة' },
                { id: 'hiddenOccupancyType', name: 'نوع الإقامة' },
                { id: 'checkInDate', name: 'تاريخ الوصول' },
                { id: 'checkOutDate', name: 'تاريخ المغادرة' }
            ];

            let missingFields = [];

            requiredFields.forEach(field => {
                const element = document.getElementById(field.id);
                if (!element || !element.value) {
                    missingFields.push(field.name);
                }
            });

            if (missingFields.length > 0) {
                e.preventDefault();
                alert('يرجى إكمال البيانات المطلوبة:\n' + missingFields.join('\n'));
                return false;
            }

            // عرض البيانات في console للتحقق
            console.log('📊 بيانات النموذج:');
            console.log('العميل:', document.getElementById('hiddenCustomerId').value);
            console.log('رقم الغرفة:', document.getElementById('hiddenRoomNumber').value);
            console.log('نوع الإقامة:', document.getElementById('hiddenOccupancyType').value);
            console.log('تاريخ الوصول:', document.getElementById('checkInDate').value);
            console.log('تاريخ المغادرة:', document.getElementById('checkOutDate').value);
            console.log('نسبة الخصم:', document.getElementById('hiddenDiscountPercentage').value);

            console.log('✅ تم إرسال النموذج بنجاح');
        });
    }

    console.log('✅ تم تحميل JavaScript بنجاح');
});
