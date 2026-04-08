// JavaScript محدث لصفحة إنشاء الحجز الجديد
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 تحميل نظام الحجز المحدث...');
    
    // العناصر الأساسية
    const customerSearch = document.getElementById('customerSearch');
    const customerSearchResults = document.getElementById('customerSearchResults');
    const selectedCustomerInfo = document.getElementById('selectedCustomerInfo');
    const customerDetails = document.getElementById('customerDetails');
    const changeCustomerBtn = document.getElementById('changeCustomerBtn');
    
    // عناصر التواريخ
    const checkInDate = document.getElementById('checkInDate');
    const checkOutDate = document.getElementById('checkOutDate');
    const daysInfo = document.getElementById('daysInfo');
    const numberOfDays = document.getElementById('numberOfDays');
    
    // عناصر الغرفة
    const roomSelectionSection = document.getElementById('roomSelectionSection');
    const roomSelect = document.getElementById('roomSelect');
    const selectedRoomInfo = document.getElementById('selectedRoomInfo');
    const roomDetails = document.getElementById('roomDetails');
    const changeRoomBtn = document.getElementById('changeRoomBtn');
    
    // عناصر نوع الإقامة
    const occupancyTypeSection = document.getElementById('occupancyTypeSection');
    const occupancyType = document.getElementById('occupancyType');
    const occupancyPriceInfo = document.getElementById('occupancyPriceInfo');
    
    // عناصر إضافية
    const additionalOptionsSection = document.getElementById('additionalOptionsSection');
    const discountSection = document.getElementById('discountSection');
    const finalBookingSummary = document.getElementById('finalBookingSummary');
    const notesSection = document.getElementById('notesSection');
    const submitSection = document.getElementById('submitSection');
    
    // عناصر العميل الجديد
    const addNewCustomerBtn = document.getElementById('addNewCustomerBtn');
    const newCustomerCard = document.getElementById('newCustomerCard');
    const newCustomerForm = document.getElementById('newCustomerForm');
    const cancelNewCustomerBtn = document.getElementById('cancelNewCustomerBtn');
    
    // عناصر الخطوات
    const steps = {
        step1: document.getElementById('step1'),
        step2: document.getElementById('step2'),
        step3: document.getElementById('step3'),
        step4: document.getElementById('step4'),
        step5: document.getElementById('step5')
    };
    
    // بيانات الحجز
    let selectedCustomer = null;
    let selectedRoom = null;
    let bookingDays = 0;
    let currentPrices = {};
    
    // تعيين التواريخ الافتراضية
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    checkInDate.value = today.toISOString().split('T')[0];
    checkOutDate.value = tomorrow.toISOString().split('T')[0];
    
    // ===== البحث عن العملاء =====
    let searchTimeout;
    
    customerSearch.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            customerSearchResults.innerHTML = '';
            return;
        }
        
        searchTimeout = setTimeout(() => {
            searchCustomers(query);
        }, 300);
    });
    
    function searchCustomers(query) {
        console.log('🔍 البحث عن العملاء:', query);
        
        customerSearchResults.innerHTML = '<div class="p-2 text-center"><i class="fas fa-spinner fa-spin"></i> جاري البحث...</div>';
        
        fetch(`/bookings/new-search-customers?q=${encodeURIComponent(query)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('📊 البيانات المستلمة:', data);
                displayCustomerResults(data.customers || []);
            })
            .catch(error => {
                console.error('❌ خطأ في البحث:', error);
                customerSearchResults.innerHTML = '<div class="alert alert-danger">خطأ في البحث</div>';
            });
    }
    
    function displayCustomerResults(customers) {
        if (customers.length === 0) {
            customerSearchResults.innerHTML = '<div class="alert alert-warning">لا توجد نتائج</div>';
            return;
        }
        
        let html = '<div class="list-group">';
        customers.forEach(customer => {
            html += `
                <button type="button" class="list-group-item list-group-item-action" 
                        onclick="selectCustomer(${customer.id}, '${customer.name}', '${customer.id_number}', '${customer.phone || ''}')">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h6 class="mb-1">${customer.name}</h6>
                            <p class="mb-1 text-muted">رقم الهوية: ${customer.id_number}</p>
                            ${customer.phone ? `<small class="text-muted">الهاتف: ${customer.phone}</small>` : ''}
                        </div>
                        <i class="fas fa-chevron-left"></i>
                    </div>
                </button>
            `;
        });
        html += '</div>';
        
        customerSearchResults.innerHTML = html;
    }
    
    // اختيار العميل
    window.selectCustomer = function(id, name, idNumber, phone) {
        selectedCustomer = { id, name, idNumber, phone };

        customerDetails.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>الاسم:</strong> ${name}
                </div>
                <div class="col-md-6">
                    <strong>رقم الهوية:</strong> ${idNumber}
                </div>
                ${phone ? `<div class="col-md-12 mt-2"><strong>الهاتف:</strong> ${phone}</div>` : ''}
            </div>
        `;

        selectedCustomerInfo.style.display = 'block';
        customerSearchResults.innerHTML = '';
        customerSearch.value = name;

        // تحديث الحقل المخفي
        document.getElementById('hiddenCustomerId').value = id;

        // تحديث الخطوة
        updateStep('step1', true);

        // إذا كانت التواريخ محددة، تحميل الغرف المتاحة
        if (checkInDate.value && checkOutDate.value) {
            console.log('✅ العميل والتواريخ محددة، تحميل الغرف...');
            loadAvailableRooms();
        }

        console.log('✅ تم اختيار العميل:', name);
    };
    
    // تغيير العميل
    changeCustomerBtn.addEventListener('click', function() {
        selectedCustomer = null;
        selectedCustomerInfo.style.display = 'none';
        customerSearch.value = '';
        customerSearch.focus();
        document.getElementById('hiddenCustomerId').value = '';
        updateStep('step1', false);
    });
    
    // ===== إضافة عميل جديد =====
    addNewCustomerBtn.addEventListener('click', function() {
        newCustomerCard.style.display = 'block';
        customerSearchResults.innerHTML = '';
    });
    
    cancelNewCustomerBtn.addEventListener('click', function() {
        newCustomerCard.style.display = 'none';
        newCustomerForm.reset();
    });
    
    newCustomerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const name = document.getElementById('newCustomerName').value.trim();
        const idNumber = document.getElementById('newCustomerIdNumber').value.trim();
        const phone = document.getElementById('newCustomerPhone').value.trim();
        const email = document.getElementById('newCustomerEmail').value.trim();
        
        if (!name || !idNumber) {
            alert('الاسم ورقم الهوية مطلوبان');
            return;
        }
        
        // إرسال البيانات لإضافة العميل
        fetch('/customers/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrf_token]').value
            },
            body: JSON.stringify({
                name: name,
                id_number: idNumber,
                phone: phone,
                email: email
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // اختيار العميل الجديد
                selectCustomer(data.customer.id, data.customer.name, data.customer.id_number, data.customer.phone);
                newCustomerCard.style.display = 'none';
                newCustomerForm.reset();
                alert('تم إضافة العميل بنجاح');
            } else {
                alert('خطأ في إضافة العميل: ' + data.message);
            }
        })
        .catch(error => {
            console.error('خطأ:', error);
            alert('حدث خطأ أثناء إضافة العميل');
        });
    });
    
    // ===== التواريخ =====
    function updateDays() {
        const checkIn = new Date(checkInDate.value);
        const checkOut = new Date(checkOutDate.value);

        console.log('📅 تحديث التواريخ:', checkInDate.value, 'إلى', checkOutDate.value);

        if (checkIn && checkOut && checkOut > checkIn) {
            bookingDays = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
            numberOfDays.textContent = bookingDays;
            daysInfo.style.display = 'block';

            // تحديث الخطوة
            updateStep('step2', true);

            // إظهار اختيار الغرفة إذا كان العميل محدد
            if (selectedCustomer) {
                console.log('✅ العميل محدد، تحميل الغرف المتاحة...');
                loadAvailableRooms();
            } else {
                console.log('❌ العميل غير محدد، لا يمكن تحميل الغرف');
            }

            console.log('📅 عدد الأيام:', bookingDays);
        } else {
            daysInfo.style.display = 'none';
            updateStep('step2', false);
            roomSelectionSection.style.display = 'none';

            // إخفاء الأقسام التالية
            hideAllSections();

            console.log('❌ التواريخ غير صحيحة');
        }
    }

    // دالة لإخفاء جميع الأقسام
    function hideAllSections() {
        selectedRoomInfo.style.display = 'none';
        occupancyTypeSection.style.display = 'none';
        additionalOptionsSection.style.display = 'none';
        discountSection.style.display = 'none';
        finalBookingSummary.style.display = 'none';
        notesSection.style.display = 'none';
        submitSection.style.display = 'none';
    }
    
    checkInDate.addEventListener('change', updateDays);
    checkOutDate.addEventListener('change', updateDays);
    
    // تحديث الأيام عند التحميل
    updateDays();

    // تحميل جميع الغرف عند بدء التشغيل
    console.log('🏨 تحميل جميع الغرف...');
    fetch('/bookings/available-rooms')
        .then(response => response.json())
        .then(data => {
            console.log('📊 استجابة الغرف:', data);
            if (data.success && data.rooms) {
                displayAvailableRooms(data.rooms);
            } else {
                console.error('❌ فشل في تحميل الغرف:', data.message);
            }
        })
        .catch(error => {
            console.error('❌ خطأ في تحميل الغرف:', error);
        });

    // إضافة مستمع للتحقق من وجود العناصر
    console.log('🔍 فحص العناصر المطلوبة...');
    const requiredElements = [
        'customerSearch', 'roomSelect', 'occupancyType',
        'discountPercentage', 'includeTax', 'isDeus',
        'finalBookingSummary', 'baseAmount', 'totalAmount',
        'selectedCustomerInfo', 'roomSelectionSection', 'occupancyTypeSection',
        'additionalOptionsSection', 'discountSection', 'notesSection', 'submitSection'
    ];

    let missingElements = [];
    requiredElements.forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            console.log(`✅ ${elementId}: موجود`);
        } else {
            console.error(`❌ ${elementId}: غير موجود`);
            missingElements.push(elementId);
        }
    });

    if (missingElements.length > 0) {
        console.error('❌ عناصر مفقودة:', missingElements);
        alert('تحذير: بعض عناصر النموذج مفقودة. قد لا يعمل النظام بشكل صحيح.');
    } else {
        console.log('✅ جميع العناصر المطلوبة موجودة');
    }
    
    // ===== تحديث الخطوات =====
    function updateStep(stepId, completed) {
        const step = steps[stepId];
        if (!step) {
            console.log(`❌ الخطوة ${stepId} غير موجودة`);
            return;
        }

        const badge = step.querySelector('.badge');
        const check = step.querySelector('.fas.fa-check');

        if (completed) {
            badge.className = 'badge bg-success rounded-pill me-2';
            if (check) check.style.display = 'inline';
            console.log(`✅ تم تحديث الخطوة ${stepId} كمكتملة`);
        } else {
            badge.className = 'badge bg-secondary rounded-pill me-2';
            if (check) check.style.display = 'none';
            console.log(`❌ تم تحديث الخطوة ${stepId} كغير مكتملة`);
        }
    }
    
    // ===== تحميل الغرف المتاحة =====
    function loadAvailableRooms() {
        if (!checkInDate.value || !checkOutDate.value) {
            console.log('❌ التواريخ غير محددة');
            return;
        }

        console.log('🏨 تحميل الغرف المتاحة...');
        console.log('📅 من:', checkInDate.value, 'إلى:', checkOutDate.value);

        const url = `/bookings/available-rooms?check_in=${checkInDate.value}&check_out=${checkOutDate.value}`;

        fetch(url)
            .then(response => {
                console.log('📡 استجابة الخادم:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('📊 بيانات الغرف:', data);
                if (data.success) {
                    displayAvailableRooms(data.rooms);
                    roomSelectionSection.style.display = 'block';
                } else {
                    console.error('خطأ في تحميل الغرف:', data.message);
                    roomSelectionSection.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('خطأ في تحميل الغرف:', error);
                roomSelectionSection.style.display = 'none';
            });
    }

    function displayAvailableRooms(rooms) {
        console.log('🏨 عرض الغرف المتاحة:', rooms);

        roomSelect.innerHTML = '<option value="">اختر الغرفة...</option>';

        if (!rooms || rooms.length === 0) {
            roomSelect.innerHTML = '<option value="">لا توجد غرف متاحة في هذه التواريخ</option>';
            console.log('❌ لا توجد غرف متاحة');
            return;
        }

        rooms.forEach(room => {
            const option = document.createElement('option');
            option.value = room.id;
            option.textContent = `غرفة ${room.room_number} - ${room.room_type} - ${room.price_per_night} جنيه/ليلة`;
            option.dataset.roomNumber = room.room_number;
            option.dataset.roomType = room.room_type;
            option.dataset.price = room.price_per_night;
            option.dataset.capacity = room.capacity;
            option.dataset.description = room.description || '';
            roomSelect.appendChild(option);
        });

        console.log(`✅ تم تحميل ${rooms.length} غرفة متاحة`);

        // إظهار قسم اختيار الغرفة
        roomSelectionSection.style.display = 'block';
    }

    // اختيار الغرفة
    roomSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];

        console.log('🏨 تم اختيار الغرفة:', selectedOption.value);

        if (selectedOption.value) {
            selectedRoom = {
                id: selectedOption.value,
                room_number: selectedOption.dataset.roomNumber,
                room_type: selectedOption.dataset.roomType,
                price: parseFloat(selectedOption.dataset.price),
                capacity: parseInt(selectedOption.dataset.capacity),
                description: selectedOption.dataset.description
            };

            console.log('📋 بيانات الغرفة المختارة:', selectedRoom);

            displayRoomDetails();
            updateStep('step3', true);

            // إظهار نوع الإقامة
            occupancyTypeSection.style.display = 'block';
            console.log('✅ تم إظهار قسم نوع الإقامة');

            // تحديث الحقل المخفي
            document.getElementById('hiddenRoomId').value = selectedRoom.id;

        } else {
            selectedRoom = null;
            selectedRoomInfo.style.display = 'none';
            updateStep('step3', false);
            occupancyTypeSection.style.display = 'none';

            // إخفاء الأقسام التالية
            additionalOptionsSection.style.display = 'none';
            discountSection.style.display = 'none';
            finalBookingSummary.style.display = 'none';
            notesSection.style.display = 'none';
            submitSection.style.display = 'none';
        }
    });

    function displayRoomDetails() {
        roomDetails.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>رقم الغرفة:</strong> ${selectedRoom.room_number}
                </div>
                <div class="col-md-6">
                    <strong>نوع الغرفة:</strong> ${selectedRoom.room_type}
                </div>
                <div class="col-md-6 mt-2">
                    <strong>السعر الأساسي:</strong> ${selectedRoom.price} جنيه/ليلة
                </div>
                <div class="col-md-6 mt-2">
                    <strong>السعة:</strong> ${selectedRoom.capacity} أشخاص
                </div>
                ${selectedRoom.description ? `<div class="col-md-12 mt-2"><strong>الوصف:</strong> ${selectedRoom.description}</div>` : ''}
            </div>
        `;

        selectedRoomInfo.style.display = 'block';

        // تحديث أسعار نوع الإقامة
        updateOccupancyPrices();
    }

    // تغيير الغرفة
    changeRoomBtn.addEventListener('click', function() {
        selectedRoom = null;
        selectedRoomInfo.style.display = 'none';
        roomSelect.value = '';
        updateStep('step3', false);
        occupancyTypeSection.style.display = 'none';
        document.getElementById('hiddenRoomId').value = '';
    });

    // ===== نوع الإقامة =====
    function updateOccupancyPrices() {
        if (!selectedRoom) return;

        const isDeus = document.getElementById('isDeus').checked;

        if (isDeus) {
            // أسعار الديوز
            currentPrices = {
                single: 500,
                double: 700,
                triple: 900
            };

            occupancyPriceInfo.innerHTML = `
                <div class="alert alert-warning">
                    <strong><i class="fas fa-star me-2"></i>أسعار الديوز (مخفضة):</strong><br>
                    <span class="text-muted">Single: ${currentPrices.single} جنيه/ليلة</span><br>
                    <span class="text-muted">Double: ${currentPrices.double} جنيه/ليلة</span><br>
                    <span class="text-muted">Triple: ${currentPrices.triple} جنيه/ليلة</span>
                </div>
            `;
        } else {
            // التحقق من السنة لتحديد الأسعار (تحديث 2026)
            const checkInVal = checkInDate.value;
            let is2026OrLater = true; // افتراضي: الأسعار الجديدة
            
            if (checkInVal) {
                const year = parseInt(checkInVal.substring(0, 4));
                if (!isNaN(year) && year < 2026) {
                    is2026OrLater = false;
                }
            }

            if (is2026OrLater) {
                // الأسعار الجديدة بداية من 2026
                currentPrices = {
                    single: 900,
                    double: 1250,
                    triple: 1500
                };
            } else {
                // الأسعار القديمة
                currentPrices = {
                    single: 800,
                    double: 1100,
                    triple: 1400
                };
            }

            occupancyPriceInfo.innerHTML = `
                <div class="alert alert-info">
                    <strong><i class="fas fa-money-bill me-2"></i>أسعار أنواع الإقامة:</strong><br>
                    <span class="text-muted">Single: ${currentPrices.single} جنيه/ليلة</span><br>
                    <span class="text-muted">Double: ${currentPrices.double} جنيه/ليلة</span><br>
                    <span class="text-muted">Triple: ${currentPrices.triple} جنيه/ليلة</span>
                </div>
            `;
        }

        console.log('💰 تم تحديث أسعار نوع الإقامة:', currentPrices);
    }

    occupancyType.addEventListener('change', function() {
        console.log('👥 تم اختيار نوع الإقامة:', this.value);

        if (this.value) {
            updateStep('step4', true);

            // إظهار الخيارات الإضافية
            additionalOptionsSection.style.display = 'block';
            discountSection.style.display = 'block';
            finalBookingSummary.style.display = 'block';
            notesSection.style.display = 'block';
            submitSection.style.display = 'block';

            console.log('✅ تم إظهار جميع الأقسام الإضافية');

            // تحديث الحقل المخفي
            document.getElementById('hiddenOccupancyType').value = this.value;

            // حساب السعر
            calculateTotal();

        } else {
            updateStep('step4', false);
            additionalOptionsSection.style.display = 'none';
            discountSection.style.display = 'none';
            finalBookingSummary.style.display = 'none';
            notesSection.style.display = 'none';
            submitSection.style.display = 'none';

            console.log('❌ تم إخفاء الأقسام الإضافية');
        }
    });

    // ===== حساب المجموع =====
    function calculateTotal() {
        if (!selectedRoom || !occupancyType.value || !bookingDays) {
            console.log('❌ بيانات ناقصة للحساب:', {
                selectedRoom: !!selectedRoom,
                occupancyType: occupancyType.value,
                bookingDays: bookingDays
            });
            return;
        }

        console.log('💰 بدء حساب المجموع...');

        const occupancy = occupancyType.value;
        const isDeus = document.getElementById('isDeus').checked;

        // تحديد السعر حسب الديوز أو العادي
        let pricePerNight;
        if (isDeus) {
            const deusPrices = { single: 600, double: 800, triple: 1000 };
            pricePerNight = deusPrices[occupancy] || 500;
        } else {
            pricePerNight = currentPrices[occupancy] || selectedRoom.price;
        }

        const baseAmount = pricePerNight * bookingDays;

        // حساب الضريبة أولاً على المبلغ الأساسي
        const includeTax = document.getElementById('includeTax').checked;
        const taxAmount = includeTax ? (baseAmount * 0.14) : 0;
        const totalWithTax = baseAmount + taxAmount;

        // تطبيق الخصم على الإجمالي (شامل الضريبة)
        const discountPercentage = parseFloat(document.getElementById('discountPercentage').value) || 0;
        const discountAmount = (totalWithTax * discountPercentage) / 100;
        const totalAmount = totalWithTax - discountAmount;
        const afterDiscount = totalAmount - taxAmount; // للعرض فقط

        console.log('📊 تفاصيل الحساب:', {
            pricePerNight,
            bookingDays,
            baseAmount,
            discountPercentage,
            discountAmount,
            afterDiscount,
            taxAmount,
            totalAmount,
            isDeus,
            includeTax
        });

        // تحديث العرض
        document.getElementById('baseAmount').textContent = baseAmount.toFixed(0);
        document.getElementById('discountAmount').textContent = discountAmount.toFixed(0);
        document.getElementById('afterDiscountAmount').textContent = afterDiscount.toFixed(0);
        document.getElementById('taxAmount').textContent = taxAmount.toFixed(0);
        document.getElementById('totalAmount').textContent = totalAmount.toFixed(0);

        // إظهار/إخفاء صف الضريبة
        const taxRow = document.getElementById('taxRow');
        if (includeTax) {
            taxRow.style.display = 'block';
        } else {
            taxRow.style.display = 'none';
        }

        // تحديث ملخص الحجز
        updateBookingSummary();

        console.log('✅ تم حساب المجموع:', totalAmount);
    }

    function updateBookingSummary() {
        const summaryContent = document.getElementById('summaryContent');

        const isDeus = document.getElementById('isDeus').checked;
        const includeTax = document.getElementById('includeTax').checked;
        const discountPercentage = parseFloat(document.getElementById('discountPercentage').value) || 0;

        // تحديد نوع الإقامة بالعربية
        const occupancyTypes = {
            'single': 'إقامة مفردة',
            'double': 'إقامة مزدوجة',
            'triple': 'إقامة ثلاثية'
        };

        summaryContent.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong><i class="fas fa-user me-1"></i>العميل:</strong> ${selectedCustomer.name}
                </div>
                <div class="col-md-6">
                    <strong><i class="fas fa-bed me-1"></i>الغرفة:</strong> ${selectedRoom.room_number} (${selectedRoom.room_type})
                </div>
                <div class="col-md-6 mt-2">
                    <strong><i class="fas fa-calendar-alt me-1"></i>تاريخ الوصول:</strong> ${checkInDate.value}
                </div>
                <div class="col-md-6 mt-2">
                    <strong><i class="fas fa-calendar-alt me-1"></i>تاريخ المغادرة:</strong> ${checkOutDate.value}
                </div>
                <div class="col-md-6 mt-2">
                    <strong><i class="fas fa-users me-1"></i>نوع الإقامة:</strong> ${occupancyTypes[occupancyType.value] || occupancyType.value}
                </div>
                <div class="col-md-6 mt-2">
                    <strong><i class="fas fa-calendar-day me-1"></i>عدد الأيام:</strong> ${bookingDays} يوم
                </div>
                ${isDeus ? '<div class="col-md-6 mt-2"><span class="badge bg-warning"><i class="fas fa-star me-1"></i>ديوز</span></div>' : ''}
                ${includeTax ? '<div class="col-md-6 mt-2"><span class="badge bg-info"><i class="fas fa-receipt me-1"></i>شامل ضريبة 14%</span></div>' : ''}
                ${discountPercentage > 0 ? `<div class="col-md-6 mt-2"><span class="badge bg-success"><i class="fas fa-percentage me-1"></i>خصم ${discountPercentage}%</span></div>` : ''}
            </div>
        `;
    }

    // مستمعات الأحداث للحسابات
    document.getElementById('discountPercentage').addEventListener('input', function() {
        console.log('💰 تغيير نسبة الخصم:', this.value);
        calculateTotal();
    });

    document.getElementById('includeTax').addEventListener('change', function() {
        console.log('🧾 تغيير الضريبة:', this.checked);
        calculateTotal();
    });

    document.getElementById('isDeus').addEventListener('change', function() {
        console.log('⭐ تغيير الديوز:', this.checked);

        if (this.checked) {
            console.log('✅ تطبيق أسعار الديوز');
            // تطبيق أسعار الديوز
            currentPrices = {
                single: 500,
                double: 700,
                triple: 900
            };
        } else {
            console.log('✅ العودة للأسعار العادية');
            // العودة للأسعار العادية
            updateOccupancyPrices();
        }

        // تحديث عرض الأسعار
        if (selectedRoom) {
            updateOccupancyPrices();
        }

        calculateTotal();
    });

    // ===== إرسال النموذج =====
    document.getElementById('bookingForm').addEventListener('submit', function(e) {
        console.log('📝 محاولة إرسال النموذج...');

        // التحقق من البيانات المطلوبة
        if (!selectedCustomer) {
            e.preventDefault();
            alert('يجب اختيار عميل');
            return false;
        }

        if (!selectedRoom) {
            e.preventDefault();
            alert('يجب اختيار غرفة');
            return false;
        }

        if (!occupancyType.value) {
            e.preventDefault();
            alert('يجب اختيار نوع الإقامة');
            return false;
        }

        if (!checkInDate.value || !checkOutDate.value) {
            e.preventDefault();
            alert('يجب تحديد تواريخ الوصول والمغادرة');
            return false;
        }

        // تحديث الحقول المخفية
        document.getElementById('hiddenCustomerId').value = selectedCustomer.id;
        document.getElementById('hiddenRoomId').value = selectedRoom.id;
        document.getElementById('hiddenOccupancyType').value = occupancyType.value;
        document.getElementById('hiddenCheckInDate').value = checkInDate.value;
        document.getElementById('hiddenCheckOutDate').value = checkOutDate.value;
        document.getElementById('hiddenDiscountPercentage').value = document.getElementById('discountPercentage').value || 0;
        document.getElementById('hiddenNotes').value = document.getElementById('notes').value || '';

        // تحديث checkboxes
        const includeTaxCheckbox = document.getElementById('includeTax');
        const isDeusCheckbox = document.getElementById('isDeus');

        // إضافة حقول مخفية للـ checkboxes
        const includeTaxHidden = document.createElement('input');
        includeTaxHidden.type = 'hidden';
        includeTaxHidden.name = 'include_tax';
        includeTaxHidden.value = includeTaxCheckbox.checked ? '1' : '0';
        this.appendChild(includeTaxHidden);

        const isDeusHidden = document.createElement('input');
        isDeusHidden.type = 'hidden';
        isDeusHidden.name = 'is_deus';
        isDeusHidden.value = isDeusCheckbox.checked ? '1' : '0';
        this.appendChild(isDeusHidden);

        updateStep('step5', true);

        console.log('✅ تم تحديث جميع الحقول، إرسال النموذج...');
        console.log('البيانات المرسلة:', {
            customer_id: selectedCustomer.id,
            room_id: selectedRoom.id,
            occupancy_type: occupancyType.value,
            check_in_date: checkInDate.value,
            check_out_date: checkOutDate.value,
            discount_percentage: document.getElementById('discountPercentage').value,
            include_tax: includeTaxCheckbox.checked,
            is_deus: isDeusCheckbox.checked,
            notes: document.getElementById('notes').value
        });
    });

    // إضافة زر اختبار لإظهار جميع الأقسام (للتطوير فقط)
    const testButton = document.createElement('button');
    testButton.textContent = '🧪 اختبار إظهار جميع الأقسام';
    testButton.className = 'btn btn-warning btn-sm mt-2';
    testButton.type = 'button';
    testButton.onclick = function() {
        console.log('🧪 إظهار جميع الأقسام للاختبار...');

        // محاكاة بيانات للاختبار
        selectedCustomer = { id: 1, name: 'عميل تجريبي', idNumber: '123456789', phone: '01000000000' };
        selectedRoom = { id: 1, room_number: '101', room_type: 'Standard', price: 800, capacity: 2 };
        bookingDays = 2;
        currentPrices = { single: 800, double: 1100, triple: 1400 };

        // إظهار جميع الأقسام
        selectedCustomerInfo.style.display = 'block';
        roomSelectionSection.style.display = 'block';
        selectedRoomInfo.style.display = 'block';
        occupancyTypeSection.style.display = 'block';
        additionalOptionsSection.style.display = 'block';
        discountSection.style.display = 'block';
        finalBookingSummary.style.display = 'block';
        notesSection.style.display = 'block';
        submitSection.style.display = 'block';
        daysInfo.style.display = 'block';

        // ملء البيانات التجريبية
        customerDetails.innerHTML = `
            <div class="row">
                <div class="col-md-6"><strong>الاسم:</strong> عميل تجريبي</div>
                <div class="col-md-6"><strong>رقم الهوية:</strong> 123456789</div>
            </div>
        `;

        roomDetails.innerHTML = `
            <div class="row">
                <div class="col-md-6"><strong>رقم الغرفة:</strong> 101</div>
                <div class="col-md-6"><strong>نوع الغرفة:</strong> Standard</div>
            </div>
        `;

        numberOfDays.textContent = '2';
        updateOccupancyPrices();

        console.log('✅ تم إظهار جميع الأقسام');
    };

    // إضافة الزر إلى الصفحة
    const cardBody = document.querySelector('.card-body');
    if (cardBody) {
        cardBody.appendChild(testButton);
    }

    console.log('✅ تم تحميل نظام الحجز بنجاح');
});
