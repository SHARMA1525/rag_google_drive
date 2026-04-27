import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
print(f"Testing key: {api_key[:10]}...")

client = Groq(api_key=api_key)
try:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "test"}],
    )
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
