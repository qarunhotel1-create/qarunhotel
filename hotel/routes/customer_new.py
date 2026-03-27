from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app, send_from_directory
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from flask_login import login_required, current_user
import os
import uuid
import json
import base64
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import io

from hotel import db
# from flask_wtf import csrf
from hotel.models import Customer
from hotel.models.document import CustomerDocument
from hotel.forms.customer import CustomerForm
from hotel.utils.decorators import permission_required
from sqlalchemy import or_

customer_new_bp = Blueprint('customer_new', __name__, url_prefix='/customers-new')

# مسار اختبار رفع الملفات الجذري
@customer_new_bp.route('/test-upload', methods=['POST'])
def test_upload():
    files = request.files.getlist('document_files')
    if not files or all(f.filename == '' for f in files):
        return "لم يتم استقبال أي ملف!", 400
    names = [f.filename for f in files]
    return f"تم استقبال الملفات التالية: {', '.join(names)}"

@customer_new_bp.route('/document/<int:doc_id>/view')
@login_required
@permission_required('manage_customers')
def view_document(doc_id):
    """عرض الوثيقة PDF مباشرة في نافذة بدون تحميل"""
    try:
        document = CustomerDocument.query.get_or_404(doc_id)
        if document.status != 'active':
            return ("<h3 style='color:red;text-align:center'>الوثيقة غير متاحة</h3>", 404)
        file_path = os.path.join(UPLOAD_FOLDER, document.filename)
        if not os.path.exists(file_path):
            return ("<h3 style='color:red;text-align:center'>الملف غير موجود</h3>", 404)
        # عرض PDF أو صورة مباشرة بدون تحميل
        from flask import send_file
        file_path = os.path.join(UPLOAD_FOLDER, document.filename)
        # حاول إرسال الملف للعرض inline. بعض المتصفحات قد تتجاهل ذلك إذا كانت الرؤوس تشير للتحميل.
        resp = None
        if document.is_pdf:
            resp = send_file(
                file_path,
                mimetype='application/pdf',
                as_attachment=False,
                conditional=True
            )
        elif document.is_image:
            resp = send_file(
                file_path,
                mimetype=document.mime_type,
                as_attachment=False,
                conditional=True
            )

        # إن تم إنشاء استجابة، أفرض Content-Disposition = inline لضمان العرض داخل المتصفح
        if resp is not None:
            try:
                resp.headers['Content-Disposition'] = f'inline; filename="{document.original_name}"'
            except Exception:
                pass
            return resp
        else:
            return ("<h3 style='color:red;text-align:center'>نوع الملف غير مدعوم للعرض المباشر</h3>", 400)
    except Exception as e:
        current_app.logger.error(f'Error viewing document: {str(e)}')
        return (f"<h3 style='color:red;text-align:center'>حدث خطأ في عرض الوثيقة: {str(e)}</h3>", 500)

# إعدادات رفع الملفات - بدون قيود على الحجم أو النوع أو العدد
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.abspath(os.path.join(BASE_DIR, '..', 'static', 'uploads', 'customers'))
MAX_FILES_PER_CUSTOMER = 100  # حد أقصى للوثائق لكل عميل
# تم إزالة جميع القيود - يقبل أي حجم وأي نوع ملف وأي عدد

def create_upload_folder():
    """إنشاء مجلد الرفع إذا لم يكن موجوداً"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_file_size(file):
    """الحصول على حجم الملف"""
    file.seek(0, 2)  # الانتقال لنهاية الملف
    size = file.tell()
    file.seek(0)  # العودة للبداية
    return size

@customer_new_bp.route('/')
@login_required
@permission_required('manage_customers')
def index():
    """قائمة العملاء"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    q = (request.args.get('q') or '').strip()

    base_query = Customer.query
    if q:
        like = f"%{q}%"
        base_query = base_query.filter(
            or_(
                Customer.name.ilike(like),
                Customer.id_number.ilike(like),
                Customer.phone.ilike(like)
            )
        )

    customers_pagination = base_query.order_by(Customer.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # إذا كان الطلب AJAX ونحتاج فقط الصفوف
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.args.get('partial') == 'rows':
        return render_template('customer/_index_rows.html', customers=customers_pagination)

    return render_template('customer/index_new.html', title='قائمة العملاء', customers=customers_pagination, q=q)

@customer_new_bp.route('/<int:id>')
@login_required
@permission_required('manage_customers')
def details(id):
    """تفاصيل العميل مع الوثائق"""
    customer = Customer.query.get_or_404(id)
    documents = customer.active_documents
    return render_template('customer/details_new.html', 
                         title=f'تفاصيل العميل - {customer.name}', 
                         customer=customer, 
                         documents=documents)

@customer_new_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('manage_customers')
def create():
    """إضافة عميل جديد مع نظام الوثائق المتقدم"""
    form = CustomerForm()
    if form.validate_on_submit():
        try:
            # تحديد الجنسية النهائية
            nationality = form.nationality.data
            if form.nationality.data == 'جنسية أخرى':
                if form.nationality_other.data:
                    nationality = form.nationality_other.data
            
            # إنشاء العميل
            id_number = form.id_number.data.strip() if form.id_number.data and form.id_number.data.strip() else None
            customer = Customer(
                name=form.name.data,
                id_number=id_number,
                phone=form.phone.data,
                nationality=nationality,
                gender=form.gender.data,
                marital_status=form.marital_status.data,
                address=form.address.data,
                created_by=current_user.full_name
            )
            db.session.add(customer)
            db.session.flush()  # للحصول على ID العميل
            
            # معالجة الوثائق المرفوعة
            documents_saved = process_customer_documents(customer, request)
            
            db.session.commit()
            
            if documents_saved > 0:
                flash(f'تم إضافة العميل بنجاح مع {documents_saved} وثيقة', 'success')
            else:
                flash('تم إضافة العميل بنجاح', 'success')
            
            # التحقق من وجود معامل next للعودة للصفحة المطلوبة
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('customer_new.details', id=customer.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating customer: {str(e)}', exc_info=True)
            flash(f'خطأ في إضافة العميل: {str(e)}', 'error')
            
    return render_template('customer/create_new.html', title='إضافة عميل جديد', form=form)

@customer_new_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('manage_customers')
def edit(id):
    """تعديل بيانات العميل مع إدارة الوثائق"""
    customer = Customer.query.get_or_404(id)
    form = CustomerForm(obj=customer)
    
    if request.method == 'POST' and form.validate_on_submit():
        print(f"[DEBUG] بدء عملية تعديل العميل {id}")
        try:
            # تحديث البيانات الأساسية
            customer.name = form.name.data
            customer.id_number = (form.id_number.data.strip() if form.id_number.data and form.id_number.data.strip() else None)
            customer.phone = form.phone.data
            
            # Determine final nationality
            nationality = form.nationality.data
            if form.nationality.data == 'جنسية أخرى':
                if form.nationality_other.data:
                    nationality = form.nationality_other.data
            customer.nationality = nationality

            customer.gender = form.gender.data
            customer.marital_status = form.marital_status.data
            customer.address = form.address.data
            customer.updated_by = current_user.full_name
            # حفظ الملاحظات من النموذج (إذا كانت موجودة)
            customer.notes = (request.form.get('notes') or '').strip() if request.form.get('notes') is not None else customer.notes
            customer.updated_at = datetime.utcnow()
            print("[DEBUG] تم تحديث البيانات الأساسية للعميل بما في ذلك الملاحظات.")
            
            # معالجة الوثائق الجديدة
            try:
                documents_saved = process_customer_documents(customer, request)
                print(f"[DEBUG] تم معالجة {documents_saved} وثيقة جديدة.")
                
                db.session.commit()
                print("[DEBUG] تم حفظ التغييرات في قاعدة البيانات.")
                
                if documents_saved > 0:
                    flash(f'تم تحديث العميل بنجاح مع إضافة {documents_saved} وثيقة جديدة', 'success')
                else:
                    flash('تم تحديث العميل بنجاح', 'success')
            except Exception as doc_error:
                # في حالة فشل معالجة الوثائق، احفظ بيانات العميل على الأقل
                db.session.commit()
                current_app.logger.error(f'Error processing documents during edit: {str(doc_error)}', exc_info=True)
                flash(f'تم تحديث بيانات العميل، لكن حدث خطأ في معالجة الوثائق: {str(doc_error)}', 'warning')
            
            print(f"[DEBUG] إعادة توجيه إلى تفاصيل العميل {customer.id}")
            return redirect(url_for('customer_new.details', id=customer.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating customer: {str(e)}', exc_info=True)
            flash(f'خطأ في تحديث العميل: {str(e)}', 'error')
    
    documents = customer.active_documents
    print(f"[DEBUG] عرض صفحة تعديل العميل {customer.id} مع {len(documents)} وثيقة نشطة.")
    return render_template('customer/edit_new.html',
                         title=f'تعديل العميل - {customer.name}',
                         form=form,
                         customer=customer,
                         documents=documents)

@customer_new_bp.route('/block/<int:customer_id>', methods=['POST'])
@login_required
def block_customer(customer_id):
    """حظر العميل"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # التحقق من وجود البيانات
        if request.is_json:
            data = request.get_json()
            reason = data.get('reason', '').strip() if data else ''
        else:
            reason = request.form.get('reason', '').strip()
        
        if not reason:
            return jsonify({'success': False, 'message': 'يجب إدخال سبب الحظر'})
        
        # الحقول موجودة الآن في قاعدة البيانات
        
        # حظر العميل
        success = customer.block_customer(reason, current_user.full_name)
        
        if success:
            return jsonify({'success': True, 'message': 'تم حظر العميل بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في حظر العميل'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@customer_new_bp.route('/unblock/<int:customer_id>', methods=['POST'])
@login_required
def unblock_customer(customer_id):
    """إلغاء حظر العميل"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # إلغاء حظر العميل
        success = customer.unblock_customer()
        
        if success:
            return jsonify({'success': True, 'message': 'تم إلغاء حظر العميل بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في إلغاء حظر العميل'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

def process_customer_documents(customer, request):
    """معالجة وثائق العميل من الطلب"""
    print("[DEBUG] بدء معالجة وثائق العميل")
    documents_saved = 0
    errors = []
    
    try:
        print("[DEBUG] Content-Type:", request.content_type)
        print("[DEBUG] request.files.keys():", list(request.files.keys()))
        print("[DEBUG] request.form.keys():", list(request.form.keys()))
        print("[DEBUG] Request form content:", dict(request.form))
        print("[DEBUG] Uploaded files:", list(request.files.keys()))
        uploaded_files = request.files.getlist('document_files')
        print(f"[DEBUG] Number of uploaded_files (document_files): {len(uploaded_files)}")
        create_upload_folder()
        new_documents = request.form.get('new_documents')
        new_documents_data = request.form.get('new_documents_data')
        documents_data = request.form.get('documents_data')
        documents_json = new_documents or new_documents_data or documents_data
        json_docs_present = False
        if documents_json:
            print(f"[DEBUG] JSON document data found. Length: {len(documents_json)} chars.")
            try:
                documents_list = json.loads(documents_json)
                print(f"[DEBUG] Number of documents in JSON: {len(documents_list)}")
                json_docs_present = isinstance(documents_list, list) and len(documents_list) > 0
                for i, doc_data in enumerate(documents_list):
                    print(f"[DEBUG] Processing document {i+1} from JSON: {doc_data.get('name', 'Unnamed')}, Method: {doc_data.get('method', 'Undefined')}")
                    try:
                        method = (doc_data.get('method') or doc_data.get('scan_method') or 'upload')
                        if method == 'upload':
                            doc = save_document_from_data(customer, doc_data)
                            if doc:
                                documents_saved += 1
                                print(f"[DEBUG] Uploaded document saved from JSON: {doc.original_name}")
                            else:
                                error_msg = f"فشل حفظ الوثيقة: {doc_data.get('name', 'ملف غير معروف')}\nقد يكون السبب اسم الملف أو نوع البيانات أو مشكلة في الترميز."
                                errors.append(error_msg)
                                flash(error_msg, 'danger')
                        elif method == 'scan':
                            doc = save_scanned_document_from_data(customer, doc_data)
                            if doc:
                                documents_saved += 1
                                print(f"[DEBUG] Scanned document saved from JSON: {doc.original_name}")
                            else:
                                error_msg = f"فشل حفظ المسح الضوئي: {doc_data.get('name', 'مسح غير معروف')}"
                                errors.append(error_msg)
                                flash(error_msg, 'danger')
                        else:
                            print(f"[DEBUG] Unknown method for document {doc_data.get('name', 'Unknown')}: {method}")
                    except Exception as e:
                        filename = doc_data.get('name', 'Unknown')
                        print(f"[DEBUG] خطأ في معالجة الوثيقة {filename}: {str(e)}")
                        print(f"[DEBUG] تفاصيل الخطأ الكاملة: {repr(e)}")
                        print(f"[DEBUG] نوع الخطأ: {type(e).__name__}")
                        try:
                            import time
                            safe_filename = f"document_{int(time.time())}_{hash(filename) % 10000}.jpg"
                            data_url = doc_data.get('data') or doc_data.get('content') or ''
                            if data_url and ',' in data_url:
                                try:
                                    header, encoded = data_url.split(',', 1)
                                    file_bytes = base64.b64decode(encoded)
                                    if len(file_bytes) > 0:
                                        unique_filename = CustomerDocument.generate_filename(safe_filename)
                                        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                                        with open(file_path, 'wb') as f:
                                            f.write(file_bytes)
                                        document = CustomerDocument(
                                            customer_id=customer.id,
                                            filename=unique_filename,
                                            original_name=safe_filename,
                                            file_type='image',
                                            file_extension='jpg',
                                            file_size=len(file_bytes),
                                            mime_type='image/jpeg',
                                            scan_method='upload',
                                            is_scanned=False,
                                            status='active'
                                        )
                                        db.session.add(document)
                                        documents_saved += 1
                                        print(f"[DEBUG] تم حفظ الملف بالطريقة البديلة: {safe_filename}")
                                        continue
                                except Exception as backup_error:
                                    print(f"[DEBUG] فشلت الطريقة البديلة أيضاً: {str(backup_error)}")
                        except Exception as rescue_error:
                            print(f"[DEBUG] فشل في محاولة الإنقاذ: {str(rescue_error)}")
                        error_msg = f"تم تخطي الملف: {filename} (خطأ في المعالجة)"
                        errors.append(error_msg)
                        flash(error_msg, 'danger')
                        current_app.logger.error(f"Error processing document {filename}: {str(e)}", exc_info=True)
            except json.JSONDecodeError as e:
                error_msg = f'JSON غير صالح في بيانات الوثائق: {str(e)}'
                errors.append(error_msg)
                flash(error_msg, 'danger')
                current_app.logger.warning(error_msg, exc_info=True)
        else:
            print("[DEBUG] No JSON document data found.")
        
        # تجنب الازدواج: إذا وُجدت وثائق JSON حقيقية (ليست فارغة)، نتجنب معالجة الرفع التقليدي
        use_json = bool(json_docs_present)

        if not use_json:
            # معالجة الملفات المرفوعة التقليدية (للتوافق مع النظام القديم)
            uploaded_files = request.files.getlist('document_files')
            allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'txt'}
            max_file_size = 10 * 1024 * 1024  # 10MB لكل ملف
            if not uploaded_files or all(not f or not f.filename for f in uploaded_files):
                # Allow proceeding without requiring any uploaded files on edit/create
                print("[DEBUG] No traditional uploaded files provided. Skipping without error.")
            else:
                print(f"[DEBUG] Found {len(uploaded_files)} traditional uploaded files.")
                for file in uploaded_files:
                    if not file or not file.filename:
                        errors.append('أحد الملفات المرفوعة فارغ أو بدون اسم. تم تجاهله.')
                        continue
                    filename = file.filename
                    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                    if ext not in allowed_extensions:
                        error_msg = f'نوع الملف غير مدعوم: {filename}'
                        errors.append(error_msg)
                        flash(error_msg, 'danger')
                        print(f"[DEBUG] {error_msg}")
                        continue
                    file.seek(0, 2)
                    file_size = file.tell()
                    file.seek(0)
                    if file_size == 0:
                        error_msg = f'الملف {filename} فارغ ولا يمكن رفعه.'
                        errors.append(error_msg)
                        flash(error_msg, 'danger')
                        print(f"[DEBUG] {error_msg}")
                        continue
                    if file_size > max_file_size:
                        error_msg = f'حجم الملف {filename} أكبر من الحد المسموح (10MB).'
                        errors.append(error_msg)
                        flash(error_msg, 'danger')
                        print(f"[DEBUG] {error_msg}")
                        continue
                    print(f"[DEBUG] Processing traditional uploaded file: {filename}, size: {file_size}")
                    doc = save_uploaded_document(customer, file, 'upload')
                    if doc:
                        documents_saved += 1
                    else:
                        errors.append(f"فشل حفظ الملف: {filename}")
        else:
            print("[DEBUG] Skipping traditional upload processing because JSON documents were provided.")

        # تجنب الازدواج أيضاً لمسح الوثائق التقليدي إذا تم استخدام JSON
        if not use_json:
            # معالجة الملفات الممسوحة ضوئياً التقليدية (للتوافق مع النظام القديم)
            scanned_data = request.form.get('scanned_documents')
            if scanned_data:
                print(f"[DEBUG] Found traditional scanned document data. Length: {len(scanned_data)} chars.")
                try:
                    scanned_list = json.loads(scanned_data)
                    print(f"[DEBUG] Number of traditional scanned documents: {len(scanned_list)}")
                    for scan_data in scanned_list:
                        doc = save_scanned_document(customer, scan_data)
                        if doc:
                            documents_saved += 1
                        else:
                            errors.append(f"Failed to save traditional scanned document: {scan_data.get('title', 'Unknown')}")
                except json.JSONDecodeError as e:
                    current_app.logger.warning(f'Invalid JSON in scanned_documents: {str(e)}', exc_info=True)
                    errors.append(f'Invalid JSON in scanned_documents: {str(e)}')
            else:
                print("[DEBUG] No traditional scanned document data found.")
        else:
            print("[DEBUG] Skipping traditional scanned document processing because JSON documents were provided.")

        if not use_json:
            # معالجة الملفات المتعددة من الماسح التقليدية (للتوافق مع النظام القديم)
            multi_scan_data = request.form.get('multi_scan_documents')
            if multi_scan_data:
                print(f"[DEBUG] Found traditional multi-scan document data. Length: {len(multi_scan_data)} chars.")
                try:
                    multi_scan_list = json.loads(multi_scan_data)
                    print(f"[DEBUG] Number of traditional multi-scan documents: {len(multi_scan_list)}")
                    for multi_data in multi_scan_list:
                        doc = save_multi_scan_document(customer, multi_data)
                        if doc:
                            documents_saved += 1
                        else:
                            errors.append(f"Failed to save traditional multi-scan document: {multi_data.get('title', 'Unknown')}")
                except json.JSONDecodeError as e:
                    current_app.logger.warning(f'Invalid JSON in multi_scan_documents: {str(e)}', exc_info=True)
                    errors.append(f'Invalid JSON in multi_scan_documents: {str(e)}')
            else:
                print("[DEBUG] No traditional multi-scan document data found.")
        else:
            print("[DEBUG] Skipping traditional multi-scan document processing because JSON documents were provided.")
                
    except Exception as e:
        error_msg = f'Error processing documents: {str(e)}'
        errors.append(error_msg)
        current_app.logger.error(error_msg, exc_info=True)
    
    print(f"[DEBUG] Number of documents added: {documents_saved}")
    if errors:
        print(f"[DEBUG] Errors: {errors}")
        # يمكن إضافة الأخطاء إلى flash messages هنا إذا لزم الأمر
        for error in errors[:3]:  # عرض أول 3 أخطاء فقط
            flash(error, 'warning')
    
    return documents_saved

def save_uploaded_document(customer, file, scan_method='upload'):
    """حفظ وثيقة مرفوعة - بدون قيود على النوع أو الحجم"""
    print(f"[DEBUG] بدء save_uploaded_document لـ: {file.filename}")
    try:
        # إزالة فحص نوع الملف - يقبل جميع الأنواع
        # إزالة فحص حجم الملف - يقبل أي حجم
        file_size = get_file_size(file)
        print(f"[DEBUG] حجم الملف: {file_size} بايت")
        
        # إنشاء اسم ملف فريد
        original_filename = secure_filename(file.filename)
        unique_filename = CustomerDocument.generate_filename(original_filename)
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        print(f"[DEBUG] المسار الفريد للملف: {file_path}")
        
        # حفظ الملف
        file.save(file_path)
        print(f"[DEBUG] تم حفظ الملف في: {file_path}")
        
        # التحقق من حفظ الملف
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            print(f"[DEBUG] فشل التحقق من الملف: {file_path} غير موجود أو فارغ.")
            return None
        print(f"[DEBUG] تم التحقق من الملف بنجاح: {os.path.getsize(file_path)} بايت")
        
        # إنشاء سجل الوثيقة
        document = CustomerDocument(
            customer_id=customer.id,
            filename=unique_filename,
            original_name=original_filename,
            file_type=CustomerDocument.get_file_type(file.content_type),
            file_extension=original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else '',
            file_size=file_size,
            mime_type=file.content_type,
            scan_method=scan_method,
            is_scanned=(scan_method != 'upload'),
            status='active'
        )
        print(f"[DEBUG] تم إنشاء سجل الوثيقة لـ: {document.original_name}")
        
        db.session.add(document)
        print("[DEBUG] تم إضافة الوثيقة إلى الجلسة.")
        return document
        
    except Exception as e:
        current_app.logger.error(f'Error saving uploaded document: {str(e)}', exc_info=True)
        print(f"[DEBUG] خطأ في save_uploaded_document: {str(e)}")
        return None

# استيراد الدالة المحسنة
from hotel.routes.document_save_patch import enhanced_save_document_from_data

def save_document_from_data(customer, doc_data):
    """حفظ وثيقة من بيانات الجافا سكريبت - تم استبدالها بالنسخة المحسنة"""
    # استدعاء الدالة المحسنة بدلاً من التنفيذ الأصلي
    return enhanced_save_document_from_data(customer, doc_data)
    
    # تم تعطيل الكود القديم
    # معالجة شاملة للأخطاء مع تفاصيل كاملة
    try:
        # التحقق من صحة البيانات الأساسية
        if not doc_data:
            print("[DEBUG] doc_data فارغ")
            return None
            
        if not isinstance(doc_data, dict):
            print(f"[DEBUG] doc_data ليس dictionary: {type(doc_data)}")
            return None
        
        # استخراج البيانات مع قيم افتراضية آمنة
        data_url = doc_data.get('data', '')
        filename = doc_data.get('name', 'document.file')
        file_size = doc_data.get('size', 0)
        mime_type = doc_data.get('type', 'application/octet-stream')
        
        print(f"[DEBUG] البيانات المستخرجة:")
        print(f"  - اسم الملف: '{filename}'")
        print(f"  - الحجم: {file_size}")
        print(f"  - النوع: '{mime_type}'")
        print(f"  - طول data_url: {len(data_url) if data_url else 0}")
        
        # التحقق من البيانات الأساسية
        if not data_url:
            print("[DEBUG] data_url فارغ")
            flash('فشل حفظ الوثيقة: البيانات المرسلة من المتصفح فارغة. حاول إعادة رفع الملف.', 'danger')
            return None
            
        if not filename or filename.strip() == '':
            print("[DEBUG] اسم الملف فارغ")
            flash('فشل حفظ الوثيقة: اسم الملف فارغ أو غير صالح.', 'danger')
            filename = 'document.file'
        
        # معالجة اسم الملف بشكل آمن تماماً
        try:
            import re
            import unicodedata
            
            # إزالة الأحرف غير المرئية والتحكم
            filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')
            
            # تنظيف شامل لاسم الملف
            clean_filename = filename.strip()
            
            # استبدال جميع الأحرف الخاصة والمسافات
            clean_filename = re.sub(r'[^\w\-_.]', '_', clean_filename)
            
            # تقليل الشرطات السفلية المتعددة
            clean_filename = re.sub(r'_+', '_', clean_filename)
            
            # إزالة الشرطات من البداية والنهاية
            clean_filename = clean_filename.strip('_')
            
            # التأكد من وجود اسم ملف صالح
            if not clean_filename or clean_filename == '':
                clean_filename = 'document'
            
            # التأكد من وجود امتداد
            if '.' not in clean_filename:
                if mime_type.startswith('image/'):
                    if 'jpeg' in mime_type or 'jpg' in mime_type:
                        clean_filename += '.jpg'
                    elif 'png' in mime_type:
                        clean_filename += '.png'
                    else:
                        clean_filename += '.jpg'
                elif mime_type == 'application/pdf':
                    clean_filename += '.pdf'
                else:
                    clean_filename += '.file'
            
            print(f"[DEBUG] اسم الملف بعد التنظيف: '{clean_filename}'")
            
        except Exception as e:
            print(f"[DEBUG] خطأ في تنظيف اسم الملف: {str(e)}")
            clean_filename = 'document.file'
        
        # فك تشفير base64 مع معالجة شاملة
        try:
            if not data_url.startswith('data:'):
                print("[DEBUG] تنسيق البيانات غير صحيح (لا تبدأ بـ 'data:')")
                flash('فشل حفظ الوثيقة: تنسيق البيانات غير صحيح (data_url).', 'danger')
                return None
            
            # تقسيم البيانات
            if ',' not in data_url:
                print("[DEBUG] تنسيق data_url غير صحيح (لا يحتوي على فاصلة)")
                flash('فشل حفظ الوثيقة: البيانات المرسلة غير مكتملة (data_url).', 'danger')
                return None
                
            header, encoded = data_url.split(',', 1)
            
            if not encoded or encoded.strip() == '':
                print("[DEBUG] البيانات المشفرة فارغة")
                flash('فشل حفظ الوثيقة: البيانات المشفرة فارغة (base64).', 'danger')
                return None
            
            # فك التشفير مع معالجة الأخطاء المحتملة
            try:
                file_bytes = base64.b64decode(encoded)
            except Exception as decode_error:
                print(f"[DEBUG] خطأ في فك تشفير base64: {str(decode_error)}")
                # محاولة إصلاح البيانات المشفرة
                encoded = encoded.replace(' ', '+')  # استبدال المسافات بعلامات +
                try:
                    file_bytes = base64.b64decode(encoded)
                    print("[DEBUG] تم إصلاح البيانات المشفرة ونجح فك التشفير")
                except Exception as retry_error:
                    print(f"[DEBUG] فشل في إصلاح البيانات المشفرة: {str(retry_error)}")
                    flash('فشل حفظ الوثيقة: خطأ في فك تشفير البيانات.', 'danger')
                    return None
            
            print(f"[DEBUG] تم فك تشفير {len(file_bytes)} بايت من base64")
            
            if len(file_bytes) == 0:
                print("[DEBUG] الملف فارغ بعد فك التشفير")
                flash('فشل حفظ الوثيقة: الملف فارغ بعد فك التشفير. تأكد من أن الملف ليس فارغاً.', 'danger')
                return None
                
        except Exception as e:
            print(f"[DEBUG] خطأ في فك التشفير base64: {str(e)}")
            current_app.logger.error(f'Error decoding base64 data for file {filename}: {str(e)}', exc_info=True)
            flash(f'فشل حفظ الوثيقة: قد يكون السبب اسم الملف أو نوع البيانات أو مشكلة في الترميز.', 'danger')
            
            # محاولة طارئة للحفظ
            try:
                import time
                emergency_filename = f"emergency_file_{int(time.time())}.jpg"
                
                if data_url and ',' in data_url:
                    header, encoded = data_url.split(',', 1)
                    try:
                        # محاولة إصلاح البيانات المشفرة
                        encoded = encoded.replace(' ', '+')  # استبدال المسافات بعلامات +
                        file_bytes = base64.b64decode(encoded)
                        
                        if len(file_bytes) > 0:
                            unique_filename = f"emrg_{int(time.time())}_{len(file_bytes)}.jpg"
                            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                            
                            # التأكد من وجود المجلد
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            
                            with open(file_path, 'wb') as f:
                                f.write(file_bytes)
                            
                            # إنشاء سجل بسيط
                            document = CustomerDocument(
                                customer_id=customer.id,
                                filename=unique_filename,
                                original_name=emergency_filename,
                                file_type='image',
                                file_extension='jpg',
                                file_size=len(file_bytes),
                                mime_type='image/jpeg',
                                scan_method='upload',
                                is_scanned=False,
                                status='active'
                            )
                            
                            db.session.add(document)
                            print(f"[DEBUG] تم حفظ الملف بالطريقة الطارئة: {emergency_filename}")
                            return document
                    except Exception as emergency_error:
                        print(f"[DEBUG] فشلت المحاولة الطارئة: {str(emergency_error)}")
            except Exception as emergency_error:
                print(f"[DEBUG] فشلت المحاولة الطارئة: {str(emergency_error)}")
            
            return None
        
        # إنشاء مسار الملف مع معالجة آمنة
        try:
            original_filename = secure_filename(clean_filename)
            if not original_filename:
                original_filename = 'document.file'
                
            unique_filename = CustomerDocument.generate_filename(original_filename)
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            print(f"[DEBUG] المسار الفريد للملف: {file_path}")
            
        except Exception as e:
            print(f"[DEBUG] خطأ في إنشاء مسار الملف: {str(e)}")
            flash(f'فشل حفظ الوثيقة: خطأ في إنشاء مسار الملف: {str(e)}', 'danger')
            return None
        
        # حفظ الملف
        try:
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            print(f"[DEBUG] تم حفظ الملف في: {file_path}")
        except Exception as e:
            print(f"[DEBUG] خطأ في حفظ الملف على القرص: {str(e)}")
            current_app.logger.error(f'Error writing file to disk: {str(e)}', exc_info=True)
            
            # محاولة إنشاء المجلد مرة أخرى
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb') as f:
                    f.write(file_bytes)
                print(f"[DEBUG] تم حفظ الملف في المحاولة الثانية: {file_path}")
            except Exception as retry_error:
                print(f"[DEBUG] فشل في المحاولة الثانية لحفظ الملف: {str(retry_error)}")
                flash(f'فشل حفظ الوثيقة: خطأ في كتابة الملف على القرص.', 'danger')
                return None
        
        # التحقق من حفظ الملف
        if not os.path.exists(file_path):
            print(f"[DEBUG] الملف غير موجود بعد الحفظ: {file_path}")
            flash('فشل حفظ الوثيقة: الملف غير موجود بعد الحفظ.', 'danger')
            return None
        
        actual_size = os.path.getsize(file_path)
        if actual_size == 0:
            print(f"[DEBUG] الملف فارغ بعد الحفظ: {file_path}")
            flash('فشل حفظ الوثيقة: الملف فارغ بعد الحفظ.', 'danger')
            os.remove(file_path)
            return None
        
        print(f"[DEBUG] تم التحقق من الملف بنجاح: {actual_size} بايت")
        
        # إنشاء سجل الوثيقة
        document = CustomerDocument(
            customer_id=customer.id,
            filename=unique_filename,
            original_name=original_filename,
            file_type=CustomerDocument.get_file_type(mime_type),
            file_extension=original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else '',
            file_size=len(file_bytes), # استخدم len(file_bytes) للحجم الفعلي للبيانات
            mime_type=mime_type,
            scan_method='upload',
            is_scanned=False,
            status='active'
        )
        print(f"[DEBUG] تم إنشاء سجل الوثيقة لـ: {document.original_name}")
        
        db.session.add(document)
        print("[DEBUG] تم إضافة الوثيقة إلى الجلسة.")
        return document
        
    except Exception as e:
        # معالجة جذرية - محاولة أخيرة لحفظ الملف
        print(f"[DEBUG] خطأ عام في save_document_from_data: {str(e)}")
        print(f"[DEBUG] محاولة حفظ طارئة للملف...")
        
        try:
            # محاولة أخيرة بأبسط طريقة ممكنة
            import time
            emergency_filename = f"emergency_file_{int(time.time())}.jpg"
            
            data_url = doc_data.get('data', '') if doc_data else ''
            if data_url and ',' in data_url:
                header, encoded = data_url.split(',', 1)
                file_bytes = base64.b64decode(encoded)
                
                if len(file_bytes) > 0:
                    unique_filename = f"emrg_{int(time.time())}_{len(file_bytes)}.jpg"
                    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_bytes)
                    
                    # إنشاء سجل بسيط
                    document = CustomerDocument(
                        customer_id=customer.id,
                        filename=unique_filename,
                        original_name=emergency_filename,
                        file_type='image',
                        file_extension='jpg',
                        file_size=len(file_bytes),
                        mime_type='image/jpeg',
                        scan_method='upload',
                        is_scanned=False,
                        status='active'
                    )
                    
                    db.session.add(document)
                    print(f"[DEBUG] تم حفظ الملف بالطريقة الطارئة: {emergency_filename}")
                    return document
                    
        except Exception as emergency_error:
            print(f"[DEBUG] فشلت المحاولة الطارئة: {str(emergency_error)}")
        
        current_app.logger.error(f'Error saving document from data: {str(e)}', exc_info=True)
        return None

def save_scanned_document_from_data(customer, doc_data):
    """حفظ وثيقة ممسوحة ضوئياً من بيانات الجافا سكريبت"""
    print("[DEBUG] بدء save_scanned_document_from_data")
    try:
        # استخراج البيانات
        scan_data = doc_data.get('data', [])
        filename = doc_data.get('name', 'مسح ضوئي')
        pages_count = doc_data.get('pages', 1)
        print(f"[DEBUG] بيانات المسح: {filename}, عدد الصفحات: {pages_count}")
        
        if not scan_data:
            print("[DEBUG] لا توجد بيانات مسح.")
            return None
        
        # إذا كانت صفحة واحدة
        if isinstance(scan_data, str):
            print("[DEBUG] معالجة صفحة واحدة ممسوحة ضوئياً.")
            return save_single_scanned_page(customer, scan_data, filename)
        
        # إذا كانت عدة صفحات
        elif isinstance(scan_data, list) and len(scan_data) > 0:
            if len(scan_data) == 1:
                print("[DEBUG] معالجة قائمة بصفحة واحدة ممسوحة ضوئياً.")
                return save_single_scanned_page(customer, scan_data[0], filename)
            else:
                print(f"[DEBUG] معالجة مسح متعدد الصفحات ({len(scan_data)} صفحة).")
                return save_multi_page_scan(customer, scan_data, filename)
        
        print("[DEBUG] تنسيق بيانات المسح غير مدعوم.")
        return None
        
    except Exception as e:
        current_app.logger.error(f'Error saving scanned document from data: {str(e)}', exc_info=True)
        print(f"[DEBUG] خطأ في save_scanned_document_from_data: {str(e)}")
        return None

def save_single_scanned_page(customer, image_data, title):
    """حفظ صفحة ممسوحة واحدة"""
    print(f"[DEBUG] بدء save_single_scanned_page لـ: {title}")
    try:
        if not image_data:
            print("[DEBUG] لا توجد بيانات صورة للصفحة الممسوحة.")
            return None
        
        # فك تشفير base64
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        print(f"[DEBUG] تم فك تشفير {len(image_bytes)} بايت من صورة الصفحة الممسوحة.")
        
        # إنشاء اسم ملف فريد
        unique_filename = f"scan_{customer.id}_{uuid.uuid4().hex[:8]}.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        print(f"[DEBUG] المسار الفريد لصفحة المسح: {file_path}")
        
        # حفظ الصورة
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        print(f"[DEBUG] تم حفظ صورة الصفحة الممسوحة في: {file_path}")
        
        # إنشاء سجل الوثيقة
        document = CustomerDocument(
            customer_id=customer.id,
            filename=unique_filename,
            original_name=f'{title}.jpg',
            file_type='image',
            file_extension='jpg',
            file_size=len(image_bytes),
            mime_type='image/jpeg',
            document_title=title,
            scan_method='scan',
            is_scanned=True,
            scan_quality='high',
            scan_resolution=300,
            status='active'
        )
        print(f"[DEBUG] تم إنشاء سجل وثيقة لصفحة المسح: {document.original_name}")
        
        db.session.add(document)
        print("[DEBUG] تم إضافة وثيقة صفحة المسح إلى الجلسة.")
        return document
        
    except Exception as e:
        current_app.logger.error(f'Error saving single scanned page: {str(e)}', exc_info=True)
        print(f"[DEBUG] خطأ في save_single_scanned_page: {str(e)}")
        return None

def save_multi_page_scan(customer, pages_data, title):
    """حفظ مسح متعدد الصفحات"""
    print(f"[DEBUG] بدء save_multi_page_scan لـ: {title} ({len(pages_data)} صفحة)")
    try:
        if not pages_data or len(pages_data) == 0:
            print("[DEBUG] لا توجد بيانات صفحات للمسح المتعدد.")
            return None
        
        # إنشاء اسم ملف فريد
        unique_filename = f"multiscan_{customer.id}_{uuid.uuid4().hex[:8]}.pdf"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        print(f"[DEBUG] المسار الفريد لملف PDF متعدد الصفحات: {file_path}")
        
        # إنشاء PDF متعدد الصفحات
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from PIL import Image
        import io
        
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        
        for i, page_data in enumerate(pages_data):
            print(f"[DEBUG] معالجة الصفحة {i+1} من المسح المتعدد.")
            if page_data.startswith('data:image/'):
                page_data = page_data.split(',')[1]
            
            # فك تشفير الصورة
            image_bytes = base64.b64decode(page_data)
            
            # تحويل إلى PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # حفظ الصورة مؤقتاً
            temp_image_path = os.path.join(UPLOAD_FOLDER, f"temp_page_{i}_{uuid.uuid4().hex[:8]}.jpg")
            print(f"[DEBUG] حفظ الصورة المؤقتة لصفحة المسح: {temp_image_path}")
            image.save(temp_image_path, 'JPEG')
            
            # إضافة الصورة للـ PDF
            c.drawImage(temp_image_path, 0, 0, width, height)
            c.showPage()
            
            # حذف الملف المؤقت
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
                print(f"[DEBUG] تم حذف الملف المؤقت: {temp_image_path}")
        
        c.save()
        print(f"[DEBUG] تم حفظ ملف PDF متعدد الصفحات في: {file_path}")
        
        # إنشاء سجل الوثيقة
        file_size = os.path.getsize(file_path)
        document = CustomerDocument(
            customer_id=customer.id,
            filename=unique_filename,
            original_name=f'{title}.pdf',
            file_type='pdf',
            file_extension='pdf',
            file_size=file_size,
            mime_type='application/pdf',
            document_title=title,
            scan_method='multi_scan',
            is_scanned=True,
            pages_count=len(pages_data),
            scan_quality='high',
            scan_resolution=300,
            status='active'
        )
        print(f"[DEBUG] تم إنشاء سجل وثيقة للمسح المتعدد: {document.original_name}")
        
        db.session.add(document)
        print("[DEBUG] تم إضافة وثيقة المسح المتعدد إلى الجلسة.")
        return document
        
    except Exception as e:
        current_app.logger.error(f'Error creating multi-page scan: {str(e)}', exc_info=True)
        print(f"[DEBUG] خطأ في save_multi_page_scan: {str(e)}")
        return None

def save_scanned_document(customer, scan_data):
    """حفظ وثيقة ممسوحة ضوئياً"""
    try:
        image_data = scan_data.get('data', '')
        title = scan_data.get('title', 'مسح ضوئي')
        
        if not image_data:
            return None
        
        # فك تشفير base64
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # إنشاء اسم ملف فريد
        unique_filename = f"scan_{customer.id}_{uuid.uuid4().hex[:8]}.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # حفظ الصورة
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        # إنشاء سجل الوثيقة
        document = CustomerDocument(
            customer_id=customer.id,
            filename=unique_filename,
            original_name=f'{title}.jpg',
            file_type='image',
            file_extension='jpg',
            file_size=len(image_bytes),
            mime_type='image/jpeg',
            document_title=title,
            scan_method='scan',
            is_scanned=True,
            scan_quality='high',
            scan_resolution=300
        )
        
        db.session.add(document)
        return document
        
    except Exception as e:
        current_app.logger.error(f'Error saving scanned document: {str(e)}')
        return None

def save_multi_scan_document(customer, multi_data):
    """حفظ وثيقة متعددة الصفحات من الماسح"""
    try:
        pages = multi_data.get('pages', [])
        title = multi_data.get('title', 'مسح متعدد الصفحات')
        
        if not pages:
            return None
        
        # دمج الصفحات في ملف PDF واحد
        if len(pages) > 1:
            return save_multi_page_pdf(customer, pages, title)
        else:
            # صفحة واحدة فقط
            return save_scanned_document(customer, {
                'data': pages[0],
                'title': title
            })
            
    except Exception as e:
        current_app.logger.error(f'Error saving multi-scan document: {str(e)}')
        return None

def save_multi_page_pdf(customer, pages, title):
    """دمج عدة صفحات في ملف PDF واحد"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        # إنشاء اسم ملف فريد
        unique_filename = f"multiscan_{customer.id}_{uuid.uuid4().hex[:8]}.pdf"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # إنشاء PDF
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        
        for i, page_data in enumerate(pages):
            if page_data.startswith('data:image/'):
                page_data = page_data.split(',')[1]
            
            # فك تشفير الصورة
            image_bytes = base64.b64decode(page_data)
            
            # تحويل إلى PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # حفظ الصورة مؤقتاً
            temp_image_path = f"temp_page_{i}.jpg"
            image.save(temp_image_path, 'JPEG')
            
            # إضافة الصورة للـ PDF
            c.drawImage(temp_image_path, 0, 0, width, height)
            c.showPage()
            
            # حذف الملف المؤقت
            os.remove(temp_image_path)
        
        c.save()
        
        # إنشاء سجل الوثيقة
        file_size = os.path.getsize(file_path)
        document = CustomerDocument(
            customer_id=customer.id,
            filename=unique_filename,
            original_name=f'{title}.pdf',
            file_type='pdf',
            file_extension='pdf',
            file_size=file_size,
            mime_type='application/pdf',
            document_title=title,
            scan_method='multi_scan',
            is_scanned=True,
            pages_count=len(pages),
            scan_quality='high',
            scan_resolution=300
        )
        
        db.session.add(document)
        return document
        
    except Exception as e:
        current_app.logger.error(f'Error creating multi-page PDF: {str(e)}')
        return None

# API Routes للوثائق

@customer_new_bp.route('/api/upload-documents', methods=['POST'])
@login_required
@permission_required('manage_customers')
def api_upload_documents():
    """API لرفع عدة وثائق"""
    try:
        customer_id = request.form.get('customer_id')
        if not customer_id:
            return jsonify({'success': False, 'message': 'معرف العميل مطلوب'})
        
        customer = Customer.query.get_or_404(customer_id)
        
        # التحقق من عدد الوثائق الحالية
        current_docs_count = customer.documents_count
        if current_docs_count >= MAX_FILES_PER_CUSTOMER:
            return jsonify({'success': False, 'message': f'تم الوصول للحد الأقصى من الوثائق ({MAX_FILES_PER_CUSTOMER})'})
        
        files = request.files.getlist('documents')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'success': False, 'message': 'لم يتم اختيار ملفات'})
        
        # التحقق من عدم تجاوز الحد الأقصى
        if current_docs_count + len(files) > MAX_FILES_PER_CUSTOMER:
            allowed_count = MAX_FILES_PER_CUSTOMER - current_docs_count
            return jsonify({'success': False, 'message': f'يمكن رفع {allowed_count} ملف فقط'})
        
        create_upload_folder()
        
        uploaded_docs = []
        errors = []
        
        for file in files:
            if file and file.filename:
                doc = save_uploaded_document(customer, file)
                if doc:
                    uploaded_docs.append({
                        'id': doc.id,
                        'filename': doc.filename,
                        'original_name': doc.original_name,
                        'file_type': doc.file_type,
                        'file_size': doc.file_size_formatted,
                        'upload_date': doc.upload_date.strftime('%Y-%m-%d %H:%M')
                    })
                else:
                    errors.append(f'فشل في رفع: {file.filename}')
        
        if uploaded_docs:
            db.session.commit()
        
        return jsonify({
            'success': len(uploaded_docs) > 0,
            'message': f'تم رفع {len(uploaded_docs)} وثيقة بنجاح',
            'documents': uploaded_docs,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in api_upload_documents: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في النظام: {str(e)}'})

@customer_new_bp.route('/api/scanner-capture', methods=['POST'])
@login_required
@permission_required('manage_customers')
def api_scanner_capture():
    """API للمسح الضوئي من الطابعة"""
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        images = data.get('images', [])
        title = data.get('title', 'مسح ضوئي')
        
        if not customer_id:
            return jsonify({'success': False, 'message': 'معرف العميل مطلوب'})
        
        if not images:
            return jsonify({'success': False, 'message': 'لا توجد صور للمسح'})
        
        customer = Customer.query.get_or_404(customer_id)
        
        # التحقق من عدد الوثائق
        if customer.documents_count >= MAX_FILES_PER_CUSTOMER:
            return jsonify({'success': False, 'message': f'تم الوصول للحد الأقصى من الوثائق ({MAX_FILES_PER_CUSTOMER})'})
        
        create_upload_folder()
        
        # حفظ الوثيقة الممسوحة
        if len(images) == 1:
            # صفحة واحدة
            doc = save_scanned_document(customer, {
                'data': images[0],
                'title': title
            })
        else:
            # عدة صفحات
            doc = save_multi_scan_document(customer, {
                'pages': images,
                'title': title
            })
        
        if doc:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'تم مسح الوثيقة بنجاح ({len(images)} صفحة)',
                'document': {
                    'id': doc.id,
                    'filename': doc.filename,
                    'original_name': doc.original_name,
                    'file_type': doc.file_type,
                    'pages_count': doc.pages_count,
                    'scan_method': doc.scan_method_display
                }
            })
        else:
            return jsonify({'success': False, 'message': 'فشل في حفظ الوثيقة'})
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in api_scanner_capture: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في المسح: {str(e)}'})

@customer_new_bp.route('/api/document/<int:doc_id>/preview')
@login_required
@permission_required('manage_customers')
def api_document_preview(doc_id):
    """API لمعاينة الوثيقة"""
    try:
        document = CustomerDocument.query.get_or_404(doc_id)
        
        # التحقق من الصلاحية
        if document.status != 'active':
            return jsonify({'success': False, 'message': 'الوثيقة غير متاحة'})
        
        return jsonify({
            'success': True,
            'document': {
                'id': document.id,
                'filename': document.filename,
                'original_name': document.original_name,
                'file_type': document.file_type,
                'file_size': document.file_size_formatted,
                'file_url': document.file_url,
                'is_image': document.is_image,
                'is_pdf': document.is_pdf,
                'upload_date': document.upload_date.strftime('%Y-%m-%d %H:%M'),
                'scan_method': document.scan_method_display,
                'pages_count': document.pages_count
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in api_document_preview: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في المعاينة: {str(e)}'})

@customer_new_bp.route('/api/upload-documents-v2', methods=['POST'])
@login_required
@permission_required('manage_customers')
def api_upload_documents_v2():
    """API لرفع الوثائق - الإصدار الثاني"""
    try:
        customer_id = request.form.get('customer_id')
        if not customer_id:
            return jsonify({'success': False, 'message': 'معرف العميل مطلوب'})
        
        customer = Customer.query.get_or_404(customer_id)
        
        # إنشاء مجلد الرفع
        create_upload_folder()
        
        uploaded_files = request.files.getlist('documents')
        documents_saved = 0
        errors = []
        
        for file in uploaded_files:
            if file and file.filename:
                try:
                    doc = save_uploaded_document(customer, file, 'upload')
                    if doc:
                        documents_saved += 1
                    else:
                        errors.append(f'فشل في حفظ {file.filename}')
                except Exception as e:
                    errors.append(f'خطأ في {file.filename}: {str(e)}')
        
        if documents_saved > 0:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'تم رفع {documents_saved} وثيقة بنجاح',
                'uploaded_count': documents_saved,
                'errors': errors if errors else None
            })
        else:
            return jsonify({
                'success': False,
                'message': 'فشل في رفع الوثائق',
                'errors': errors
            })
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in api_upload_documents_v2: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في النظام: {str(e)}'})

@customer_new_bp.route('/api/test-upload', methods=['POST'])
@login_required
@permission_required('manage_customers')
def api_test_upload():
    """API لاختبار رفع الملفات"""
    try:
        print("[DEBUG] اختبار رفع الملفات")
        print(f"[DEBUG] request.form: {dict(request.form)}")
        print(f"[DEBUG] request.files: {list(request.files.keys())}")
        
        # فحص البيانات المرسلة
        customer_id = request.form.get('customer_id')
        new_documents_data = request.form.get('new_documents_data')
        
        if new_documents_data:
            try:
                documents_list = json.loads(new_documents_data)
                print(f"[DEBUG] عدد الوثائق في JSON: {len(documents_list)}")
                for i, doc in enumerate(documents_list):
                    print(f"[DEBUG] وثيقة {i+1}: {doc.get('name', 'بدون اسم')}, الحجم: {doc.get('size', 0)}")
            except json.JSONDecodeError as e:
                print(f"[DEBUG] خطأ في JSON: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'تم اختبار البيانات بنجاح',
            'customer_id': customer_id,
            'documents_count': len(json.loads(new_documents_data)) if new_documents_data else 0,
            'form_keys': list(request.form.keys()),
            'files_keys': list(request.files.keys())
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in api_test_upload: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في الاختبار: {str(e)}'})

@customer_new_bp.route('/api/document/<int:doc_id>/delete', methods=['POST'])
@login_required
@permission_required('manage_customers')
def api_document_delete(doc_id):
    """API لحذف الوثيقة"""
    try:
        document = CustomerDocument.query.get_or_404(doc_id)
        
        # حذف ناعم
        document.soft_delete()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف الوثيقة بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in api_document_delete: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في الحذف: {str(e)}'})

@customer_new_bp.route('/document/<int:doc_id>/download')
@login_required
@permission_required('manage_customers')
def download_document(doc_id):
    """تحميل الوثيقة"""
    try:
        document = CustomerDocument.query.get_or_404(doc_id)
        if document.status != 'active':
            return ("<h3 style='color:red;text-align:center'>الوثيقة غير متاحة</h3>", 404)
        file_path = os.path.join(UPLOAD_FOLDER, document.filename)
        if not os.path.exists(file_path):
            return ("<h3 style='color:red;text-align:center'>الملف غير موجود</h3>", 404)
        return send_from_directory(
            UPLOAD_FOLDER,
            document.filename,
            as_attachment=True,
            download_name=document.original_name
        )
    except Exception as e:
        current_app.logger.error(f'Error downloading document: {str(e)}')
        return (f"<h3 style='color:red;text-align:center'>حدث خطأ في تحميل الوثيقة: {str(e)}</h3>", 500)

@customer_new_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@permission_required('manage_customers')
def delete(id):
    """حذف عميل"""
    try:
        customer = Customer.query.get_or_404(id)
        
        # التحقق من عدم وجود حجوزات
        if customer.bookings.count() > 0:
            flash('لا يمكن حذف العميل لوجود حجوزات مرتبطة به', 'error')
            return redirect(url_for('customer_new.index'))
        
        # حذف الوثائق المرتبطة
        for document in customer.documents:
            document.soft_delete()
        
        # حذف العميل
        db.session.delete(customer)
        db.session.commit()
        
        flash(f'تم حذف العميل {customer.full_name} بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting customer: {str(e)}')
        flash('حدث خطأ في حذف العميل', 'error')
    
    return redirect(url_for('customer_new.index'))
