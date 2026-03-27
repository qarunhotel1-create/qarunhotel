from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app, send_from_directory
from flask_login import login_required, current_user
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

from hotel import db
from hotel.models import Customer, Booking
from hotel.models.payment import Payment
from sqlalchemy import func, or_
from hotel.forms.customer import CustomerForm
from hotel.utils.decorators import permission_required

customer_bp = Blueprint('customer', __name__, url_prefix='/customers')

# إعدادات رفع الملفات الجديدة
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf', 'doc', 'docx', 'txt'}
UPLOAD_FOLDER = os.path.join('hotel', 'static', 'uploads', 'customers')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """التحقق من صحة امتداد الملف"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """الحصول على حجم الملف"""
    file.seek(0, 2)  # الانتقال لنهاية الملف
    size = file.tell()
    file.seek(0)  # العودة للبداية
    return size

def create_upload_folder():
    """إنشاء مجلد الرفع إذا لم يكن موجوداً"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_document_type_from_mime(mime_type):
    """تحديد نوع الوثيقة من MIME type"""
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type == 'application/pdf':
        return 'pdf'
    elif 'word' in mime_type or 'document' in mime_type:
        return 'document'
    else:
        return 'other'
@customer_bp.route('/block/<int:customer_id>', methods=['POST'])
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
        
        # حظر العميل
        success = customer.block_customer(reason, 'Admin')
        
        if success:
            return jsonify({'success': True, 'message': 'تم حظر العميل بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في حظر العميل'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@customer_bp.route('/unblock/<int:customer_id>', methods=['POST'])
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

@customer_bp.route('/')
@login_required
@permission_required('manage_customers')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    q = (request.args.get('q') or '').strip()

    query = Customer.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Customer.name.ilike(like),
                Customer.id_number.ilike(like),
                Customer.phone.ilike(like)
            )
        )

    customers_pagination = query.order_by(Customer.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('customer/index.html', title='قائمة العملاء', customers=customers_pagination, q=q)

@customer_bp.route('/<int:id>')
@login_required
@permission_required('manage_customers')
def details(id):
    customer = Customer.query.get_or_404(id)

    # احصائيات الحجوزات لهذا العميل
    bookings_count = Booking.query.filter_by(customer_id=id).count()
    total_bookings_amount = db.session.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(Booking.customer_id == id).scalar() or 0
    total_paid_amount = db.session.query(func.coalesce(func.sum(Booking.paid_amount), 0)).filter(Booking.customer_id == id).scalar() or 0

    # جلب كل الدفعات الخاصة بحجوزات العميل (للعرض في صفحة العميل)
    payments = (
        Payment.query
        .join(Booking, Payment.booking_id == Booking.id)
        .filter(Booking.customer_id == id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    return render_template(
        'customer/details.html',
        title=f'تفاصيل العميل - {customer.name}',
        customer=customer,
        bookings_count=bookings_count,
        total_bookings_amount=total_bookings_amount,
        total_paid_amount=total_paid_amount,
        payments=payments,
    )




@customer_bp.route('/add', methods=['POST'])
@login_required
@permission_required('manage_customers')
def add_customer_ajax():
    try:
        data = request.get_json()
        if not data.get('name'):
            return jsonify({'success': False, 'message': 'الاسم مطلوب'})

        # التحقق من عدم وجود عميل بنفس رقم الهوية
        if data.get('id_number') and data.get('id_number').strip():
            id_number = data.get('id_number').strip()
            existing = Customer.query.filter_by(id_number=id_number).first()
            if existing:
                return jsonify({'success': False, 'message': 'يوجد عميل بنفس رقم الهوية'})

        # تعديل: حفظ id_number كـ None إذا كان فارغاً
        id_number = data.get('id_number', '').strip() if data.get('id_number') else None
        customer = Customer(
            name=data['name'],
            id_number=id_number,
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            nationality='مصري',
            marital_status='أعزب',
            created_by=current_user.full_name
        )
        db.session.add(customer)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم إضافة العميل بنجاح',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'id_number': customer.id_number,
                'phone': customer.phone
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'خطأ في الإضافة: {str(e)}'})



@customer_bp.route('/upload-multiple-documents', methods=['POST'])
@login_required
@permission_required('manage_customers')
def upload_multiple_documents():
    """رفع عدة وثائق للعميل"""
    try:
        # التحقق من وجود ملفات
        if 'documents' not in request.files:
            return jsonify({'success': False, 'message': 'لم يتم اختيار أي ملفات'})
        
        files = request.files.getlist('documents')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'success': False, 'message': 'لم يتم اختيار ملفات صالحة'})
        
        # إنشاء مجلد الرفع
        create_upload_folder()
        
        uploaded_files = []
        errors = []
        
        for file in files:
            if file and file.filename:
                # التحقق من نوع الملف
                if not allowed_file(file.filename):
                    errors.append(f'نوع ملف غير مسموح: {file.filename}')
                    continue
                
                # التحقق من حجم الملف
                file_size = get_file_size(file)
                if file_size > MAX_FILE_SIZE:
                    errors.append(f'حجم الملف كبير جداً: {file.filename} ({file_size / (1024*1024):.1f}MB)')
                    continue
                
                try:
                    # إنشاء اسم ملف فريد
                    original_filename = secure_filename(file.filename)
                    file_extension = original_filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
                    
                    # حفظ الملف
                    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(file_path)
                    
                    # التحقق من حفظ الملف
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        uploaded_files.append({
                            'filename': unique_filename,
                            'original_name': original_filename,
                            'size': file_size,
                            'type': file_extension.upper(),
                            'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                    else:
                        errors.append(f'فشل في حفظ الملف: {file.filename}')
                        
                except Exception as e:
                    current_app.logger.error(f'Error saving file {file.filename}: {str(e)}')
                    errors.append(f'خطأ في حفظ {file.filename}: {str(e)}')
        
        return jsonify({
            'success': len(uploaded_files) > 0,
            'message': f'تم رفع {len(uploaded_files)} ملف بنجاح' if uploaded_files else 'فشل في رفع الملفات',
            'files': uploaded_files,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in upload_multiple_documents: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في النظام: {str(e)}'})

@customer_bp.route('/scanner-capture', methods=['POST'])
@login_required
@permission_required('manage_customers')
def scanner_capture():
    """معالجة الصور الممسوحة من الطابعة"""
    try:
        data = request.get_json()
        if not data or 'images' not in data:
            return jsonify({'success': False, 'message': 'لم يتم استلام صور'})
        
        images = data['images']
        if not images:
            return jsonify({'success': False, 'message': 'لا توجد صور للمعالجة'})
        
        # إنشاء مجلد الرفع
        create_upload_folder()
        
        scanned_files = []
        
        for i, image_data in enumerate(images):
            try:
                # إزالة بادئة base64
                if image_data.startswith('data:image/'):
                    image_data = image_data.split(',')[1]
                
                # فك تشفير base64
                import base64
                image_bytes = base64.b64decode(image_data)
                
                # إنشاء اسم ملف فريد
                unique_filename = f"{uuid.uuid4().hex}_scan_{i+1}.jpg"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                
                # حفظ الصورة
                with open(file_path, 'wb') as f:
                    f.write(image_bytes)
                
                # التحقق من الحفظ
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    scanned_files.append({
                        'filename': unique_filename,
                        'original_name': f'مسح ضوئي {i+1}.jpg',
                        'size': len(image_bytes),
                        'type': 'JPG',
                        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
            except Exception as e:
                current_app.logger.error(f'Error processing scanned image {i+1}: {str(e)}')
                continue
        
        return jsonify({
            'success': len(scanned_files) > 0,
            'message': f'تم مسح {len(scanned_files)} صورة بنجاح' if scanned_files else 'فشل في المسح',
            'files': scanned_files
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in scanner_capture: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في المسح: {str(e)}'})

@customer_bp.route('/delete-temp-file', methods=['POST'])
@login_required
@permission_required('manage_customers')
def delete_temp_file():
    """حذف ملف مؤقت قبل الحفظ النهائي"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'message': 'اسم الملف مطلوب'})
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'message': 'تم حذف الملف'})
        else:
            return jsonify({'success': False, 'message': 'الملف غير موجود'})
            
    except Exception as e:
        current_app.logger.error(f'Error deleting temp file: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في الحذف: {str(e)}'})



@customer_bp.route('/download-document/<filename>')
@login_required
@permission_required('manage_customers')
def download_document_file(filename):
    """تحميل ملف وثيقة"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            flash('الملف غير موجود', 'error')
            return redirect(url_for('customer.index'))
        
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
        
    except Exception as e:
        current_app.logger.error(f'Error downloading document: {str(e)}')
        flash('حدث خطأ في تحميل الوثيقة', 'error')
        return redirect(url_for('customer.index'))

@customer_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('manage_customers')
def create():
    form = CustomerForm()
    if form.validate_on_submit():
        try:
            # إنشاء العميل
            # تعديل: حفظ id_number كـ None إذا كان فارغاً
            id_number = form.id_number.data.strip() if form.id_number.data else None
            # تحديد الجنسية المحفوظة: إذا اختار المستخدم "جنسية أخرى" نحفظ النص المدخل
            selected_nationality = (form.nationality_other.data.strip() if form.nationality.data == 'جنسية أخرى' and form.nationality_other.data else form.nationality.data)

            customer = Customer(
                name=form.name.data,
                id_number=id_number,
                phone=form.phone.data,
                nationality=selected_nationality,
                marital_status=form.marital_status.data,
                address=form.address.data,
                created_by=current_user.full_name
            )
            db.session.add(customer)
            db.session.flush()  # للحصول على ID العميل
            
            # معالجة الوثائق من النظام الجديد
            documents_saved = 0
            documents_data = request.form.get('documents_data')
            
            if documents_data:
                try:
                    import json
                    import base64
                    documents_list = json.loads(documents_data)
                    
                    if documents_list and isinstance(documents_list, list):
                        create_upload_folder()  # التأكد من وجود مجلد الرفع
                        
                        for doc_data in documents_list:
                            try:
                                # استخراج بيانات الملف
                                file_name = doc_data.get('name', '')
                                file_data = doc_data.get('data', '')
                                file_type = doc_data.get('type', '')
                                file_size = doc_data.get('size', 0)
                                
                                if not file_name or not file_data:
                                    continue
                                
                                # فصل header عن البيانات الفعلية
                                if ',' in file_data:
                                    header, file_content = file_data.split(',', 1)
                                else:
                                    file_content = file_data
                                
                                # فك تشفير base64
                                try:
                                    file_bytes = base64.b64decode(file_content)
                                except Exception as decode_error:
                                    current_app.logger.error(f'Base64 decode error for {file_name}: {str(decode_error)}')
                                    continue
                                
                                # إنشاء اسم ملف فريد
                                file_extension = file_name.split('.')[-1] if '.' in file_name else 'bin'
                                unique_filename = f"{customer.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
                                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                                
                                # حفظ الملف
                                with open(file_path, 'wb') as f:
                                    f.write(file_bytes)
                                
                                # التحقق من حفظ الملف
                                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                    # تحديث بيانات العميل (للوثيقة الأولى)
                                    if documents_saved == 0:
                                        customer.document_filename = unique_filename
                                        customer.document_type = get_document_type_from_mime(file_type)
                                        customer.document_upload_date = datetime.now()
                                    
                                    documents_saved += 1
                                    current_app.logger.info(f'Document saved: {unique_filename} for customer {customer.id}')
                                else:
                                    current_app.logger.error(f'Failed to save file: {unique_filename}')
                                    
                            except Exception as doc_error:
                                current_app.logger.error(f'Error processing document {doc_data.get("name", "unknown")}: {str(doc_error)}')
                                continue
                        
                except json.JSONDecodeError as json_error:
                    current_app.logger.warning(f'Invalid JSON in documents_data: {str(json_error)}')
                except Exception as e:
                    current_app.logger.error(f'Error processing documents: {str(e)}')
            
            db.session.commit()
            
            if documents_saved > 0:
                flash(f'تم إضافة العميل بنجاح مع {documents_saved} وثيقة', 'success')
            else:
                flash('تم إضافة العميل بنجاح', 'success')
            
            return redirect(url_for('customer.details', id=customer.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating customer: {str(e)}', exc_info=True)
            flash(f'خطأ في إضافة العميل: {str(e)}', 'error')
            
    return render_template('customer/create.html', title='إضافة عميل جديد', form=form)

@customer_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('manage_customers')
def edit(id):
    """تعديل بيانات العميل مع نظام وثائق مبسط"""
    customer = Customer.query.get_or_404(id)
    # This is the crucial change:
    # On POST, pass request.form to the constructor.
    # On GET, do not pass it, so obj=customer can work.
    form = CustomerForm(request.form if request.method == 'POST' else None, obj=customer)

    # Special handling for GET request to populate the 'other' nationality field
    if request.method == 'GET' and customer.nationality not in [choice[0] for choice in form.nationality.choices]:
        form.nationality.data = 'جنسية أخرى'
        form.nationality_other.data = customer.nationality

    if form.validate_on_submit():
        try:
            # The form data is now correctly populated from the POST request.
            # We can now safely update the customer object.
            customer.name = form.name.data.strip()
            customer.id_number = form.id_number.data.strip()
            customer.phone = form.phone.data.strip() if form.phone.data else None
            
            # Handle nationality correctly
            if form.nationality.data == 'جنسية أخرى':
                if form.nationality_other.data and form.nationality_other.data.strip():
                    customer.nationality = form.nationality_other.data.strip()
                else:
                    # If 'other' is selected but the text field is empty, do not default to 'مصري'.
                    # Instead, we can save 'جنسية أخرى' literally, or an empty string.
                    # Let's save it as an empty string to indicate no specific nationality was entered.
                    customer.nationality = ''
            else:
                customer.nationality = form.nationality.data

            customer.marital_status = form.marital_status.data if form.marital_status.data else None
            customer.address = form.address.data.strip() if form.address.data else None
            customer.updated_by = current_user.full_name
            customer.updated_at = datetime.now()
            
            # --- Document upload logic (remains unchanged) ---
            documents_saved = 0
            uploaded_files = request.files.getlist('document_files')
            if uploaded_files and any(f.filename for f in uploaded_files):
                create_upload_folder()
                for file in uploaded_files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            file_extension = file.filename.rsplit('.', 1)[1].lower()
                            unique_filename = f"{customer.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
                            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                            file.save(file_path)
                            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                if documents_saved == 0:
                                    if customer.document_filename:
                                        old_file_path = os.path.join(UPLOAD_FOLDER, customer.document_filename)
                                        if os.path.exists(old_file_path):
                                            try:
                                                os.remove(old_file_path)
                                            except: pass
                                    customer.document_filename = unique_filename
                                    # A helper function get_document_type_from_filename was missing, using a simple fallback
                                    customer.document_type = file.filename.rsplit('.', 1)[1].lower()
                                    customer.document_upload_date = datetime.now()
                                if hasattr(customer, 'documents'):
                                    from hotel.models.customer import CustomerDocument
                                    new_document = CustomerDocument(
                                        customer_id=customer.id,
                                        filename=unique_filename,
                                        original_filename=file.filename,
                                        document_type=file.filename.rsplit('.', 1)[1].lower(),
                                        file_size=os.path.getsize(file_path),
                                        upload_date=datetime.now(),
                                        is_primary=(documents_saved == 0)
                                    )
                                    db.session.add(new_document)
                                documents_saved += 1
                        except Exception as file_error:
                            current_app.logger.error(f'Error saving file {file.filename}: {str(file_error)}')
                            continue
            
            db.session.commit()
            
            if documents_saved > 0:
                flash(f'تم تحديث بيانات العميل بنجاح مع {documents_saved} وثيقة جديدة', 'success')
            else:
                flash('تم تحديث بيانات العميل بنجاح', 'success')
            
            return redirect(url_for('customer.details', id=customer.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating customer {id}: {str(e)}')
            flash(f'حدث خطأ في تحديث البيانات: {str(e)}', 'error')
    
    # Render the page for GET requests or if validation fails
    return render_template('customer/edit.html', 
                         title=f'تعديل العميل - {customer.name}', 
                         form=form, 
                         customer=customer,
                         documents=customer.active_documents)

@customer_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('manage_customers')
def delete(id):
    try:
        customer = Customer.query.get_or_404(id)
        customer_name = customer.name

        # التحقق من وجود حجوزات مرتبطة
        if customer.bookings.count() > 0:
            flash('لا يمكن حذف العميل لأنه مرتبط بحجوزات', 'error')
            return redirect(url_for('customer.index'))

        db.session.delete(customer)
        db.session.commit()

        flash(f'تم حذف العميل "{customer_name}" بنجاح', 'success')
        return redirect(url_for('customer.index'))

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف العميل: {str(e)}', 'error')
        return redirect(url_for('customer.index'))


        
    except Exception as e:
        current_app.logger.error(f'Error viewing document: {str(e)}')
        flash('حدث خطأ في عرض الوثيقة', 'error')
        return redirect(url_for('customer.details', id=customer_id))


