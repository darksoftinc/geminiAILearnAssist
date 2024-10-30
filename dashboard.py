from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Curriculum

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    curricula = Curriculum.query.all()
    
    # Get quiz scores for the progress chart
    attempts = current_user.quiz_attempts
    dates = [attempt.completed_at.strftime('%Y-%m-%d') for attempt in attempts]
    scores = [attempt.score for attempt in attempts]
    
    return render_template('dashboard/index.html', 
                         curricula=curricula,
                         dates=dates,
                         scores=scores)
