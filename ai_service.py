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
        prompt = f"""Generate a detailed curriculum for teaching {topic} at {level} level.
        Include:
        - Learning objectives
        - Key concepts
        - Practical exercises
        - Assessment criteria
        Format the response in markdown."""
        
        @retry.Retry(predicate=retry.if_exception_type(Exception))
        def _generate_with_retry():
            response = current_app.config['GENAI_MODEL'].generate_content(prompt)
            if not response or not response.text:
                raise AIServiceError("Empty response received from Gemini AI")
            return response.text
            
        return _generate_with_retry()
        
    except Exception as e:
        current_app.logger.error(f"Error generating curriculum content: {str(e)}")
        raise AIServiceError(f"Failed to generate curriculum: {str(e)}")

def generate_quiz_questions(curriculum_content: str, num_questions: int = 5) -> str:
    """Generate quiz questions with error handling and retries"""
    try:
        prompt = f"""Based on this curriculum content:
        {curriculum_content}
        
        Generate {num_questions} multiple-choice questions. 
        For each question, provide:
        - The question text
        - 4 possible answers (with one correct answer)
        - The correct answer
        Format as JSON."""
        
        @retry.Retry(predicate=retry.if_exception_type(Exception))
        def _generate_with_retry():
            response = current_app.config['GENAI_MODEL'].generate_content(prompt)
            if not response or not response.text:
                raise AIServiceError("Empty response received from Gemini AI")
            return response.text
            
        return _generate_with_retry()
        
    except Exception as e:
        current_app.logger.error(f"Error generating quiz questions: {str(e)}")
        raise AIServiceError(f"Failed to generate quiz questions: {str(e)}")
