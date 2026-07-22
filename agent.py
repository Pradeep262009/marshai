import google.generativeai as genai
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env from the same directory as this file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Gemini API key from .env file
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()

if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    raise ValueError("ERROR: GEMINI_API_KEY not configured in .env file!")

genai.configure(api_key=GEMINI_API_KEY, transport="rest")

model = genai.GenerativeModel(
    model_name="gemini-3.5-flash",   # Fast + free tier
    system_instruction="""
    You are MARSHAI, a smart and friendly AI tutor for university students.
    Your job is to explain Computer Science concepts clearly and simply.
    Always keep answers SHORT, CLEAR and BEGINNER-FRIENDLY.
    Use bullet points and simple examples.
    Never write long confusing paragraphs.
    Topics: Algorithms, Data Structures, Python, OOP, Networking, OS, Databases, AI, and more.
    """
)

def ask_marshai(question: str, image_data: dict = None) -> str:
    try:
        contents = [question]
        if image_data:
            import base64
            img_bytes = base64.b64decode(image_data['data'])
            img_part = {
                'mime_type': image_data['mime_type'],
                'data': img_bytes
            }
            contents.append(img_part)
        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        return f"⚠️ MARSHAI Error: {str(e)}"

def ask_marshai_stream(question: str, image_data: dict = None, history: list = None):
    try:
        # Prepend history to question for memory
        if history:
            context = "Chat History:\n"
            for msg in history:
                context += f"{msg['role']}: {msg['content']}\n"
            context += f"\nNew Question: {question}"
            contents = [context]
        else:
            contents = [question]

        if image_data:
            import base64
            img_bytes = base64.b64decode(image_data['data'])
            img_part = {
                'mime_type': image_data['mime_type'],
                'data': img_bytes
            }
            contents.append(img_part)
        
        # Do not use stream=True to prevent gRPC/REST streaming hangs in serverless environments
        response = model.generate_content(contents)
        
        if response.text:
            # Yield the entire response as a single chunk
            yield response.text
        else:
            yield "*(Debug) Error: The AI model returned an empty response.*"
            
    except Exception as e:
        yield f"⚠️ MARSHAI Error: {str(e)}"