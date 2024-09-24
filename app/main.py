import openai
import os
from dotenv import load_dotenv
import streamlit as st
import json
from PyPDF2 import PdfReader
import docx
import chromadb
from chromadb.config import Settings
from pymongo import MongoClient
from datetime import datetime

# Cargar las variables de entorno
load_dotenv()


# Configurar MongoDB
mongoClient = MongoClient(os.getenv("MONGO_URI"))
db = mongoClient["RAGSystem"]
coleccionDocumentos = db["Documento"]

# Configurar la API de OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configurar ChromaDB
chroma_client = chromadb.Client(Settings(persist_directory="./chroma_db"))

# Función para almacenar los chunks en MongoDB
def almacenar_chunks(idDocumento, chunks, metadatos):
     for i, chunk in enumerate(chunks):
         documento = {
             "chunk_id": i,
             "idDocumento": idDocumento,
             "texto": chunk,
             "metadata": metadatos,
             "fecha_subida": datetime.utcnow(),
             "tipo_documento": metadatos.get("tipo_documento", "desconocido"),
         }
         coleccionDocumentos.insert_one(documento)

# Función para almacenar los chunks en ChromaDB
def almacenar_chunks_en_chromadb(chunks):
    collection = chroma_client.get_or_create_collection("document_chunks")
    for i, chunk in enumerate(chunks):
        collection.add(
            ids=[f"chunk_{i}"],
            documents=[chunk],
            metadatas=[{"chunk_id": i}]
        )

# Función para responder a cualquier consulta usando OpenAI
def responder_consulta(consulta, contexto=""):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente útil."},
            {"role": "user", "content": f"{contexto}\n\n{consulta}"}
        ],
        max_tokens=1000
    )
    respuesta = response['choices'][0]['message']['content'].strip()
    return respuesta.replace('. ', '.\n')

# Función para guardar el historial de chat en un archivo JSON
def guardar_historial(historial):
    with open("../chat_history.json", "w") as file:
        json.dump(historial, file)



# Función para cargar el historial de chat desde un archivo JSON
def cargar_historial():
    if os.path.exists("../chat_history.json"):
        with open("../chat_history.json", "r") as file:
            return json.load(file)
    return []



# Función para extraer texto de un archivo PDF
def extraer_texto_pdf(file):
    reader = PdfReader(file)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text()
    return texto

# Función para extraer texto de un archivo DOCX
def extraer_texto_docx(file):
    doc = docx.Document(file)
    texto = ""
    for para in doc.paragraphs:
        texto += para.text + "\n"
    return texto

# Función para dividir el texto en fragmentos (chunks)
def dividir_texto_en_chunks(texto, tamano_chunk=500, solapamiento=50):
    chunks = []
    for i in range(0, len(texto), tamano_chunk - solapamiento):
        chunks.append(texto[i:i + tamano_chunk])
    return chunks

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

# Formulario para la consulta y subida de documentos
with st.form(key='consulta_form'):
    consulta = st.text_input("Ingrese su consulta:")
    uploaded_file = st.file_uploader("Sube un documento (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"],
                                     label_visibility="collapsed")
    submit_button = st.form_submit_button(label='Enviar')

contexto = ""
texto_documento = ""
tipo_documento = ""
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        texto_documento = extraer_texto_pdf(uploaded_file)
        tipo_documento = "PDF"
    elif uploaded_file.type == "text/plain":
        texto_documento = uploaded_file.read().decode("utf-8")
        tipo_documento = "TXT"
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        texto_documento = extraer_texto_docx(uploaded_file)
        tipo_documento = "DOCX"

    # Crear metadatos del documento
    metadatos = {
        "titulo": uploaded_file.name,
        "autor": "Desconocido",  # Aquí puedes extraer o añadir información sobre el autor
        "fecha_creacion": datetime.utcnow(),
        "categoria": "General",  # Puedes personalizar según la categoría del documento
        "tipo_documento": tipo_documento
    }

    # Generar un ID único para el documento
    idDocumento = f"doc_{int(datetime.utcnow().timestamp())}"

    # Dividir el texto en chunks
    chunks = dividir_texto_en_chunks(texto_documento)

    # Almacenar chunks en ChromaDB
    almacenar_chunks_en_chromadb(chunks)

    # Almacenar chunks y metadatos en MongoDB
    almacenar_chunks(idDocumento, chunks, metadatos)

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
