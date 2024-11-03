from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, QuizAttempt, Quiz, Curriculum, Student
from sqlalchemy import func, desc, and_, extract
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def index():
    selected_student_id = request.args.get('student_id', type=int)
    
    # Base query with all necessary joins
    base_query = QuizAttempt.query\
        .join(Quiz)\
        .join(Quiz.curriculum)
    
    if current_user.is_teacher:
        if selected_student_id:
            # Get attempts for a specific student with validation
            student = Student.query.filter_by(id=selected_student_id, teacher_id=current_user.id).first_or_404()
            attempts = base_query\
                .join(Student)\
                .filter(
                    QuizAttempt.student_id == student.id,
                    Student.teacher_id == current_user.id
                ).order_by(QuizAttempt.completed_at.desc()).all()
        else:
            # Get all attempts from teacher's students
            attempts = base_query\
                .join(Student)\
                .filter(Student.teacher_id == current_user.id)\
                .order_by(QuizAttempt.completed_at.desc()).all()
    else:
        # Student viewing their own attempts
        student = Student.query.filter_by(email=current_user.email).first()
        if not student:
            flash('Öğrenci profili bulunamadı.', 'error')
            return redirect(url_for('dashboard.index'))
            
        attempts = base_query.filter(
            QuizAttempt.student_id == student.id
        ).order_by(QuizAttempt.completed_at.desc()).all()
    
    # Calculate overall statistics
    total_quizzes = len(attempts)
    if total_quizzes > 0:
        average_score = sum(attempt.score for attempt in attempts) / total_quizzes
        highest_score = max(attempt.score for attempt in attempts)
        lowest_score = min(attempt.score for attempt in attempts)
        
        # Get recent trend with proper student information
        recent_trend = [
            {
                'date': attempt.completed_at.strftime('%Y-%m-%d'),
                'score': attempt.score,
                'quiz': attempt.quiz.title,
                'student': attempt.student_profile.name if attempt.student_profile else current_user.username,
                'curriculum': attempt.quiz.curriculum.title
            }
            for attempt in sorted(attempts, key=lambda x: x.completed_at, reverse=True)[:10]
        ]
    else:
        average_score = highest_score = lowest_score = 0
        recent_trend = []
    
    # Calculate curriculum-wise performance
    curriculum_performance = {}
    for attempt in attempts:
        curriculum = attempt.quiz.curriculum
        if curriculum.title not in curriculum_performance:
            curriculum_performance[curriculum.title] = {
                'attempts': 0,
                'total_score': 0,
                'average': 0,
                'student_count': set(),
                'recent_scores': []
            }
        
        curr_perf = curriculum_performance[curriculum.title]
        curr_perf['attempts'] += 1
        curr_perf['total_score'] += attempt.score
        if attempt.student_id:
            curr_perf['student_count'].add(attempt.student_id)
        curr_perf['recent_scores'].append({
            'date': attempt.completed_at.strftime('%Y-%m-%d'),
            'score': attempt.score
        })
    
    # Calculate averages and prepare final curriculum data
    for curr_title, curr_data in curriculum_performance.items():
        curr_data['average'] = curr_data['total_score'] / curr_data['attempts']
        curr_data['student_count'] = len(curr_data['student_count'])
        curr_data['recent_scores'].sort(key=lambda x: x['date'], reverse=True)
        curr_data['recent_scores'] = curr_data['recent_scores'][:5]  # Keep only recent 5 scores
    
    # Get student list and performance data for teachers
    students = []
    student_performance = {}
    if current_user.is_teacher:
        students = Student.query.filter_by(teacher_id=current_user.id).all()
        
        for student in students:
            student_attempts = QuizAttempt.query\
                .join(Student)\
                .filter(
                    QuizAttempt.student_id == student.id,
                    Student.teacher_id == current_user.id
                )\
                .order_by(QuizAttempt.completed_at.desc())\
                .all()
            
            if student_attempts:
                avg_score = sum(a.score for a in student_attempts) / len(student_attempts)
                recent_score = student_attempts[0].score
                improvement = recent_score - student_attempts[-1].score if len(student_attempts) > 1 else 0
                
                # Calculate weekly progress
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_attempts = [a for a in student_attempts if a.completed_at >= week_ago]
                weekly_progress = sum(a.score for a in recent_attempts) / len(recent_attempts) if recent_attempts else 0
            else:
                avg_score = recent_score = improvement = weekly_progress = 0
            
            student_performance[student.id] = {
                'name': student.name,
                'average_score': avg_score,
                'recent_score': recent_score,
                'total_attempts': len(student_attempts),
                'improvement': improvement,
                'weekly_progress': weekly_progress
            }
    
    # Calculate class-wide performance metrics for teachers
    class_performance = None
    if current_user.is_teacher:
        total_class_attempts = QuizAttempt.query\
            .join(Student)\
            .filter(Student.teacher_id == current_user.id)\
            .count()
        
        if total_class_attempts > 0:
            class_avg = db.session.query(func.avg(QuizAttempt.score))\
                .join(Student)\
                .filter(Student.teacher_id == current_user.id)\
                .scalar() or 0
            
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_completion = QuizAttempt.query\
                .join(Student)\
                .filter(
                    Student.teacher_id == current_user.id,
                    QuizAttempt.completed_at >= week_ago
                ).count()
            
            class_performance = {
                'total_students': len(students),
                'total_attempts': total_class_attempts,
                'class_average': class_avg,
                'recent_completion_rate': (recent_completion / total_class_attempts * 100)
            }
        else:
            class_performance = {
                'total_students': len(students),
                'total_attempts': 0,
                'class_average': 0,
                'recent_completion_rate': 0
            }
    
    return render_template(
        'analytics/index.html',
        total_quizzes=total_quizzes,
        average_score=average_score,
        highest_score=highest_score,
        lowest_score=lowest_score,
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
        date_format = '%Y-%m-%d'
        date_extract = func.date(QuizAttempt.completed_at)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
        date_format = '%Y-%m-%d'
        date_extract = func.date(QuizAttempt.completed_at)
    else:  # year
        start_date = end_date - timedelta(days=365)
        date_format = '%Y-%m'
        date_extract = func.date_trunc('month', QuizAttempt.completed_at)
    
    # Build base query with proper joins
    base_query = QuizAttempt.query\
        .join(Quiz)\
        .join(Quiz.curriculum)\
        .filter(QuizAttempt.completed_at.between(start_date, end_date))
    
    if current_user.is_teacher:
        if student_id:
            # Verify student belongs to teacher
            student = Student.query.filter_by(id=student_id, teacher_id=current_user.id).first_or_404()
            base_query = base_query\
                .join(Student)\
                .filter(
                    QuizAttempt.student_id == student.id,
                    Student.teacher_id == current_user.id
                )
        else:
            base_query = base_query\
                .join(Student)\
                .filter(Student.teacher_id == current_user.id)
    else:
        student = Student.query.filter_by(email=current_user.email).first()
        if student:
            base_query = base_query.filter(QuizAttempt.student_id == student.id)
        else:
            return jsonify({period: []})
    
    # Get attempts grouped by date
    attempts_by_date = base_query\
        .with_entities(
            date_extract.label('date'),
            func.avg(QuizAttempt.score).label('avg_score'),
            func.count(QuizAttempt.id).label('attempt_count')
        )\
        .group_by('date')\
        .order_by('date')\
        .all()
    
    # Format data for charts
    trend_data = [
        {
            'date': date.strftime(date_format) if period != 'year' else date.strftime('%Y-%m'),
            'score': float(avg_score),
            'attempts': attempt_count
        }
        for date, avg_score, attempt_count in attempts_by_date
    ]
    
    return jsonify({period: trend_data})
