import os
import json
import logging
import re
import google.generativeai as genai
from google.api_core import retry
from flask import current_app

class AIServiceError(Exception):
    """AI servisi için özel hata sınıfı"""
    pass

def generate_curriculum_content(topic: str, level: str = "intermediate") -> str:
    """Gemini AI kullanarak müfredat içeriği oluştur ve hata yönetimini sağla"""
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

def clean_json_response(response_text: str) -> str:
    """AI yanıtından JSON temizle ve ayıkla"""
    # Hata ayıklama için ham yanıtı logla
    current_app.logger.debug(f"Ham AI Yanıtı:\n{response_text}")
    
    # Markdown kod bloklarını kaldır
    text = re.sub(r'```(?:json)?\n?(.*?)\n```', r'\1', response_text, flags=re.DOTALL)
    
    # JSON yapısını bul
    match = re.search(r'({[\s\S]*})', text)
    if match:
        text = match.group(1)
    
    # JSON olmayan metinleri baştan ve sondan temizle
    text = text.strip()
    
    current_app.logger.debug(f"Temizlenmiş JSON Yanıtı:\n{text}")
    return text

def generate_quiz_questions(curriculum_content: str, num_questions: int = 5) -> list:
    """Gelişmiş hata yönetimi ve JSON doğrulama ile quiz soruları oluştur"""
    try:
        prompt = f"""Lütfen aşağıdaki müfredata göre {num_questions} adet soru oluşturun:
{curriculum_content}

ÖNEMLİ: Yanıtı SADECE aşağıdaki JSON formatında verin, başka açıklama veya metin EKLEMEDEN:

{
    "questions": [
        {
            "question": "Soru metni buraya gelecek?",
            "options": [
                "A) Birinci seçenek",
                "B) İkinci seçenek",
                "C) Üçüncü seçenek",
                "D) Dördüncü seçenek"
            ],
            "correct_answer": "A) Birinci seçenek"
        }
    ]
}

KURALLAR:
1. Yanıt SADECE JSON olmalıdır, başka metin veya açıklama OLMAMALIDIR
2. Her soru için tam olarak 4 seçenek olmalıdır
3. Seçenekler A), B), C), D) şeklinde başlamalıdır
4. Doğru cevap mutlaka seçeneklerden biri olmalıdır
5. Tüm içerik Türkçe olmalıdır"""

        @retry.Retry(predicate=retry.if_exception_type(Exception))
        def _generate_with_retry():
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    response = current_app.config['GENAI_MODEL'].generate_content(prompt)
                    if not response or not response.text:
                        raise AIServiceError("Gemini AI'dan boş yanıt alındı")
                    
                    # JSON temizle ve ayrıştır
                    json_text = clean_json_response(response.text)
                    data = json.loads(json_text)
                    
                    # JSON yapısını doğrula
                    if not isinstance(data, dict) or "questions" not in data:
                        raise AIServiceError("Yanıt beklenen JSON yapısında değil")
                    
                    questions = data["questions"]
                    if not isinstance(questions, list) or len(questions) != num_questions:
                        raise AIServiceError(f"Beklenen soru sayısı ({num_questions}) ile eşleşmiyor")
                    
                    # Her soruyu doğrula
                    for i, q in enumerate(questions):
                        if not all(key in q for key in ["question", "options", "correct_answer"]):
                            raise AIServiceError(f"{i+1}. soru gerekli tüm alanları içermiyor")
                        if not isinstance(q["options"], list) or len(q["options"]) != 4:
                            raise AIServiceError(f"{i+1}. soru tam olarak 4 seçenek içermiyor")
                        if not all(opt.startswith(('A)', 'B)', 'C)', 'D)')) for opt in q["options"]):
                            raise AIServiceError(f"{i+1}. soru için seçenekler A), B), C), D) ile başlamalıdır")
                        if q["correct_answer"] not in q["options"]:
                            raise AIServiceError(f"{i+1}. soru için doğru cevap seçenekler arasında değil")
                    
                    return questions
                    
                except json.JSONDecodeError:
                    if attempt == max_attempts - 1:
                        raise AIServiceError("JSON formatında geçerli bir yanıt alınamadı")
                    current_app.logger.warning(f"JSON ayrıştırma hatası, yeniden deneniyor (Deneme {attempt + 1}/{max_attempts})")
                    continue
                    
                except AIServiceError as e:
                    if attempt == max_attempts - 1:
                        raise
                    current_app.logger.warning(f"AI yanıtı geçersiz, yeniden deneniyor (Deneme {attempt + 1}/{max_attempts}): {str(e)}")
                    continue
            
            raise AIServiceError("Maksimum deneme sayısına ulaşıldı")
            
        return _generate_with_retry()
            
    except AIServiceError as e:
        current_app.logger.error(f"Quiz soruları oluşturulurken özel hata: {str(e)}")
        raise
    except Exception as e:
        current_app.logger.error(f"Quiz soruları oluşturulurken beklenmeyen hata: {str(e)}")
        raise AIServiceError("Quiz soruları oluşturulurken teknik bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
