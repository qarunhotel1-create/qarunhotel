from hotel import create_app, db
from sqlalchemy import text

def update_id_number_nullable():
    """تحديث حقل id_number ليكون nullable=True"""
    app = create_app()
    
    with app.app_context():
        try:
            # تنفيذ استعلام SQL مباشر لتعديل قاعدة البيانات
            db.session.execute(text("PRAGMA foreign_keys=OFF;"))
            
            # إنشاء جدول جديد مع السماح بقيم فارغة لحقل id_number
            create_table_sql = """CREATE TABLE customers_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                id_number VARCHAR(20) UNIQUE,
                nationality VARCHAR(50),
                marital_status VARCHAR(20),
                gender VARCHAR(10),
                phone VARCHAR(20),
                address VARCHAR(200),
                is_blocked BOOLEAN DEFAULT 0 NOT NULL,
                block_reason VARCHAR(500),
                blocked_at DATETIME,
                blocked_by VARCHAR(100),
                created_at DATETIME,
                updated_at DATETIME
            );"""
            db.session.execute(text(create_table_sql))
            
            # نقل البيانات من الجدول القديم إلى الجدول الجديد
            db.session.execute(text("INSERT INTO customers_new SELECT * FROM customers;"))
            
            # حذف الجدول القديم وإعادة تسمية الجدول الجديد
            db.session.execute(text("DROP TABLE customers;"))
            db.session.execute(text("ALTER TABLE customers_new RENAME TO customers;"))
            
            # إعادة تفعيل قيود المفاتيح الخارجية
            db.session.execute(text("PRAGMA foreign_keys=ON;"))
            
            # تنفيذ التغييرات
            db.session.commit()
            
            print("✅ تم تحديث حقل id_number بنجاح ليسمح بالقيم الفارغة")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ حدث خطأ أثناء تحديث قاعدة البيانات: {e}")
            return False

if __name__ == "__main__":
    success = update_id_number_nullable()
    if success:
        print("🎉 تم تحديث قاعدة البيانات بنجاح! يمكنك الآن إضافة عملاء بدون رقم هوية.")
    else:
        print("❌ فشل في تحديث قاعدة البيانات. يرجى التحقق من السجلات للحصول على مزيد من المعلومات.")