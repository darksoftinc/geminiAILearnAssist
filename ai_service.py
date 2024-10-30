from app import model

def generate_curriculum_content(topic, level="intermediate"):
    prompt = f"""Generate a detailed curriculum for teaching {topic} at {level} level.
    Include:
    - Learning objectives
    - Key concepts
    - Practical exercises
    - Assessment criteria
    Format the response in markdown."""
    
    response = model.generate_content(prompt)
    return response.text

def generate_quiz_questions(curriculum_content, num_questions=5):
    prompt = f"""Based on this curriculum content:
    {curriculum_content}
    
    Generate {num_questions} multiple-choice questions. 
    For each question, provide:
    - The question text
    - 4 possible answers (with one correct answer)
    - The correct answer
    Format as JSON."""
    
    response = model.generate_content(prompt)
    return response.text
