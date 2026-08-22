import os
from dotenv import load_dotenv

# Carga la variable de entorno buscando Tutor.env dentro de la carpeta backend
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, "Tutor.env")
load_dotenv(env_path)

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MODELO = "openai/gpt-oss-120b"
    
    if not GROQ_API_KEY:
        raise ValueError("❌ GROQ_API_KEY no encontrada. Asegúrate de tener Tutor.env dentro de /backend")

config = Config()