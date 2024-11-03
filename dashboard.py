from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Curriculum, Student, QuizAttempt, QuizAssignment, Quiz
from sqlalchemy import desc, and_

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    curricula = Curriculum.query.all()
    
    # Get quiz scores for the progress chart with proper filtering
    if current_user.is_teacher:
        attempts = QuizAttempt.query\
            .join(Student)\
            .filter(Student.teacher_id == current_user.id)\
            .order_by(QuizAttempt.completed_at)\
            .all()
    else:
        attempts = QuizAttempt.query\
            .filter_by(user_id=current_user.id)\
            .order_by(QuizAttempt.completed_at)\
            .all()
    
    dates = [attempt.completed_at.strftime('%Y-%m-%d') for attempt in attempts]
    scores = [attempt.score for attempt in attempts]
    
    # Additional data for teachers
    recent_student_attempts = []
    total_students = 0
    active_quizzes = 0
    completed_quizzes = 0
    
    if current_user.is_teacher:
        # Get recent student attempts with proper joins
        recent_student_attempts = QuizAttempt.query\
            .join(Student)\
            .filter(Student.teacher_id == current_user.id)\
            .join(Quiz)\
            .order_by(desc(QuizAttempt.completed_at))\
            .limit(10)\
            .all()
        
        # Calculate statistics
        total_students = Student.query.filter_by(teacher_id=current_user.id).count()
        
        # Count active and completed quizzes with proper joins
        quiz_assignments = QuizAssignment.query\
            .join(Student)\
            .filter(Student.teacher_id == current_user.id)\
            .all()
            
        active_quizzes = len([a for a in quiz_assignments if not a.completed])
        completed_quizzes = len([a for a in quiz_assignments if a.completed])
    
    return render_template('dashboard/index.html',
                         curricula=curricula,
                         dates=dates,
                         scores=scores,
                         recent_student_attempts=recent_student_attempts,
                         total_students=total_students,
                         active_quizzes=active_quizzes,
                         completed_quizzes=completed_quizzes)
