import os
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

def generate_quiz_questions(curriculum_content: str, num_questions: int = 5) -> str:
    """Generate quiz questions with error handling and retries"""
    try:
        prompt = f"""Bu müfredat içeriğine dayanarak:
        {curriculum_content}
        
        {num_questions} adet çoktan seçmeli soru oluşturun. 
        Her soru için şunları sağlayın:
        - Soru metni
        - 4 olası cevap (bir doğru cevap ile)
        - Doğru cevap
        JSON formatında yanıt verin.
        
        Not: Tüm sorular ve cevaplar Türkçe olmalıdır."""
        
        @retry.Retry(predicate=retry.if_exception_type(Exception))
        def _generate_with_retry():
            response = current_app.config['GENAI_MODEL'].generate_content(prompt)
            if not response or not response.text:
                raise AIServiceError("Gemini AI'dan boş yanıt alındı")
            return response.text
            
        return _generate_with_retry()
        
    except Exception as e:
        current_app.logger.error(f"Quiz soruları oluşturulurken hata: {str(e)}")
        raise AIServiceError(f"Quiz soruları oluşturulamadı: {str(e)}")
