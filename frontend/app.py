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
    # Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Preparar datos para el backend
    payload = {
        "mensaje": prompt,
        "nivel": nivel_seleccionado,
        "historial": [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]
    }

    # Procesar respuesta del asistente
    with st.chat_message("assistant"):
        with st.spinner("Analizando respuesta..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    respuesta_texto = data.get("respuesta", "")
                    pilares = data.get("pilares_mencionados", [])

                    st.markdown(respuesta_texto)
                    
                    if pilares:
                        st.caption(f"📌 Pilares identificados: {', '.join(pilares)}")

                    st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})
                else:
                    try:
                        detalle = response.json().get("detail", response.text)
                    except Exception:
                        detalle = response.text
                    st.error(f"Error en la API backend ({response.status_code}): {detalle}")

            except Exception as e:
                st.error(f"No se pudo conectar con el servidor: {str(e)}")