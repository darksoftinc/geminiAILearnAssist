from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Student, QuizAttempt
from functools import wraps

student_bp = Blueprint('student', __name__)

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_teacher:
            flash('Bu işlemi sadece öğretmenler yapabilir.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/student/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        grade = request.form.get('grade')
        
        if not all([name, email, grade]):
            flash('Lütfen tüm alanları doldurun.', 'error')
            return render_template('student/create.html')
            
        if Student.query.filter_by(email=email).first():
            flash('Bu e-posta adresi zaten kayıtlı.', 'error')
            return render_template('student/create.html')
            
        student = Student(
            name=name,
            email=email,
            grade=grade,
            teacher_id=current_user.id
        )
        
        try:
            db.session.add(student)
            db.session.commit()
            flash('Öğrenci başarıyla eklendi.', 'success')
            return redirect(url_for('student.list'))
        except Exception as e:
            db.session.rollback()
            flash('Öğrenci eklenirken bir hata oluştu.', 'error')
            
    return render_template('student/create.html')

@student_bp.route('/student/list')
@login_required
def list():
    if current_user.is_teacher:
        students = Student.query.filter_by(teacher_id=current_user.id).all()
    else:
        students = []  # Regular users don't see the list
    return render_template('student/list.html', students=students)

@student_bp.route('/student/<int:id>')
@login_required
def view(id):
    student = Student.query.get_or_404(id)
    if not current_user.is_teacher or student.teacher_id != current_user.id:
        flash('Bu öğrencinin bilgilerini görüntüleme yetkiniz yok.', 'error')
        return redirect(url_for('dashboard.index'))
        
    # Get student's quiz attempts and performance data
    quiz_attempts = QuizAttempt.query.filter_by(student_id=student.id).order_by(QuizAttempt.completed_at.desc()).all()
    
    # Calculate performance metrics
    total_attempts = len(quiz_attempts)
    if total_attempts > 0:
        average_score = sum(attempt.score for attempt in quiz_attempts) / total_attempts
        highest_score = max(attempt.score for attempt in quiz_attempts)
        lowest_score = min(attempt.score for attempt in quiz_attempts)
    else:
        average_score = highest_score = lowest_score = 0
        
    performance_data = {
        'total_attempts': total_attempts,
        'average_score': average_score,
        'highest_score': highest_score,
        'lowest_score': lowest_score
    }
    
    return render_template('student/view.html', 
                         student=student, 
                         quiz_attempts=quiz_attempts,
                         performance_data=performance_data)
