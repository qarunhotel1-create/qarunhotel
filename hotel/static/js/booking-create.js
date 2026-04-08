// نظام إنشاء الحجز - JavaScript منفصل ونظيف
console.log('🚀 تحميل نظام إنشاء الحجز...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 بدء تهيئة نموذج الحجز...');
    
    // العناصر الأساسية
    const customerSearch = document.getElementById('customer_search');
    const customerIdField = document.getElementById('customer_id');
    const roomIdField = document.getElementById('room_id');
    const occupancyTypeField = document.getElementById('occupancy_type');
    const checkInField = document.getElementById('check_in_date');
    const checkOutField = document.getElementById('check_out_date');
    const discountPercentageField = document.getElementById('discount_percentage');
    const discountAmountField = document.getElementById('discount_amount');
    const includeTaxField = document.getElementById('include_tax');
    const isDeusField = document.getElementById('is_deus');
    
    // متغيرات عامة
    let selectedCustomer = null;
    let isUpdatingDiscount = false;
    
    // أسعار الغرف (تحديث 2026)
    const currentPrices = {
        single: 900,
        double: 1250,
        triple: 1500
    };
    
    console.log('✅ تم تحميل العناصر الأساسية');
    
    // دالة حساب المجموع الرئيسية
    function calculateTotal() {
        console.log('💰 بدء حساب المجموع...');
        
        if (!checkInField || !checkOutField) {
            console.log('❌ حقول التاريخ مفقودة');
            return;
        }
        
        const checkInValue = checkInField.value;
        const checkOutValue = checkOutField.value;
        const occupancyType = occupancyTypeField ? occupancyTypeField.value.toLowerCase() : '';
        
        console.log('📊 البيانات:', {
            checkIn: checkInValue,
            checkOut: checkOutValue,
            occupancy: occupancyType
        });
        
        // إظهار ملخص الحساب إذا كانت التواريخ موجودة
        const calculationSummary = document.getElementById('calculationSummary');
        if (calculationSummary) {
            if (checkInValue && checkOutValue) {
                calculationSummary.style.display = 'block';
                calculationSummary.style.opacity = '1';
                console.log('✅ إظهار ملخص الحساب');
            } else {
                calculationSummary.style.opacity = '0.5';
                console.log('⚠️ إخفاء ملخص الحساب');
            }
        }
        
        if (!checkInValue || !checkOutValue) {
            console.log('⚠️ التواريخ غير مكتملة');
            updateDisplay({
                occupancyType: occupancyType || 'لم يتم الاختيار',
                days: 0,
                pricePerNight: 0,
                baseAmount: 0,
                discountPercent: 0,
                discountAmount: 0,
                afterDiscount: 0,
                taxAmount: 0,
                totalAmount: 0,
                isDeus: false,
                includeTax: false
            });
            return;
        }
        
        const checkIn = new Date(checkInValue);
        const checkOut = new Date(checkOutValue);
        
        if (checkOut <= checkIn) {
            console.log('❌ التواريخ غير صحيحة');
            updateDisplay({
                occupancyType: occupancyType || 'لم يتم الاختيار',
                days: 'خطأ في التواريخ',
                pricePerNight: 0,
                baseAmount: 0,
                discountPercent: 0,
                discountAmount: 0,
                afterDiscount: 0,
                taxAmount: 0,
                totalAmount: 0,
                isDeus: false,
                includeTax: false
            });
            return;
        }
        
        const days = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
        const isDeus = isDeusField && isDeusField.checked;
        const includeTax = includeTaxField && includeTaxField.checked;
        const discountPercent = parseFloat(discountPercentageField ? discountPercentageField.value : 0) || 0;
        
        // تحديد السعر
        let pricePerNight;
        if (isDeus) {
            const deusPrices = { single: 600, double: 800, triple: 1000 };
            pricePerNight = deusPrices[occupancyType] || 500;
        } else {
            // التحقق من السنة لتحديد الأسعار (تحديث 2026)
            let is2026 = true; // افتراضي: الأسعار الجديدة
            
            if (checkInValue) {
                const year = parseInt(checkInValue.substring(0, 4));
                if (!isNaN(year) && year < 2026) {
                    is2026 = false;
                }
            }
            
            let prices;
            if (is2026) {
                prices = {
                    single: 900,
                    double: 1250,
                    triple: 1500
                };
            } else {
                prices = {
                    single: 800,
                    double: 1100,
                    triple: 1400
                };
            }
            
            pricePerNight = prices[occupancyType] || (is2026 ? 900 : 800);
        }
        
        const baseAmount = pricePerNight * days;

        // حساب الضريبة أولاً على المبلغ الأساسي
        const taxAmount = includeTax ? (baseAmount * 0.14) : 0;
        const totalWithTax = baseAmount + taxAmount;

        // تطبيق الخصم على الإجمالي (شامل الضريبة)
        const discountAmount = (totalWithTax * discountPercent) / 100;
        const totalAmount = totalWithTax - discountAmount;
        const afterDiscount = totalAmount - taxAmount; // للعرض فقط
        
        console.log('💰 النتائج:', {
            days, pricePerNight, baseAmount, discountPercent,
            discountAmount, afterDiscount, taxAmount, totalAmount
        });
        
        updateDisplay({
            occupancyType,
            days,
            pricePerNight,
            baseAmount,
            discountPercent,
            discountAmount,
            afterDiscount,
            taxAmount,
            totalAmount,
            isDeus,
            includeTax
        });
    }
    
    // دالة تحديث العرض
    function updateDisplay(calc) {
        const occupancyTypes = {
            'single': 'Single - إقامة مفردة',
            'double': 'Double - إقامة مزدوجة', 
            'triple': 'Triple - إقامة ثلاثية'
        };
        
        const elements = {
            'displayOccupancyType': occupancyTypes[calc.occupancyType] || (calc.occupancyType || 'لم يتم الاختيار'),
            'displayDays': calc.days || '-',
            'displayPricePerNight': calc.pricePerNight || '-',
            'displayBaseAmount': calc.baseAmount ? calc.baseAmount.toFixed(0) : '-',
            'displayDiscountPercent': calc.discountPercent || '0',
            'displayDiscountAmount': calc.discountAmount ? calc.discountAmount.toFixed(0) : '0',
            'displayAfterDiscount': calc.afterDiscount ? calc.afterDiscount.toFixed(0) : '-',
            'displayTaxAmount': calc.taxAmount ? calc.taxAmount.toFixed(0) : '0',
            'displayTotalAmount': calc.totalAmount ? calc.totalAmount.toFixed(0) : '-'
        };
        
        Object.keys(elements).forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = elements[id];
            }
        });
        
        // إظهار/إخفاء الصفوف
        const discountRow = document.getElementById('discountRow');
        const taxRow = document.getElementById('taxRow');
        
        if (discountRow) {
            discountRow.style.display = calc.discountPercent > 0 ? 'block' : 'none';
        }
        
        if (taxRow) {
            taxRow.style.display = calc.includeTax ? 'block' : 'none';
        }
    }
    
    // مستمعات الأحداث
    if (checkInField) {
        checkInField.addEventListener('change', calculateTotal);
        checkInField.addEventListener('input', calculateTotal);
    }
    
    if (checkOutField) {
        checkOutField.addEventListener('change', calculateTotal);
        checkOutField.addEventListener('input', calculateTotal);
    }
    
    if (occupancyTypeField) {
        occupancyTypeField.addEventListener('change', calculateTotal);
    }
    
    if (discountPercentageField) {
        discountPercentageField.addEventListener('input', calculateTotal);
        discountPercentageField.addEventListener('change', calculateTotal);
    }
    
    if (includeTaxField) {
        includeTaxField.addEventListener('change', calculateTotal);
    }
    
    if (isDeusField) {
        isDeusField.addEventListener('change', calculateTotal);
    }
    
    // حساب أولي
    setTimeout(() => {
        console.log('🔄 حساب أولي...');
        calculateTotal();
    }, 500);
    
    console.log('✅ تم تحميل نظام الحجز بنجاح');
});
