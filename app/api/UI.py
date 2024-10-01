from datetime import datetime

import streamlit as st

from app.usecases import *

from app.adapters.mongodb_adapter import MongoDBAdapter
from app.adapters.chromadb_adapter import ChromaDBAdapter
from app.api.dependencies import *
from app.core.ports import *


# Configurar la API de OpenAI
configure_openai()

# Crear la interfaz gráfica con Streamlit
st.title("Sistema de Gestión de Respuestas (RAG)")

# Inicializar el historial de chat y los chats anteriores
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'previous_chats' not in st.session_state:
    st.session_state.previous_chats = cargar_historial()

# Botón para iniciar un nuevo chat
if st.sidebar.button("Nuevo Chat"):
    if st.session_state.chat_history:
        st.session_state.previous_chats.append(st.session_state.chat_history)
        guardar_historial(st.session_state.previous_chats)
    st.session_state.chat_history = []

# Mostrar los chats anteriores en la barra lateral
st.sidebar.subheader("Chats Anteriores")
for i, chat in enumerate(st.session_state.previous_chats):
    with st.sidebar.expander(f"Chat {i + 1}"):
        for message in chat:
            st.write(message['content'])
        if st.button(f"Cargar Chat {i + 1}", key=f"load_{i}"):
            st.session_state.chat_history = chat
        if st.button(f"Eliminar Chat {i + 1}", key=f"delete_{i}"):
            st.session_state.previous_chats.pop(i)
            guardar_historial(st.session_state.previous_chats)

# FUnción para mapear procesadores según el tipo de archivo
def obtener_procesador(uploaded_file):
    mime_type = uploaded_file.type
    procesadores = {
        "application/pdf": PDFProcessor(),
        "text/plain": TXTProcessor(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DOCXProcessor()
    }
    return procesadores.get(mime_type, None)



# Formulario para la consulta y subida de documentos
with st.form(key='consulta_form'):
    consulta = st.text_input("Ingrese su consulta:")
    uploaded_file = st.file_uploader("Sube un documento (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"],
                                     label_visibility="collapsed")
    submit_button = st.form_submit_button(label='Enviar')

contexto = ""
texto_documento = ""
tipo_documento = ""


# Inicializar clientes de base de datos
mongo_client = get_mongo_client()
chroma_client = get_chroma_client()

# Crear instancias de los adaptadores
mongo_adapter = MongoDBAdapter(mongo_client)
chroma_adapter = ChromaDBAdapter(chroma_client)


if uploaded_file:
    procesador = obtener_procesador(uploaded_file)

    if procesador:
        # Extraer el texto y el tipo de archivo
        texto_documento = procesador.extract_text(uploaded_file)
        tipo_documento = procesador.get_file_type()


    # Crear metadatos del documento
    metadatos = {
        "titulo": uploaded_file.name,
        "fecha_creacion": datetime.utcnow(),
        "tipo_documento": tipo_documento
    }

    # Generar un ID único para el documento
    idDocumento = f"doc_{int(datetime.utcnow().timestamp())}"

    # Dividir el texto en chunks
    chunks = dividir_texto_en_chunks(texto_documento)

    # Almacenar chunks en ChromaDB
    chroma_adapter.almacenar_chunks(chunks)

    # Almacenar chunks y metadatos en MongoDB
    mongo_adapter.almacenar_chunks(idDocumento, chunks, metadatos)


    # Agregar el contexto al historial de chat
    contexto = f"Texto del documento cargado: {uploaded_file.name}"
    st.session_state.chat_history.append({"role": "system", "content": contexto})

if submit_button:
    respuesta = responder_consulta(consulta, texto_documento)
    st.session_state.chat_history.append({"role": "assistant", "content": respuesta})

# Mostrar el historial de chat en orden inverso
st.subheader("Historial de Chat")
# Mostrar solo las respuestas en orden inverso
for message in reversed(st.session_state.chat_history):
    if message["role"] == "assistant":
        st.write(message['content'])
        st.markdown("<hr>", unsafe_allow_html=True)

# Guardar el historial actual al archivo JSON
guardar_historial(st.session_state.previous_chats)