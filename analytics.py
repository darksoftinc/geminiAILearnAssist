from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import User, QuizAttempt, Quiz, Curriculum
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import pandas as pd

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def index():
    # Get user's quiz attempts
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
                'quiz': attempt.quiz.title
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

    # Get peer comparison data (for students)
    if not current_user.is_teacher:
        peer_data = QuizAttempt.query.join(Quiz).join(User).filter(
            User.is_teacher == False,
            User.id != current_user.id
        ).with_entities(
            func.avg(QuizAttempt.score).label('peer_average')
        ).scalar() or 0
    else:
        peer_data = None

    # Get class performance data (for teachers)
    class_performance = None
    if current_user.is_teacher:
        class_performance = {
            'total_students': User.query.filter_by(is_teacher=False).count(),
            'total_attempts': QuizAttempt.query.join(User).filter(User.is_teacher==False).count(),
            'class_average': QuizAttempt.query.join(User).filter(
                User.is_teacher==False
            ).with_entities(
                func.avg(QuizAttempt.score).label('average')
            ).scalar() or 0
        }

    return render_template(
        'analytics/index.html',
        total_quizzes=total_quizzes,
        average_score=average_score,
        highest_score=highest_score,
        recent_trend=recent_trend,
        curriculum_performance=curriculum_performance,
        peer_average=peer_data,
        class_performance=class_performance
    )

@analytics_bp.route('/analytics/performance_trends')
@login_required
def performance_trends():
    timeframes = {
        'week': datetime.now() - timedelta(days=7),
        'month': datetime.now() - timedelta(days=30),
        'year': datetime.now() - timedelta(days=365)
    }
    
    trends = {}
    for period, start_date in timeframes.items():
        attempts = QuizAttempt.query.filter(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.completed_at >= start_date
        ).order_by(QuizAttempt.completed_at).all()
        
        trends[period] = [
            {
                'date': attempt.completed_at.strftime('%Y-%m-%d'),
                'score': attempt.score,
                'quiz': attempt.quiz.title
            }
            for attempt in attempts
        ]
    
    return jsonify(trends)
