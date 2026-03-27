-- إضافة حقول الحظر لجدول العملاء
-- قم بتشغيل هذه الأوامر في أي أداة SQLite

-- إضافة حقل is_blocked
ALTER TABLE customers ADD COLUMN is_blocked INTEGER DEFAULT 0;

-- إضافة حقل block_reason
ALTER TABLE customers ADD COLUMN block_reason TEXT;

-- إضافة حقل blocked_at
ALTER TABLE customers ADD COLUMN blocked_at DATETIME;

-- إضافة حقل blocked_by
ALTER TABLE customers ADD COLUMN blocked_by TEXT;

-- تحديث القيم الافتراضية
UPDATE customers SET is_blocked = 0 WHERE is_blocked IS NULL;

-- فحص النتيجة
SELECT name FROM pragma_table_info('customers') WHERE name LIKE '%block%';
