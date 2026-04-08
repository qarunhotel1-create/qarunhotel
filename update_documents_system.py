#!/usr/bin/env python3
"""
تحديث نظام الوثائق الجديد
يقوم بإنشاء الجداول الجديدة وتحديث البيانات الموجودة
"""

import os
import sys
from datetime import datetime

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import CustomerDocument

def update_documents_system():
    """تحديث نظام الوثائق"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 بدء تحديث نظام الوثائق...")
            
            # إنشاء الجداول الجديدة
            print("📋 إنشاء جداول قاعدة البيانات...")
            db.create_all()
            
            # التحقق من وجود جدول الوثائق
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'customer_documents' in tables:
                print("✅ جدول الوثائق موجود")
                
                # عرض إحصائيات الوثائق الحالية
                docs_count = CustomerDocument.query.count()
                print(f"📊 عدد الوثائق الحالية: {docs_count}")
                
                if docs_count > 0:
                    # إحصائيات تفصيلية
                    scanned_count = CustomerDocument.query.filter_by(is_scanned=True).count()
                    uploaded_count = CustomerDocument.query.filter_by(is_scanned=False).count()
                    
                    print(f"   - وثائق ممسوحة: {scanned_count}")
                    print(f"   - وثائق مرفوعة: {uploaded_count}")
                    
                    # تحديث الوثائق الموجودة لتتوافق مع النظام الجديد
                    print("🔧 تحديث الوثائق الموجودة...")
                    
                    documents = CustomerDocument.query.all()
                    updated_count = 0
                    
                    for doc in documents:
                        # تحديث الحقول الجديدة إذا لم تكن موجودة
                        if not hasattr(doc, 'status') or doc.status is None:
                            doc.status = 'active'
                            updated_count += 1
                        
                        if not hasattr(doc, 'scan_method') or doc.scan_method is None:
                            doc.scan_method = 'scan' if doc.is_scanned else 'upload'
                            updated_count += 1
                        
                        if not hasattr(doc, 'pages_count') or doc.pages_count is None:
                            doc.pages_count = doc.scan_pages_count if hasattr(doc, 'scan_pages_count') and doc.scan_pages_count else 1
                            updated_count += 1
                        
                        if not hasattr(doc, 'scan_resolution') or doc.scan_resolution is None:
                            doc.scan_resolution = 300
                            updated_count += 1
                    
                    if updated_count > 0:
                        db.session.commit()
                        print(f"✅ تم تحديث {updated_count} حقل في الوثائق الموجودة")
                    else:
                        print("✅ جميع الوثائق محدثة بالفعل")
                
            else:
                print("❌ جدول الوثائق غير موجود - سيتم إنشاؤه")
                db.create_all()
                print("✅ تم إنشاء جدول الوثائق")
            
            # التحقق من مجلد الرفع
            upload_folder = os.path.join('hotel', 'static', 'uploads', 'customers')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder, exist_ok=True)
                print(f"📁 تم إنشاء مجلد الرفع: {upload_folder}")
            else:
                print(f"📁 مجلد الرفع موجود: {upload_folder}")
            
            # عرض ملخص النظام الجديد
            print("\n" + "="*50)
            print("🎉 تم تحديث نظام الوثائق بنجاح!")
            print("="*50)
            print("✨ الميزات الجديدة:")
            print("   • رفع متعدد للوثائق")
            print("   • دعم جميع أنواع الملفات")
            print("   • ماسح ضوئي متقدم")
            print("   • مسح متعدد الصفحات")
            print("   • معاينة فورية")
            print("   • طباعة مباشرة")
            print("   • حذف ناعم للوثائق")
            print("   • إحصائيات تفصيلية")
            print("\n🔗 المسارات الجديدة:")
            print("   • /customers-new/ - النظام الجديد")
            print("   • /customers-new/create - إضافة عميل")
            print("   • /customers-new/<id> - تفاصيل العميل")
            print("   • /customers-new/<id>/edit - تعديل العميل")
            print("\n📝 ملاحظات:")
            print("   • النظام القديم لا يزال يعمل على /customers/")
            print("   • يمكن التبديل بين النظامين")
            print("   • البيانات محفوظة ومتوافقة")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحديث النظام: {str(e)}")
            db.session.rollback()
            return False

def test_new_system():
    """اختبار النظام الجديد"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n🧪 اختبار النظام الجديد...")
            
            # اختبار إنشاء وثيقة تجريبية
            from hotel.models import Customer
            
            # البحث عن عميل للاختبار
            test_customer = Customer.query.first()
            
            if test_customer:
                print(f"👤 عميل الاختبار: {test_customer.name}")
                print(f"📄 عدد الوثائق: {test_customer.documents_count}")
                print(f"📊 وثائق ممسوحة: {test_customer.scanned_documents_count}")
                print(f"📤 وثائق مرفوعة: {test_customer.uploaded_documents_count}")
                
                # عرض الوثائق
                if test_customer.has_documents:
                    print("📋 الوثائق الموجودة:")
                    for doc in test_customer.active_documents:
                        print(f"   • {doc.original_name} ({doc.file_size_formatted}) - {doc.scan_method_display}")
                
                print("✅ النظام يعمل بشكل صحيح")
            else:
                print("⚠️  لا يوجد عملاء للاختبار")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في اختبار النظام: {str(e)}")
            return False

if __name__ == '__main__':
    print("🏨 نظام إدارة الفندق - تحديث نظام الوثائق")
    print("="*50)
    
    # تحديث النظام
    if update_documents_system():
        # اختبار النظام
        test_new_system()
        
        print("\n🚀 النظام جاهز للاستخدام!")
        print("يمكنك الآن الوصول للنظام الجديد على:")
        print("http://localhost:5000/customers-new/")
    else:
        print("\n❌ فشل في تحديث النظام")
        sys.exit(1)