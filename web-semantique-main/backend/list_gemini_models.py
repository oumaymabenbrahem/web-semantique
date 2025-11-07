import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    print("Liste des modèles Gemini disponibles:\n")
    print("="*60)
    
    try:
        models = genai.list_models()
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"✅ {model.name}")
                print(f"   Description: {model.display_name}")
                print(f"   Méthodes: {', '.join(model.supported_generation_methods)}")
                print()
    except Exception as e:
        print(f"Erreur: {e}")
else:
    print("Clé API Gemini non trouvée dans .env")
