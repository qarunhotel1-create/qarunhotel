from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
import uuid

from hotel import db
from hotel.models import Payment, Booking
from hotel.forms.payment import PaymentForm
from hotel.utils.decorators import permission_required

payment_bp = Blueprint('payment', __name__, url_prefix='/payments')

@payment_bp.route('/replace-attachment/<int:payment_id>', methods=['GET', 'POST'])
@login_required
def replace_attachment(payment_id):
    """رفع/استبدال مرفق دفعة مفقود أو خاطئ"""
    from flask import render_template
    payment = Payment.query.get_or_404(payment_id)

    if request.method == 'POST':
        file = request.files.get('attachment')
        if not file or not file.filename:
            flash('يرجى اختيار ملف مرفق', 'warning')
            return redirect(url_for('payment.replace_attachment', payment_id=payment_id))
        try:
            # حفظ في مجلد ثابت داخل التطبيق
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'payments')
            os.makedirs(upload_folder, exist_ok=True)
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
            import uuid
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)

            # تحديث اسم الملف في الدفعة
            old = payment.attachment_file
            payment.attachment_file = unique_filename
            db.session.commit()

            flash('تم حفظ المرفق وتحديث الدفعة بنجاح', 'success')
            # العودة إلى تفاصيل الحجز أو العميل إن وجد مرجع
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('booking.details', id=payment.booking_id))
        except Exception as e:
            current_app.logger.error(f'Error replacing attachment for payment {payment_id}: {str(e)}', exc_info=True)
            db.session.rollback()
            flash(f'حدث خطأ أثناء حفظ المرفق: {str(e)}', 'danger')
            return redirect(url_for('payment.replace_attachment', payment_id=payment_id))

    return render_template('payment/replace_attachment.html', payment=payment, title='استبدال/رفع مرفق الدفعة')

@payment_bp.route('/add/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def add_payment(booking_id):
    # التحقق من الصلاحية
    if not current_user.can_add_payment():
        flash('ليس لديك صلاحية لإضافة دفعة', 'danger')
        return redirect(url_for('booking.details', id=booking_id))
    booking = Booking.query.get_or_404(booking_id)
    form = PaymentForm(booking=booking)
    form.booking_id.data = booking_id
    
    if form.validate_on_submit():
        attachment_filename = None

        # التعامل مع رفع الملف للتحويل البنكي
        if form.payment_type.data == 'bank_transfer' and form.attachment.data:
            file = form.attachment.data
            if file and file.filename:
                # إنشاء اسم ملف فريد
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

                # مسار حفظ الملف
                upload_folder = os.path.join('hotel', 'static', 'uploads', 'payments')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)

                # حفظ الملف
                file.save(file_path)
                attachment_filename = unique_filename

        # إنشاء دفعة جديدة
        payment = Payment(
            booking_id=booking_id,
            amount=form.amount.data,
            payment_type=form.payment_type.data,
            notes=form.notes.data,
            attachment_file=attachment_filename,
            user_id=current_user.id
        )
        
        db.session.add(payment)
        db.session.flush()  # للحصول على ID الدفعة

        # تحديث المبلغ المدفوع في الحجز
        booking.update_paid_amount()

        db.session.commit()
        
        flash(f'تم تسجيل دفعة بمبلغ {form.amount.data} جنيه بنجاح', 'success')
        return redirect(url_for('booking.details', id=booking_id))
    
    return render_template('payment/add.html', 
                         title='إضافة دفعة', 
                         form=form, 
                         booking=booking)

@payment_bp.route('/delete/<int:payment_id>', methods=['POST'])
@login_required
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    booking = payment.booking

    # التحقق من الصلاحية
    if not current_user.can_delete_payment():
        flash('ليس لديك صلاحية لحذف الدفعة', 'danger')
        return redirect(url_for('booking.details', id=booking.id))
    
    db.session.delete(payment)
    
    # تحديث المبلغ المدفوع في الحجز
    booking.update_paid_amount()
    
    db.session.commit()
    
    flash('تم حذف الدفعة بنجاح', 'success')
    return redirect(url_for('booking.details', id=booking.id))

@payment_bp.route('/attachment/<path:filename>')
@login_required
def view_attachment(filename):
    """عرض الملف المرفق للدفعة"""
    import mimetypes
    from flask import current_app, abort, Response, url_for
    import os.path

    # تأمين الاسم ومنع تمرير مسارات داخلية وإزالة المسافات
    safe_name = os.path.basename(filename).strip()

    # استخدام المسار المطلق للملفات المرفقة
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'payments')
    file_path = os.path.join(upload_folder, safe_name)
    
    current_app.logger.info(f'طلب عرض ملف مرفق: {safe_name}')
    current_app.logger.info(f'المسار الكامل للملف: {file_path}')

    # التحقق من وجود الملف
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        current_app.logger.error(f'الملف غير موجود: {file_path}')
        return abort(404, f'الملف غير موجود: {safe_name}')

    # تحديد نوع الملف
    mimetype, _ = mimetypes.guess_type(file_path)
    if not mimetype:
        if safe_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
            mimetype = 'image/jpeg'
        elif safe_name.lower().endswith('.pdf'):
            mimetype = 'application/pdf'
        else:
            mimetype = 'application/octet-stream'
    
    current_app.logger.info(f'عرض ملف مرفق: {safe_name}, نوع الملف: {mimetype}')
    
    is_print = request.args.get('print') == '1'
    is_download = request.args.get('download') == '1'
    
    headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }

    # PDF
    if safe_name.lower().endswith('.pdf'):
        resp = send_from_directory(
            upload_folder,
            safe_name,
            mimetype='application/pdf',
            as_attachment=is_download,
            download_name=safe_name if is_download else None
        )
        try:
            if not is_download:
                resp.headers['Content-Disposition'] = f'inline; filename="{safe_name}"'
            resp.headers.update(headers)
        except Exception:
            pass
        return resp

    # Images
    elif any(safe_name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
        if is_print:
            image_url = url_for('payment.view_attachment', filename=safe_name)
            html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>طباعة الصورة</title>
                <style>
                    body {{ margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }}
                    img {{ max-width: 100%; max-height: 100vh; object-fit: contain; }}
                </style>
                <script>
                    window.onload = function() {{ window.print(); }};
                </script>
            </head>
            <body>
                <img src="{image_url}" alt="صورة للطباعة">
            </body>
            </html>
            '''
            return Response(html, mimetype='text/html', headers=headers)
        else:
            resp = send_from_directory(
                upload_folder,
                safe_name,
                mimetype=mimetype,
                as_attachment=is_download,
                download_name=safe_name if is_download else None
            )
            try:
                if not is_download:
                    resp.headers['Content-Disposition'] = f'inline; filename="{safe_name}"'
                resp.headers.update(headers)
            except Exception:
                pass
            return resp

    # Other files
    else:
        resp = send_from_directory(
            upload_folder,
            safe_name,
            mimetype=mimetype,
            as_attachment=True,
            download_name=safe_name
        )
        try:
            resp.headers.update(headers)
        except Exception:
            pass
        return resp
