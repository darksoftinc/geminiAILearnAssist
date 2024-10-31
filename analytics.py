from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import User, QuizAttempt, Quiz, Curriculum, Student
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import pandas as pd

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def index():
    selected_student_id = request.args.get('student_id', type=int)
    
    # Get user's quiz attempts
    if current_user.is_teacher:
        if selected_student_id:
            student = Student.query.get_or_404(selected_student_id)
            if student.teacher_id != current_user.id:
                flash('Bu öğrencinin verilerine erişim yetkiniz yok.', 'error')
                return redirect(url_for('dashboard.index'))
            attempts = QuizAttempt.query.filter_by(student_id=selected_student_id).all()
        else:
            # Get all students' attempts for this teacher
            attempts = QuizAttempt.query.join(Student).filter(
                Student.teacher_id == current_user.id
            ).all()
    else:
        attempts = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    
    # Calculate overall statistics
    total_quizzes = len(attempts)
    if total_quizzes > 0:
        average_score = sum(attempt.score for attempt in attempts) / total_quizzes
        highest_score = max((attempt.score for attempt in attempts), default=0)
        recent_trend = [
            {
                'date': attempt.completed_at.strftime('%Y-%m-%d'),
                'score': attempt.score,
                'quiz': attempt.quiz.title,
                'student': attempt.student_profile.name if attempt.student_profile else attempt.student.username
            }
            for attempt in sorted(attempts, key=lambda x: x.completed_at, reverse=True)[:5]
        ]
    else:
        average_score = 0
        highest_score = 0
        recent_trend = []

    # Get curriculum-wise performance
    curriculum_performance = {}
    for attempt in attempts:
        curriculum = attempt.quiz.curriculum
        if curriculum.title not in curriculum_performance:
            curriculum_performance[curriculum.title] = {
                'attempts': 0,
                'total_score': 0,
                'average': 0
            }
        curriculum_performance[curriculum.title]['attempts'] += 1
        curriculum_performance[curriculum.title]['total_score'] += attempt.score
    
    for curriculum in curriculum_performance.values():
        curriculum['average'] = curriculum['total_score'] / curriculum['attempts']

    # Get student list for teachers
    students = []
    student_performance = {}
    if current_user.is_teacher:
        students = Student.query.filter_by(teacher_id=current_user.id).all()
        
        # Calculate performance for each student
        for student in students:
            student_attempts = QuizAttempt.query.filter_by(student_id=student.id).all()
            if student_attempts:
                avg_score = sum(a.score for a in student_attempts) / len(student_attempts)
                recent_score = max(student_attempts, key=lambda x: x.completed_at).score
                improvement = recent_score - min(a.score for a in student_attempts)
            else:
                avg_score = 0
                recent_score = 0
                improvement = 0
                
            student_performance[student.id] = {
                'name': student.name,
                'average_score': avg_score,
                'recent_score': recent_score,
                'total_attempts': len(student_attempts),
                'improvement': improvement
            }

    # Get class performance data (for teachers)
    class_performance = None
    if current_user.is_teacher:
        class_performance = {
            'total_students': len(students),
            'total_attempts': QuizAttempt.query.join(Student).filter(
                Student.teacher_id == current_user.id
            ).count(),
            'class_average': QuizAttempt.query.join(Student).filter(
                Student.teacher_id == current_user.id
            ).with_entities(
                func.avg(QuizAttempt.score).label('average')
            ).scalar() or 0,
            'recent_completion_rate': len([
                a for a in attempts 
                if a.completed_at >= datetime.utcnow() - timedelta(days=7)
            ]) / max(len(attempts), 1) * 100 if attempts else 0
        }

    return render_template(
        'analytics/index.html',
        total_quizzes=total_quizzes,
        average_score=average_score,
        highest_score=highest_score,
        recent_trend=recent_trend,
        curriculum_performance=curriculum_performance,
        students=students,
        student_performance=student_performance,
        selected_student_id=selected_student_id,
        class_performance=class_performance
    )

@analytics_bp.route('/analytics/student/<int:student_id>/performance')
@login_required
def student_performance(student_id):
    if not current_user.is_teacher:
        return jsonify({'error': 'Yetkisiz erişim'}), 403
        
    student = Student.query.get_or_404(student_id)
    if student.teacher_id != current_user.id:
        return jsonify({'error': 'Bu öğrencinin verilerine erişim yetkiniz yok'}), 403
        
    attempts = QuizAttempt.query.filter_by(student_id=student_id).order_by(
        QuizAttempt.completed_at
    ).all()
    
    performance_data = {
        'dates': [a.completed_at.strftime('%Y-%m-%d') for a in attempts],
        'scores': [a.score for a in attempts],
        'quizzes': [a.quiz.title for a in attempts]
    }
    
    return jsonify(performance_data)
