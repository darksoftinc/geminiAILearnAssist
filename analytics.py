# Add new imports for advanced analytics
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, QuizAttempt, Quiz, Curriculum, Student, db
from sqlalchemy import func, desc, and_, extract, case
from datetime import datetime, timedelta
import statistics

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def index():
    selected_student_id = request.args.get('student_id', type=int)
    
    # Base query with proper joins for quiz attempts
    base_query = QuizAttempt.query\
        .join(Quiz)\
        .join(Quiz.curriculum)\
        .join(Student, QuizAttempt.student_id == Student.id)
    
    if current_user.is_teacher:
        if selected_student_id:
            # Get attempts for a specific student with validation
            student = Student.query.filter_by(
                id=selected_student_id,
                teacher_id=current_user.id
            ).first_or_404()
            
            attempts = base_query.filter(
                QuizAttempt.student_id == student.id,
                Student.teacher_id == current_user.id
            ).order_by(QuizAttempt.completed_at.desc()).all()
        else:
            # Get all attempts from teacher's students
            attempts = base_query.filter(
                Student.teacher_id == current_user.id
            ).order_by(QuizAttempt.completed_at.desc()).all()
    else:
        # Student viewing their own attempts
        student = Student.query.filter_by(email=current_user.email).first()
        if not student:
            flash('Öğrenci profili bulunamadı.', 'error')
            return redirect(url_for('dashboard.index'))
            
        attempts = base_query.filter(
            QuizAttempt.student_id == student.id
        ).order_by(QuizAttempt.completed_at.desc()).all()
    
    # Calculate overall statistics with proper error handling
    total_quizzes = len(attempts)
    if total_quizzes > 0:
        scores = [attempt.score for attempt in attempts if attempt.score is not None]
        if scores:
            average_score = statistics.mean(scores)
            median_score = statistics.median(scores)
            try:
                std_dev = statistics.stdev(scores)
            except statistics.StatisticsError:
                std_dev = 0
            highest_score = max(scores)
            lowest_score = min(scores)
            
            # Calculate improvement trend
            if len(scores) >= 2:
                recent_avg = statistics.mean(scores[:5]) if len(scores) >= 5 else statistics.mean(scores)
                older_avg = statistics.mean(scores[-5:]) if len(scores) >= 5 else scores[-1]
                improvement_rate = ((recent_avg - older_avg) / older_avg) * 100
            else:
                improvement_rate = 0
            
            # Calculate performance quartiles
            quartiles = statistics.quantiles(scores)
        else:
            average_score = median_score = std_dev = highest_score = lowest_score = improvement_rate = 0
            quartiles = [0, 0, 0]
        
        # Get recent trend with proper student information and error handling
        recent_trend = []
        trend_scores = []
        for attempt in sorted(attempts, key=lambda x: x.completed_at, reverse=True)[:10]:
            try:
                score = attempt.score
                trend_scores.append(score)
                trend_data = {
                    'date': attempt.completed_at.strftime('%Y-%m-%d'),
                    'score': score,
                    'quiz': attempt.quiz.title,
                    'student': attempt.student_profile.name if attempt.student_profile else 'Unknown',
                    'curriculum': attempt.quiz.curriculum.title,
                    'moving_average': statistics.mean(trend_scores) if trend_scores else 0
                }
                recent_trend.append(trend_data)
            except AttributeError:
                continue
    else:
        average_score = median_score = std_dev = highest_score = lowest_score = improvement_rate = 0
        quartiles = [0, 0, 0]
        recent_trend = []
    
    # Calculate curriculum-wise performance with error handling
    curriculum_performance = {}
    for attempt in attempts:
        try:
            curriculum = attempt.quiz.curriculum
            if curriculum.title not in curriculum_performance:
                curriculum_performance[curriculum.title] = {
                    'attempts': 0,
                    'total_score': 0,
                    'average': 0,
                    'student_count': set(),
                    'scores': [],
                    'recent_scores': []
                }
            
            if attempt.score is not None:
                curr_perf = curriculum_performance[curriculum.title]
                curr_perf['attempts'] += 1
                curr_perf['total_score'] += attempt.score
                curr_perf['scores'].append(attempt.score)
                if attempt.student_id:
                    curr_perf['student_count'].add(attempt.student_id)
                curr_perf['recent_scores'].append({
                    'date': attempt.completed_at.strftime('%Y-%m-%d'),
                    'score': attempt.score
                })
        except AttributeError:
            continue
    
    # Calculate advanced statistics for each curriculum
    for curr_title, curr_data in curriculum_performance.items():
        if curr_data['attempts'] > 0:
            scores = curr_data['scores']
            curr_data['average'] = statistics.mean(scores)
            curr_data['median'] = statistics.median(scores)
            try:
                curr_data['std_dev'] = statistics.stdev(scores)
            except statistics.StatisticsError:
                curr_data['std_dev'] = 0
            curr_data['quartiles'] = statistics.quantiles(scores) if len(scores) > 1 else [0, 0, 0]
            curr_data['student_count'] = len(curr_data['student_count'])
            curr_data['recent_scores'].sort(key=lambda x: x['date'], reverse=True)
            curr_data['recent_scores'] = curr_data['recent_scores'][:5]
            
            # Calculate improvement trend
            if len(scores) >= 2:
                recent_avg = statistics.mean(scores[:5]) if len(scores) >= 5 else statistics.mean(scores)
                older_avg = statistics.mean(scores[-5:]) if len(scores) >= 5 else scores[-1]
                curr_data['improvement_rate'] = ((recent_avg - older_avg) / older_avg) * 100
            else:
                curr_data['improvement_rate'] = 0
    
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
                valid_scores = [a.score for a in student_attempts if a.score is not None]
                if valid_scores:
                    avg_score = statistics.mean(valid_scores)
                    median_score = statistics.median(valid_scores)
                    try:
                        std_dev = statistics.stdev(valid_scores)
                    except statistics.StatisticsError:
                        std_dev = 0
                    recent_score = student_attempts[0].score
                    improvement = recent_score - student_attempts[-1].score if len(valid_scores) > 1 else 0
                    
                    # Calculate weekly progress
                    week_ago = datetime.utcnow() - timedelta(days=7)
                    recent_attempts = [a.score for a in student_attempts 
                                    if a.completed_at >= week_ago and a.score is not None]
                    weekly_progress = statistics.mean(recent_attempts) if recent_attempts else 0
                    
                    # Calculate relative performance
                    class_avg = average_score
                    performance_percentile = (
                        len([s for s in scores if s < avg_score]) / len(scores) * 100
                    ) if scores else 0
                else:
                    avg_score = median_score = std_dev = recent_score = improvement = weekly_progress = performance_percentile = 0
            else:
                avg_score = median_score = std_dev = recent_score = improvement = weekly_progress = performance_percentile = 0
            
            student_performance[student.id] = {
                'name': student.name,
                'average_score': avg_score,
                'median_score': median_score,
                'std_dev': std_dev,
                'recent_score': recent_score,
                'total_attempts': len(student_attempts),
                'improvement': improvement,
                'weekly_progress': weekly_progress,
                'performance_percentile': performance_percentile
            }
    
    # Calculate class-wide performance metrics for teachers
    class_performance = None
    if current_user.is_teacher:
        total_class_attempts = QuizAttempt.query\
            .join(Student)\
            .filter(Student.teacher_id == current_user.id)\
            .count()
        
        if total_class_attempts > 0:
            class_scores = db.session.query(QuizAttempt.score)\
                .join(Student)\
                .filter(
                    Student.teacher_id == current_user.id,
                    QuizAttempt.score.isnot(None)
                ).all()
            
            class_scores = [score[0] for score in class_scores]
            
            if class_scores:
                class_avg = statistics.mean(class_scores)
                class_median = statistics.median(class_scores)
                try:
                    class_std_dev = statistics.stdev(class_scores)
                except statistics.StatisticsError:
                    class_std_dev = 0
                class_quartiles = statistics.quantiles(class_scores)
            else:
                class_avg = class_median = class_std_dev = 0
                class_quartiles = [0, 0, 0]
            
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
                'class_median': class_median,
                'class_std_dev': class_std_dev,
                'class_quartiles': class_quartiles,
                'recent_completion_rate': (recent_completion / total_class_attempts * 100) if total_class_attempts > 0 else 0
            }
        else:
            class_performance = {
                'total_students': len(students),
                'total_attempts': 0,
                'class_average': 0,
                'class_median': 0,
                'class_std_dev': 0,
                'class_quartiles': [0, 0, 0],
                'recent_completion_rate': 0
            }
    
    return render_template(
        'analytics/index.html',
        total_quizzes=total_quizzes,
        average_score=average_score,
        median_score=median_score,
        std_dev=std_dev,
        highest_score=highest_score,
        lowest_score=lowest_score,
        improvement_rate=improvement_rate,
        quartiles=quartiles,
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
        .join(Student, QuizAttempt.student_id == Student.id)\
        .filter(QuizAttempt.completed_at.between(start_date, end_date))
    
    if current_user.is_teacher:
        if student_id:
            # Verify student belongs to teacher
            student = Student.query.filter_by(id=student_id, teacher_id=current_user.id).first_or_404()
            base_query = base_query.filter(
                QuizAttempt.student_id == student.id,
                Student.teacher_id == current_user.id
            )
        else:
            base_query = base_query.filter(Student.teacher_id == current_user.id)
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
    
    # Format data for charts with error handling
    trend_data = []
    for date, avg_score, attempt_count in attempts_by_date:
        try:
            trend_data.append({
                'date': date.strftime(date_format) if period != 'year' else date.strftime('%Y-%m'),
                'score': float(avg_score or 0),
                'attempts': attempt_count
            })
        except (AttributeError, ValueError):
            continue
    
    return jsonify({period: trend_data})
