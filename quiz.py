import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Quiz, Question, QuizAttempt, Curriculum, db
from ai_service import generate_quiz_questions, AIServiceError
from notifications import emit_quiz_completion

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/quiz/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_teacher:
        flash('Bu işlemi sadece öğretmenler yapabilir.', 'error')
        return redirect(url_for('dashboard.index'))
    
    curricula = Curriculum.query.filter_by(author_id=current_user.id).all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        curriculum_id = request.form.get('curriculum_id')
        try:
            num_questions = int(request.form.get('num_questions', '5'))
        except ValueError:
            flash('Geçersiz soru sayısı seçildi.', 'error')
            return render_template('quiz/create.html', curricula=curricula)
        
        if not title or not curriculum_id:
            flash('Quiz başlığı ve müfredat seçimi zorunludur.', 'error')
            return render_template('quiz/create.html', curricula=curricula)
            
        if num_questions not in [5, 10, 15, 20]:
            flash('Geçersiz soru sayısı seçildi.', 'error')
            return render_template('quiz/create.html', curricula=curricula)
        
        curriculum = Curriculum.query.get_or_404(curriculum_id)
        if curriculum.author_id != current_user.id:
            flash('Sadece kendi müfredatınız için quiz oluşturabilirsiniz.', 'error')
            return render_template('quiz/create.html', curricula=curricula)
        
        try:
            current_app.logger.info(f"Quiz oluşturuluyor: {title}, Soru sayısı: {num_questions}")
            questions_data = generate_quiz_questions(curriculum.content, num_questions)
            
            quiz = Quiz(
                title=title,
                curriculum_id=curriculum_id
            )
            db.session.add(quiz)
            db.session.flush()
            
            for q_data in questions_data:
                question = Question(
                    quiz_id=quiz.id,
                    question_text=q_data['question'],
                    options=q_data['options'],
                    correct_answer=q_data['correct_answer']
                )
                db.session.add(question)
            
            db.session.commit()
            current_app.logger.info(f"Quiz başarıyla oluşturuldu: ID={quiz.id}")
            flash('Quiz başarıyla oluşturuldu!', 'success')
            return redirect(url_for('curriculum.view', id=curriculum_id))
            
        except AIServiceError as e:
            current_app.logger.error(f"AI Servisi Hatası: {str(e)}")
            flash(f'Quiz oluşturulurken hata: {str(e)}', 'error')
            return render_template('quiz/create.html', curricula=curricula)
            
        except Exception as e:
            current_app.logger.error(f"Quiz oluşturma hatası: {str(e)}")
            db.session.rollback()
            flash('Quiz oluşturulurken beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.', 'error')
            return render_template('quiz/create.html', curricula=curricula)
    
    return render_template('quiz/create.html', curricula=curricula)

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
        
        # Emit real-time notification
        emit_quiz_completion(attempt)
        
        flash(f'Quiz tamamlandı! Puanınız: {final_score:.1f}%', 'success')
        return redirect(url_for('quiz.results', attempt_id=attempt.id))
    
    return render_template('quiz/take.html', quiz=quiz)

@quiz_bp.route('/quiz/results/<int:attempt_id>')
@login_required
def results(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        flash('Sadece kendi sonuçlarınızı görüntüleyebilirsiniz.', 'error')
        return redirect(url_for('dashboard.index'))
    
    return render_template('quiz/results.html', attempt=attempt)
