from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from groq import Groq
from app.config import config

app = FastAPI(
    title="Asistente OD API",
    description="API para el Asistente de Diseño Organizacional - Star Model",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cliente = Groq(api_key=config.GROQ_API_KEY)
MODELO = config.MODELO

class MensajeRequest(BaseModel):
    mensaje: str
    nivel: str
    historial: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    respuesta: str
    nivel_usado: str
    pilares_mencionados: Optional[List[str]] = []

def obtener_prompt_base(nivel: str) -> str:
    base = """
    Eres un consultor senior especializado en Diseño Organizacional y el Modelo de las Estrellas (Star Model) de Jay Galbraith.
    Tus 6 pilares son:
    1. ESTRATEGIA (Clientes, propuesta de valor, ventajas competitivas, familia empresaria)
    2. ESTRUCTURA (Agrupación del trabajo, organigramas, autoridad formal)
    3. PROCESOS (Flujos de trabajo, toma de decisiones, coordinación)
    4. PERSONAS (Competencias, perfiles, selección y desarrollo)
    5. RECOMPENSAS (Incentivos, retribución, reconocimiento, promoción)
    6. CULTURA (Valores, comportamientos, normas implícitas)
    
    REGLA DE ORO: Si el usuario pregunta solo por un pilar, recuérdale que los otros 5 existen y que están interconectados.
    Responde SIEMPRE en español claro y didáctico.
    """
    
    if nivel == "Inicial":
        return base + """
        El usuario es un EXPLORADOR (nivel inicial).
        - Usa lenguaje sencillo, metáforas y ejemplos de empresas famosas (Google, Netflix, Toyota).
        - NO uses tecnicismos como RACI, BPMN o 9-Box Grid.
        - Termina siempre con una pregunta para que el usuario reflexione.
        - No supongas conocimientos previos.
        """
    elif nivel == "Intermedio":
        return base + """
        El usuario es un DIAGNOSTICADOR (nivel intermedio).
        - Usa herramientas como: Matriz RACI, DAFO, Business Model Canvas, Cuadro de Mando Integral, Temas de Empresa Familiar.
        - Señala al menos 2 posibles desajustes entre pilares.
        - Ofrece pasos prácticos para aplicar el diagnóstico.
        - Presenta posibles Riesgos.
        """
    else:
        return base + """
        El usuario es un ARQUITECTO DE SISTEMAS (nivel experto).
        - Profundiza en dinámicas sistémicas: bucles de retroalimentación, organización ambidiestra.
        - Cuestiona sus supuestos con preguntas incómodas.
        - Ofrece análisis de consecuencias a 12-24 meses.
        - Habla de gestión de subculturas y contraculturas.
        - Analiza su problemática de Empresa Familiar.
        - Remarca en los Riesgos y acciones de mitigación.
        """

@app.get("/")
def root():
    return {
        "mensaje": "🏛️ Asistente OD API v1.0",
        "pilares": ["Estrategia", "Estructura", "Procesos", "Personas", "Recompensas", "Cultura", "Familia Empresaria"],
        "niveles": ["Inicial", "Intermedio", "Experto"],
        "estado": "Operativo"
    }

@app.post("/chat", response_model=ChatResponse)
async def responder_chat(solicitud: MensajeRequest):
    try:
        # 1. Obtener prompt del sistema según el nivel seleccionad
        prompt_sistema = obtener_prompt_por_nivel(solicitud.nivel)
        
        # Asegurar que prompt_sistema sea un string
        if isinstance(prompt_sistema, dict):
            prompt_sistema = prompt_sistema.get("prompt", str(prompt_sistema))

        # 2. Armar los mensajes incluyendo el historial previo
        mensajes = [{"role": "system", "content": str(prompt_sistema)}]

        # Agregar el historial enviado desde el frontend
        if solicitud.historial:
            for msg in solicitud.historial:
                mensajes.append({
                    "role": msg.get("role", "user"),
                    "content": str(msg.get("content", ""))
                })

        # Agregar el mensaje actual del usuario
        mensajes.append({"role": "user", "content": str(solicitud.mensaje)})

        # 3. Llamar a Groq API
        chat_completion = client.chat.completions.create(
            messages=mensajes,
            model=config.MODELO,
            temperature=0.7,
        )

        respuesta_texto = chat_completion.choices[0].message.content

        # 4. Retornar coincidiendo exactamente con ChatResponse
        return {
            "respuesta": respuesta_texto,
            "nivel_usado": solicitud.nivel,
            "pilares_mencionados": []
        }

    except Exception as e:
        # Devuelve el texto exacto del error en lugar de fallar a ciegas
        raise HTTPException(status_code=500, detail=f"Error en backend: {str(e)}")
    
async def chat(request: MensajeRequest):
    try:
        if request.nivel not in ["Inicial", "Intermedio", "Experto"]:
            request.nivel = "Intermedio"
        
        prompt_sistema = obtener_prompt_base(request.nivel)
        mensajes = [{"role": "system", "content": prompt_sistema}]
        
        if request.historial:
            mensajes.extend(request.historial)
        
        mensajes.append({"role": "user", "content": request.mensaje})
        
        respuesta = cliente.chat.completions.create(
            model=MODELO,
            messages=mensajes,
            temperature=0.4,
            max_tokens=1000
        )
        
        texto_respuesta = respuesta.choices[0].message.content
        
        pilares_mencionados = []
        pilares_clave = ["estrategia", "estructura", "procesos", "personas", "recompensas", "cultura", "familia empresaria"]
        texto_lower = texto_respuesta.lower()
        for pilar in pilares_clave:
            if pilar in texto_lower:
                pilares_mencionados.append(pilar.capitalize())
        
        return ChatResponse(
            respuesta=texto_respuesta,
            nivel_usado=request.nivel,
            pilares_mencionados=pilares_mencionados[:5]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Groq: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "healthy", "modelo": MODELO}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)