
import google.generativeai as genai
import os

GENAI_KEY = "AIzaSyC2jK429eca2EKfTDIHszziOgDpYQhAmOY"
genai.configure(api_key=GENAI_KEY)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
