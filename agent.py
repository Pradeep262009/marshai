import google.generativeai as genai
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env from the same directory as this file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Gemini API key from .env file
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    raise ValueError("ERROR: GEMINI_API_KEY not configured in .env file!")

genai.configure(api_key=GEMINI_API_KEY)

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

def ask_marshai_stream(question: str, image_data: dict = None):
    try:
        with open("debug_chunks.txt", "w", encoding="utf-8") as f:
            f.write("STREAM STARTED\n")
            
            first_chunk = "*(Debug) Connecting to AI...* "
            f.write(f"YIELDING: {first_chunk}\n")
            yield first_chunk
            
            contents = [question]
            if image_data:
                import base64
                img_bytes = base64.b64decode(image_data['data'])
                img_part = {
                    'mime_type': image_data['mime_type'],
                    'data': img_bytes
                }
                contents.append(img_part)
            
            f.write("CALLING GENERATE CONTENT\n")
            response = model.generate_content(contents, stream=True)
            
            has_chunks = False
            for chunk in response:
                if chunk.text:
                    has_chunks = True
                    f.write(f"YIELDING: {repr(chunk.text)}\n")
                    f.flush()
                    yield chunk.text
                    
            if not has_chunks:
                err_chunk = " *(Debug) Error: The AI model returned an empty response.*"
                f.write(f"YIELDING: {err_chunk}\n")
                yield err_chunk
                
            f.write("STREAM FINISHED\n")
            
    except Exception as e:
        with open("debug_chunks.txt", "a", encoding="utf-8") as f:
            f.write(f"EXCEPTION: {str(e)}\n")
        yield f"⚠️ MARSHAI Error: {str(e)}"