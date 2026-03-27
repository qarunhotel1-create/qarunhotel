// مدير الجلسة لتتبع نشاط المستخدم وتسجيل الخروج التلقائي
document.addEventListener('DOMContentLoaded', function() {
    // تكوين مهلة الجلسة (بالدقائق)
    const sessionTimeout = 30; // 30 دقيقة

    // تحويل الدقائق إلى مللي ثانية
    const timeoutMs = sessionTimeout * 60 * 1000;

    // متغيرات لتتبع الجلسة
    let timeoutTimer;
    let warningTimer;
    const warningTime = 5 * 60 * 1000; // 5 دقائق قبل انتهاء الجلسة

    // عناصر واجهة المستخدم
    let sessionWarningModal;
    let sessionTimer;

    // دالة لإعادة تعيين مؤقت الجلسة
    function resetSessionTimer() {
        // مسح المؤقتات الحالية
        clearTimeout(timeoutTimer);
        clearTimeout(warningTimer);

        // إخفاء رسالة التحذير إذا كانت ظاهرة
        if (sessionWarningModal) {
            sessionWarningModal.style.display = 'none';
        }

        // تعيين مؤقت تحذير جديد
        warningTimer = setTimeout(showSessionWarning, timeoutMs - warningTime);

        // تعيين مؤقت انتهاء الجلسة الجديد
        timeoutTimer = setTimeout(logout, timeoutMs);
    }

    // دالة لإظهار تحذير انتهاء الجلسة
    function showSessionWarning() {
        // إنشاء عنصر التحذير إذا لم يكن موجوداً
        if (!sessionWarningModal) {
            sessionWarningModal = document.createElement('div');
            sessionWarningModal.style.position = 'fixed';
            sessionWarningModal.style.top = '0';
            sessionWarningModal.style.left = '0';
            sessionWarningModal.style.width = '100%';
            sessionWarningModal.style.height = '100%';
            sessionWarningModal.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            sessionWarningModal.style.zIndex = '9999';
            sessionWarningModal.style.display = 'flex';
            sessionWarningModal.style.flexDirection = 'column';
            sessionWarningModal.style.justifyContent = 'center';
            sessionWarningModal.style.alignItems = 'center';
            sessionWarningModal.style.color = 'white';
            sessionWarningModal.style.fontFamily = 'Arial, sans-serif';
            sessionWarningModal.style.textAlign = 'center';
            sessionWarningModal.style.padding = '20px';

            const warningContent = document.createElement('div');
            warningContent.style.backgroundColor = '#f8f9fa';
            warningContent.style.color = '#212529';
            warningContent.style.padding = '30px';
            warningContent.style.borderRadius = '10px';
            warningContent.style.maxWidth = '500px';
            warningContent.style.width = '90%';

            const warningTitle = document.createElement('h2');
            warningTitle.textContent = 'تنبيه انتهاء الجلسة';
            warningTitle.style.color = '#dc3545';
            warningTitle.style.marginBottom = '20px';

            const warningText = document.createElement('p');
            warningText.textContent = 'ستنتهي جلستك خلال 5 دقائق بسبب عدم النشاط. هل تريد الاستمرار؟';
            warningText.style.marginBottom = '20px';

            const continueButton = document.createElement('button');
            continueButton.textContent = 'مواصلة الجلسة';
            continueButton.style.backgroundColor = '#28a745';
            continueButton.style.color = 'white';
            continueButton.style.border = 'none';
            continueButton.style.padding = '10px 20px';
            continueButton.style.borderRadius = '5px';
            continueButton.style.cursor = 'pointer';
            continueButton.style.marginRight = '10px';

            const logoutButton = document.createElement('button');
            logoutButton.textContent = 'تسجيل الخروج الآن';
            logoutButton.style.backgroundColor = '#dc3545';
            logoutButton.style.color = 'white';
            logoutButton.style.border = 'none';
            logoutButton.style.padding = '10px 20px';
            logoutButton.style.borderRadius = '5px';
            logoutButton.style.cursor = 'pointer';

            // إضافة عداد تنازلي
            const countdownContainer = document.createElement('div');
            countdownContainer.style.marginTop = '20px';
            countdownContainer.style.fontSize = '18px';
            countdownContainer.style.fontWeight = 'bold';

            const countdownText = document.createElement('span');
            countdownText.textContent = 'الوقت المتبقي: ';

            const countdownTimer = document.createElement('span');
            countdownTimer.id = 'session-countdown';
            countdownTimer.textContent = '5:00';

            countdownContainer.appendChild(countdownText);
            countdownContainer.appendChild(countdownTimer);

            // تجميع العناصر
            warningContent.appendChild(warningTitle);
            warningContent.appendChild(warningText);
            warningContent.appendChild(countdownContainer);

            const buttonContainer = document.createElement('div');
            buttonContainer.appendChild(continueButton);
            buttonContainer.appendChild(logoutButton);

            warningContent.appendChild(buttonContainer);
            sessionWarningModal.appendChild(warningContent);

            // إضافة العنصر إلى الصفحة
            document.body.appendChild(sessionWarningModal);

            // إضافة مستمعي الأحداث
            continueButton.addEventListener('click', function() {
                resetSessionTimer();
                sessionWarningModal.style.display = 'none';
            });

            logoutButton.addEventListener('click', logout);

            // بدء العد التنازلي
            startCountdown(countdownTimer);
        } else {
            sessionWarningModal.style.display = 'flex';
            // إعادة تعيين العد التنازلي
            const countdownElement = document.getElementById('session-countdown');
            if (countdownElement) {
                startCountdown(countdownElement);
            }
        }
    }

    // دالة لبدء العد التنازلي
    function startCountdown(element) {
        let timeLeft = 5 * 60; // 5 دقائق بالثواني

        // مسح أي عداد قديم
        if (sessionTimer) {
            clearInterval(sessionTimer);
        }

        sessionTimer = setInterval(function() {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;

            element.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

            if (timeLeft <= 0) {
                clearInterval(sessionTimer);
                logout();
            }

            timeLeft--;
        }, 1000);
    }

    // دالة لتسجيل الخروج
    function logout() {
        // إرسال طلب لتسجيل الخروج
        fetch('/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            // توجيه المستخدم إلى صفحة تسجيل الدخول المحددة
            window.location.href = 'http://9.9.9.94:5000/auth/login';
        })
        .catch(error => {
            console.error('Logout error:', error);
            // في حالة وجود خطأ، توجيه المستخدم anyway إلى صفحة تسجيل الدخول المحددة
            window.location.href = 'http://9.9.9.94:5000/auth/login';
        });
    }

    // إضافة مستمعي الأحداث لتتبع نشاط المستخدم
    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

    activityEvents.forEach(function(event) {
        document.addEventListener(event, resetSessionTimer, true);
    });

    // بدء مؤقت الجلسة عند تحميل الصفحة
    resetSessionTimer();
});
