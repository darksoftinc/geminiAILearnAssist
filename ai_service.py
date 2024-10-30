import os
import json
import logging
import google.generativeai as genai
from google.api_core import retry
from flask import current_app

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

def generate_curriculum_content(topic: str, level: str = "intermediate") -> str:
    """Generate curriculum content using Gemini AI with error handling and retries"""
    try:
        prompt = f"""Lütfen aşağıdaki {level} seviyesinde {topic} konusu için detaylı bir müfredat oluşturun.
        Şunları içermelidir:
        - Öğrenme hedefleri
        - Ana kavramlar
        - Pratik alıştırmalar
        - Değerlendirme kriterleri
        Yanıtı markdown formatında verin.
        
        Not: Tüm içerik Türkçe olmalıdır."""
        
        @retry.Retry(predicate=retry.if_exception_type(Exception))
        def _generate_with_retry():
            response = current_app.config['GENAI_MODEL'].generate_content(prompt)
            if not response or not response.text:
                raise AIServiceError("Gemini AI'dan boş yanıt alındı")
            return response.text
            
        return _generate_with_retry()
        
    except Exception as e:
        current_app.logger.error(f"Müfredat içeriği oluşturulurken hata: {str(e)}")
        raise AIServiceError(f"Müfredat oluşturulamadı: {str(e)}")

def generate_quiz_questions(curriculum_content: str, num_questions: int = 5) -> list:
    """Generate quiz questions with enhanced error handling and JSON validation"""
    try:
        prompt = f"""Bu müfredat içeriğine dayanarak:
        {curriculum_content}
        
        {num_questions} adet çoktan seçmeli soru oluşturun.
        Yanıtı tam olarak aşağıdaki JSON formatında verin:
        
        {{
            "questions": [
                {{
                    "question": "Soru metni",
                    "options": ["Seçenek 1", "Seçenek 2", "Seçenek 3", "Seçenek 4"],
                    "correct_answer": "Doğru cevap metni (seçeneklerden biri olmalı)"
                }},
                ...
            ]
        }}
        
        Önemli kurallar:
        1. Her soru için tam olarak 4 seçenek olmalı
        2. Doğru cevap mutlaka seçeneklerden biri olmalı
        3. Tüm içerik Türkçe olmalı
        4. JSON formatı tam olarak belirtilen yapıda olmalı
        """
        
        @retry.Retry(predicate=retry.if_exception_type(Exception))
        def _generate_with_retry():
            response = current_app.config['GENAI_MODEL'].generate_content(prompt)
            if not response or not response.text:
                raise AIServiceError("Gemini AI'dan boş yanıt alındı")
            return response.text
        
        # Get response and parse JSON
        response_text = _generate_with_retry()
        current_app.logger.debug(f"AI Response: {response_text}")
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            raise AIServiceError("AI yanıtı geçerli bir JSON formatında değil")
            
        # Validate JSON structure
        if not isinstance(data, dict) or "questions" not in data:
            raise AIServiceError("AI yanıtı beklenen JSON yapısında değil")
            
        questions = data["questions"]
        if not isinstance(questions, list) or len(questions) != num_questions:
            raise AIServiceError(f"Beklenen soru sayısı ({num_questions}) ile eşleşmiyor")
            
        # Validate each question
        for i, q in enumerate(questions):
            if not all(key in q for key in ["question", "options", "correct_answer"]):
                raise AIServiceError(f"Soru {i+1} gerekli tüm alanları içermiyor")
            if not isinstance(q["options"], list) or len(q["options"]) != 4:
                raise AIServiceError(f"Soru {i+1} tam olarak 4 seçenek içermiyor")
            if q["correct_answer"] not in q["options"]:
                raise AIServiceError(f"Soru {i+1} için doğru cevap seçenekler arasında değil")
                
        return questions
            
    except AIServiceError as e:
        current_app.logger.error(f"Quiz soruları oluşturulurken özel hata: {str(e)}")
        raise
    except Exception as e:
        current_app.logger.error(f"Quiz soruları oluşturulurken beklenmeyen hata: {str(e)}")
        raise AIServiceError("Quiz soruları oluşturulurken teknik bir hata oluştu")
