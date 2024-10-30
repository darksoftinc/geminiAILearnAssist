from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Curriculum, db
from ai_service import generate_curriculum_content

curriculum_bp = Blueprint('curriculum', __name__)

@curriculum_bp.route('/curriculum/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_teacher:
        flash('Only teachers can create curricula')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        topic = request.form.get('topic')
        level = request.form.get('level')
        
        # Generate content using Gemini AI
        content = generate_curriculum_content(topic, level)
        
        curriculum = Curriculum(
            title=title,
            content=content,
            author_id=current_user.id
        )
        
        db.session.add(curriculum)
        db.session.commit()
        
        return redirect(url_for('curriculum.list'))
    
    return render_template('curriculum/create.html')

@curriculum_bp.route('/curriculum')
@login_required
def list():
    curricula = Curriculum.query.all()
    return render_template('curriculum/list.html', curricula=curricula)

@curriculum_bp.route('/curriculum/<int:id>')
@login_required
def view(id):
    curriculum = Curriculum.query.get_or_404(id)
    return render_template('curriculum/view.html', curriculum=curriculum)

@curriculum_bp.route('/curriculum/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    curriculum = Curriculum.query.get_or_404(id)
    
    if curriculum.author_id != current_user.id:
        flash('You can only edit your own curricula')
        return redirect(url_for('curriculum.list'))
    
    if request.method == 'POST':
        curriculum.title = request.form.get('title')
        curriculum.content = request.form.get('content')
        db.session.commit()
        return redirect(url_for('curriculum.list'))
    
    return render_template('curriculum/edit.html', curriculum=curriculum)
