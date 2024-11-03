from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_teacher = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships with cascade delete
    curricula = db.relationship('Curriculum', backref='author', lazy=True, cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True, cascade='all, delete-orphan')
    students = db.relationship('Student', backref='teacher', lazy=True, cascade='all, delete-orphan')

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    grade = db.Column(db.String(20), nullable=False)  # class/grade
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_student_teacher', teacher_id),  # Index for faster teacher lookups
    )

class Curriculum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships with cascade delete
    quizzes = db.relationship('Quiz', backref='curriculum', lazy=True, cascade='all, delete-orphan')

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    curriculum_id = db.Column(db.Integer, db.ForeignKey('curriculum.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships with cascade delete
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('QuizAssignment', backref='quiz', lazy=True, cascade='all, delete-orphan')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)  # Store multiple choice options

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    score = db.Column(db.Float)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define the relationship with Student model
    student_profile = db.relationship('Student', backref='attempts', foreign_keys=[student_id])
    
    __table_args__ = (
        db.Index('idx_student_completed', student_id, completed_at),  # Index for faster student performance queries
        db.Index('idx_quiz_student', quiz_id, student_id),  # Index for quiz-student lookups
        db.Index('idx_user_completed', user_id, completed_at),  # Index for user attempt queries
    )

class QuizAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        db.Index('idx_assignment_student', student_id, completed),  # Index for faster assignment lookups
    )
