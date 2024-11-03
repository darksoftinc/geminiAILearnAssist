from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, QuizAttempt, Quiz, Curriculum, Student
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def index():
    selected_student_id = request.args.get('student_id', type=int)
    
    # Get user's quiz attempts with proper joins
    base_query = QuizAttempt.query.join(Quiz).join(Quiz.curriculum)
    
    if current_user.is_teacher:
        if selected_student_id:
            # Get attempts for a specific student
            student = Student.query.get_or_404(selected_student_id)
            if student.teacher_id != current_user.id:
                flash('Bu öğrencinin verilerine erişim yetkiniz yok.', 'error')
                return redirect(url_for('dashboard.index'))
            attempts = base_query.filter(
                QuizAttempt.student_id == selected_student_id,
                QuizAttempt.student_id.isnot(None)
            ).order_by(QuizAttempt.completed_at.desc()).all()
        else:
            # Get all students' attempts for this teacher
            attempts = base_query.join(Student).filter(
                Student.teacher_id == current_user.id,
                QuizAttempt.student_id.isnot(None)
            ).order_by(QuizAttempt.completed_at.desc()).all()
    else:
        # Get attempts for regular user/student
        attempts = base_query.filter_by(user_id=current_user.id).order_by(
            QuizAttempt.completed_at.desc()
        ).all()
    
    # Calculate overall statistics
    total_quizzes = len(attempts)
    if total_quizzes > 0:
        average_score = sum(attempt.score for attempt in attempts) / total_quizzes
        highest_score = max((attempt.score for attempt in attempts), default=0)
        
        # Get recent trend with proper student information
        recent_trend = [
            {
                'date': attempt.completed_at.strftime('%Y-%m-%d'),
                'score': attempt.score,
                'quiz': attempt.quiz.title,
                'student': attempt.student_profile.name if attempt.student_profile else current_user.username,
                'curriculum': attempt.quiz.curriculum.title
            }
            for attempt in sorted(attempts, key=lambda x: x.completed_at, reverse=True)[:5]
        ]
    else:
        average_score = 0
        highest_score = 0
        recent_trend = []

    # Get curriculum-wise performance with proper filtering
    curriculum_performance = {}
    for attempt in attempts:
        curriculum = attempt.quiz.curriculum
        if curriculum.title not in curriculum_performance:
            curriculum_performance[curriculum.title] = {
                'attempts': 0,
                'total_score': 0,
                'average': 0,
                'student_count': set()
            }
        curriculum_performance[curriculum.title]['attempts'] += 1
        curriculum_performance[curriculum.title]['total_score'] += attempt.score
        if attempt.student_id:
            curriculum_performance[curriculum.title]['student_count'].add(attempt.student_id)
    
    # Calculate averages and convert student_count to length
    for curriculum in curriculum_performance.values():
        curriculum['average'] = curriculum['total_score'] / curriculum['attempts']
        curriculum['student_count'] = len(curriculum['student_count'])

    # Get student list and performance data for teachers
    students = []
    student_performance = {}
    if current_user.is_teacher:
        students = Student.query.filter_by(teacher_id=current_user.id).all()
        
        # Calculate detailed performance metrics for each student
        for student in students:
            student_attempts = QuizAttempt.query.filter_by(
                student_id=student.id
            ).order_by(QuizAttempt.completed_at.desc()).all()
            
            if student_attempts:
                avg_score = sum(a.score for a in student_attempts) / len(student_attempts)
                recent_score = student_attempts[0].score if student_attempts else 0
                improvement = recent_score - min(a.score for a in student_attempts) if len(student_attempts) > 1 else 0
                
                # Calculate curriculum-specific performance
                curriculum_scores = {}
                for attempt in student_attempts:
                    curr_title = attempt.quiz.curriculum.title
                    if curr_title not in curriculum_scores:
                        curriculum_scores[curr_title] = {'total': 0, 'count': 0}
                    curriculum_scores[curr_title]['total'] += attempt.score
                    curriculum_scores[curr_title]['count'] += 1
            else:
                avg_score = 0
                recent_score = 0
                improvement = 0
                curriculum_scores = {}
                
            student_performance[student.id] = {
                'name': student.name,
                'average_score': avg_score,
                'recent_score': recent_score,
                'total_attempts': len(student_attempts),
                'improvement': improvement,
                'curriculum_scores': {
                    k: v['total'] / v['count'] 
                    for k, v in curriculum_scores.items()
                } if curriculum_scores else {}
            }

    # Calculate class performance metrics
    class_performance = None
    if current_user.is_teacher:
        # Get overall class statistics with proper joins
        class_attempts = QuizAttempt.query\
            .join(Student)\
            .filter(
                Student.teacher_id == current_user.id,
                QuizAttempt.student_id.isnot(None)
            )
        
        total_class_attempts = class_attempts.count()
        class_performance = {
            'total_students': len(students),
            'total_attempts': total_class_attempts,
            'class_average': class_attempts.with_entities(
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

@analytics_bp.route('/analytics/performance_trends')
@login_required
def performance_trends():
    period = request.args.get('period', 'week')
    student_id = request.args.get('student_id', type=int)
    
    # Calculate date range based on period
    end_date = datetime.utcnow()
    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    else:  # year
        start_date = end_date - timedelta(days=365)
    
    # Build query with proper filters and joins
    query = QuizAttempt.query\
        .join(Quiz)\
        .filter(QuizAttempt.completed_at.between(start_date, end_date))
        
    if current_user.is_teacher:
        if student_id:
            query = query.filter(
                QuizAttempt.student_id == student_id,
                QuizAttempt.student_id.isnot(None)
            )
        else:
            query = query.join(Student).filter(
                Student.teacher_id == current_user.id,
                QuizAttempt.student_id.isnot(None)
            )
    else:
        query = query.filter_by(user_id=current_user.id)
    
    attempts = query.order_by(QuizAttempt.completed_at).all()
    
    # Format data for charts with curriculum information
    trend_data = [
        {
            'date': attempt.completed_at.strftime('%Y-%m-%d'),
            'score': attempt.score,
            'quiz': attempt.quiz.title,
            'curriculum': attempt.quiz.curriculum.title,
            'student': attempt.student_profile.name if attempt.student_profile else current_user.username
        }
        for attempt in attempts
    ]
    
    return jsonify({period: trend_data})
