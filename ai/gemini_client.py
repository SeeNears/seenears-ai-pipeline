import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 모델 초기화 (서버 시작 시 1회)
model = genai.GenerativeModel("gemini-2.5-flash")