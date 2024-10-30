from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Quiz, Question, QuizAttempt, db
from ai_service import generate_quiz_questions

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/quiz/create/<int:curriculum_id>', methods=['GET', 'POST'])
@login_required
def create(curriculum_id):
    if not current_user.is_teacher:
        flash('Only teachers can create quizzes')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        num_questions = int(request.form.get('num_questions', 5))
        
        quiz = Quiz(
            title=title,
            curriculum_id=curriculum_id
        )
        db.session.add(quiz)
        
        # Generate questions using Gemini AI
        questions_data = generate_quiz_questions(quiz.curriculum.content, num_questions)
        
        for q_data in questions_data:
            question = Question(
                quiz_id=quiz.id,
                question_text=q_data['question'],
                correct_answer=q_data['correct_answer'],
                options=q_data['options']
            )
            db.session.add(question)
        
        db.session.commit()
        return redirect(url_for('quiz.list'))
    
    return render_template('quiz/create.html', curriculum_id=curriculum_id)

@quiz_bp.route('/quiz/<int:id>/take', methods=['GET', 'POST'])
@login_required
def take(id):
    quiz = Quiz.query.get_or_404(id)
    
    if request.method == 'POST':
        score = 0
        total_questions = len(quiz.questions)
        
        for question in quiz.questions:
            answer = request.form.get(f'question_{question.id}')
            if answer == question.correct_answer:
                score += 1
        
        final_score = (score / total_questions) * 100
        
        attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz.id,
            score=final_score
        )
        db.session.add(attempt)
        db.session.commit()
        
        return redirect(url_for('quiz.results', attempt_id=attempt.id))
    
    return render_template('quiz/take.html', quiz=quiz)

@quiz_bp.route('/quiz/results/<int:attempt_id>')
@login_required
def results(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        flash('You can only view your own results')
        return redirect(url_for('dashboard.index'))
    
    return render_template('quiz/results.html', attempt=attempt)
