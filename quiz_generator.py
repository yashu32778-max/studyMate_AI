import google.generativeai as genai

model = genai.GenerativeModel("gemini-2.5-flash")

def generate_quiz(context):

    prompt = f"""
    Generate 5 MCQ questions from the following content:
    {context}
    
    Format each question exactly like this:
    Question: [The question text]
    A) [Option]
    B) [Option]
    C) [Option]
    D) [Option]
    Correct: [Correct Option Letter only, e.g., A]
    ---
    """

    response = model.generate_content(prompt)

    return response.text