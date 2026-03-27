#!/usr/bin/env python3
"""
إنشاء migration لنظام الوثائق الجديد
"""

from hotel import create_app, db
from hotel.models import CustomerDocument, ScannedPage
import os

def create_migration():
    """إنشاء migration لنظام الوثائق الجديد"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 إنشاء جداول نظام الوثائق الجديد...")
        
        try:
            # إنشاء الجداول الجديدة
            db.create_all()
            
            # إنشاء مجلدات التحميل
            upload_dirs = [
                'hotel/static/uploads/customers',
                'hotel/static/uploads/customers/pages'
            ]
            
            for upload_dir in upload_dirs:
                os.makedirs(upload_dir, exist_ok=True)
                print(f"✅ تم إنشاء مجلد: {upload_dir}")
            
            print("✅ تم إنشاء جداول نظام الوثائق بنجاح!")
            print("\nالجداول المنشأة:")
            print("- customer_documents: جدول الوثائق الرئيسي")
            print("- scanned_pages: جدول صفحات المسح الضوئي")
            
            # إنشاء ملف .gitkeep في مجلدات التحميل
            for upload_dir in upload_dirs:
                gitkeep_path = os.path.join(upload_dir, '.gitkeep')
                with open(gitkeep_path, 'w') as f:
                    f.write('')
                print(f"✅ تم إنشاء .gitkeep في: {upload_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء الجداول: {str(e)}")
            return False

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 إنشاء نظام الوثائق الجديد")
    print("=" * 50)
    
    success = create_migration()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ تم إنشاء نظام الوثائق بنجاح!")
        print("يمكنك الآن استخدام النظام الجديد لإدارة وثائق العملاء")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ فشل في إنشاء نظام الوثائق!")
        print("يرجى مراجعة الأخطاء أعلاه")
        print("=" * 50)
