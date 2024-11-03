from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import Curriculum, db, Student, Quiz, QuizAssignment
from ai_service import generate_curriculum_content, AIServiceError

curriculum_bp = Blueprint('curriculum', __name__)

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_teacher:
            flash('Erişim reddedildi. Bu işlemi sadece öğretmenler yapabilir.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@curriculum_bp.route('/curriculum/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        topic = request.form.get('topic', '').strip()
        level = request.form.get('level', '').strip()
        
        # Form validation
        if not title or not topic or not level:
            flash('Tüm alanların doldurulması zorunludur.', 'error')
            return render_template('curriculum/create.html', 
                                form_data={'title': title, 'topic': topic, 'level': level})
        
        try:
            # Generate content using Gemini AI
            content = generate_curriculum_content(topic, level)
            
            curriculum = Curriculum(
                title=title,
                content=content,
                author_id=current_user.id
            )
            
            db.session.add(curriculum)
            db.session.commit()
            
            flash('Müfredat başarıyla oluşturuldu!', 'success')
            return redirect(url_for('curriculum.view', id=curriculum.id))
            
        except AIServiceError as e:
            flash(str(e), 'error')
            return render_template('curriculum/create.html', 
                                form_data={'title': title, 'topic': topic, 'level': level})
        except Exception as e:
            flash('Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.', 'error')
            return render_template('curriculum/create.html', 
                                form_data={'title': title, 'topic': topic, 'level': level})
    
    return render_template('curriculum/create.html', form_data={})

@curriculum_bp.route('/curriculum')
@login_required
def list():
    curricula = Curriculum.query.all()
    return render_template('curriculum/list.html', curricula=curricula)

@curriculum_bp.route('/curriculum/<int:id>')
@login_required
def view(id):
    curriculum = Curriculum.query.get_or_404(id)
    assigned_quizzes = curriculum.quizzes
    
    if not current_user.is_teacher:
        student = Student.query.filter_by(email=current_user.email).first()
        if student:
            assigned_quizzes = Quiz.query.join(QuizAssignment).filter(
                Quiz.curriculum_id == curriculum.id,
                QuizAssignment.student_id == student.id,
                QuizAssignment.completed == False
            ).all()
            
    return render_template('curriculum/view.html', curriculum=curriculum, assigned_quizzes=assigned_quizzes)

@curriculum_bp.route('/curriculum/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit(id):
    curriculum = Curriculum.query.get_or_404(id)
    
    if curriculum.author_id != current_user.id:
        flash('Sadece kendi müfredatınızı düzenleyebilirsiniz', 'error')
        return redirect(url_for('curriculum.list'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            flash('Tüm alanların doldurulması zorunludur.', 'error')
            return render_template('curriculum/edit.html', curriculum=curriculum)
            
        try:
            curriculum.title = title
            curriculum.content = content
            db.session.commit()
            flash('Müfredat başarıyla güncellendi!', 'success')
            return redirect(url_for('curriculum.view', id=curriculum.id))
        except Exception as e:
            flash('Müfredat güncellenirken bir hata oluştu.', 'error')
            return render_template('curriculum/edit.html', curriculum=curriculum)
    
    return render_template('curriculum/edit.html', curriculum=curriculum)
