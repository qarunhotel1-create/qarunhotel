from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from hotel import db
from hotel.models import User, Note, NOTE_STATUS_PENDING

notes_bp = Blueprint('notes', __name__, url_prefix='/notes')


@notes_bp.route('/', methods=['GET'])
@login_required
def index():
    # Notes sent to me and notes I sent
    received_notes = Note.query.filter_by(receiver_id=current_user.id).order_by(Note.created_at.desc()).all()
    sent_notes = Note.query.filter_by(sender_id=current_user.id).order_by(Note.created_at.desc()).all()
    users = User.query.order_by(User.full_name.asc()).all()
    return render_template('notes/index.html', received_notes=received_notes, sent_notes=sent_notes, users=users)


@notes_bp.route('/create', methods=['POST'])
@login_required
def create():
    """إنشاء ملاحظة وإرسالها لمستخدم واحد أو لجميع المستخدمين."""
    receiver_mode = request.form.get('send_to', 'one')  # values: 'all' or 'one'
    receiver_id = request.form.get('receiver_id')
    content = request.form.get('content', '').strip()

    if not content:
        flash('يرجى كتابة الملاحظة', 'danger')
        return redirect(url_for('notes.index'))

    try:
        if receiver_mode == 'all':
            # إرسال إلى جميع المستخدمين ما عدا المرسل
            targets = db.session.query(User.id).filter(User.id != current_user.id).all()
            if not targets:
                flash('لا يوجد مستخدمون لإرسال الملاحظة لهم', 'warning')
                return redirect(url_for('notes.index'))
            for (uid,) in targets:
                note = Note(sender_id=current_user.id, receiver_id=int(uid), content=content, status=NOTE_STATUS_PENDING)
                db.session.add(note)
            db.session.commit()
            flash('تم إرسال الملاحظة إلى جميع المستخدمين', 'success')
        else:
            # إرسال لمستخدم واحد محدد
            if not receiver_id:
                flash('يرجى تحديد المستخدم المستلم', 'danger')
                return redirect(url_for('notes.index'))
            note = Note(sender_id=current_user.id, receiver_id=int(receiver_id), content=content, status=NOTE_STATUS_PENDING)
            db.session.add(note)
            db.session.commit()
            flash('تم إرسال الملاحظة بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الإرسال: {e}', 'danger')

    return redirect(url_for('notes.index'))


@notes_bp.route('/<int:note_id>/complete', methods=['POST'])
@login_required
def complete(note_id):
    note = Note.query.get_or_404(note_id)
    if note.receiver_id != current_user.id and not current_user.is_admin():
        flash('لا تملك صلاحية تغيير حالة هذه الملاحظة', 'danger')
        return redirect(url_for('notes.index'))

    try:
        note.mark_completed()
        db.session.commit()
        flash('تم تعليم الملاحظة كمكتملة', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء التحديث: {e}', 'danger')

    return redirect(url_for('notes.index'))