-- إضافة حقول الحظر لجدول العملاء
-- نفذ هذه الأوامر في قاعدة البيانات instance/hotel.db

-- فحص إذا كانت الحقول موجودة أم لا
PRAGMA table_info(customers);

-- إضافة الحقول الجديدة
ALTER TABLE customers ADD COLUMN is_blocked INTEGER DEFAULT 0;
ALTER TABLE customers ADD COLUMN block_reason TEXT;
ALTER TABLE customers ADD COLUMN blocked_at DATETIME;
ALTER TABLE customers ADD COLUMN blocked_by TEXT;

-- تحديث القيم الافتراضية للسجلات الموجودة
UPDATE customers SET is_blocked = 0 WHERE is_blocked IS NULL;

-- فحص النتيجة
SELECT name, is_blocked, block_reason FROM customers LIMIT 5;
