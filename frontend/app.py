import streamlit as st
import requests

BACKEND_URL = "https://asistente-do.onrender.com/chat"  # URL del backend FastAPI

st.set_page_config(page_title="Asistente de Diseño Organizacional", page_icon="🏛️")

st.title("🏛️ Asistente de Diseño Organizacional")
st.caption("Modelo de las Estrellas (Star Model) de Jay Galbraith")

# Configuración en la barra lateral
st.sidebar.header("Parámetros del Consultor")
nivel_seleccionado = st.sidebar.selectbox(
    "Selecciona el Nivel de Interacción:",
    ["Inicial", "Intermedio", "Experto"],
    index=1
)

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial de conversación
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada de usuario
if prompt := st.chat_input("¿En qué proceso o estructura quieres profundizar hoy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Preparar el payload enviando el historial previo en el formato esperado por FastAPI
    historial_backend = [
        {"role": msg["role"], "content": msg["content"]} 
        for msg in st.session_state.messages[:-1]
    ]

    payload = {
        "mensaje": prompt,
        "nivel": nivel_seleccionado,
        "historial": historial_backend
    }

    with st.chat_message("assistant"):
        with st.spinner("Analizando componentes organizacionales..."):
            try:
                response = requests.post(BACKEND_URL, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    respuesta_texto = data.get("respuesta", "")
                    pilares = data.get("pilares_mencionados", [])

                    st.markdown(respuesta_texto)
                    
                    if pilares:
                        st.caption(f"📌 Pilares identificados en este análisis: {', '.join(pilares)}")

                    st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})
                else:
                    st.error(f"Error en la API backend: {response.status_code}")
            except Exception as e:
                st.error(f"No se pudo conectar con el servidor backend: {e}")