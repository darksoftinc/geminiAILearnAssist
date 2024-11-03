from flask_socketio import SocketIO
from flask import current_app
from flask_login import current_user

socketio = SocketIO()

def init_app(app):
    socketio.init_app(app, async_mode='eventlet', cors_allowed_origins="*")

def emit_quiz_completion(attempt):
    """Quiz tamamlama bildirimini gönder"""
    try:
        notification_data = {
            'type': 'quiz_completion',
            'quiz_title': attempt.quiz.title,
            'score': round(attempt.score, 1),
            'student_name': attempt.student.username,
            'timestamp': attempt.completed_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Öğrenci quiz'i tamamladığında öğretmenlere bildirim gönder
        if not attempt.student.is_teacher:
            socketio.emit('notification', notification_data, room='teachers')
            
        # Quiz'i tamamlayan öğrenciye de bildirim gönder
        socketio.emit('notification', notification_data, room=f'user_{attempt.student.id}')
        
    except Exception as e:
        current_app.logger.error(f"Quiz tamamlama bildirimi gönderilirken hata: {str(e)}")
