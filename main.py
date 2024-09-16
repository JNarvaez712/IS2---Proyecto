import openai
import os
import streamlit as st
import json
from PyPDF2 import PdfReader
import docx

# Configurar la API de OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Función para responder a cualquier consulta usando OpenAI
def responder_consulta(consulta, contexto=""):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{contexto}\n\n{consulta}"}
        ],
        max_tokens=5000
    )
    respuesta = response.choices[0].message['content'].strip()
    return respuesta.replace('. ', '.\n')

# Función para cargar el historial de chat desde un archivo JSON
def cargar_historial():
    if os.path.exists("chat_history.json"):
        with open("chat_history.json", "r") as file:
            return json.load(file)
    return []

# Función para guardar el historial de chat en un archivo JSON
def guardar_historial(historial):
    with open("chat_history.json", "w") as file:
        json.dump(historial, file)

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

# Crear la interfaz gráfica con Streamlit
st.title("Consulta Chat")

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
            if message["role"] == "user":
                st.write(f"**Usuario:** {message['content']}")
            else:
                st.write(f"**Asistente:** {message['content']}")
        if st.button(f"Eliminar Chat {i + 1}", key=f"delete_{i}"):
            st.session_state.previous_chats.pop(i)
            guardar_historial(st.session_state.previous_chats)

# Formulario para la consulta y subida de documentos
with st.form(key='consulta_form'):
    consulta = st.text_input("Ingrese su consulta:")
    uploaded_file = st.file_uploader("Sube un documento (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"], label_visibility="collapsed")
    submit_button = st.form_submit_button(label='Enviar')

contexto = ""
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        texto_documento = extraer_texto_pdf(uploaded_file)
    elif uploaded_file.type == "text/plain":
        texto_documento = uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        texto_documento = extraer_texto_docx(uploaded_file)
    contexto = f"Texto del documento:\n{texto_documento}"
    st.session_state.chat_history.append({"role": "system", "content": contexto})

if submit_button:
    respuesta = responder_consulta(consulta, contexto)
    st.session_state.chat_history.append({"role": "user", "content": consulta})
    st.session_state.chat_history.append({"role": "system", "content": respuesta})

# Mostrar el historial de chat en orden inverso
st.subheader("Historial de Chat")
# Agrupar mensajes en pares de usuario y asistente
paired_messages = []
i = 0
while i < len(st.session_state.chat_history):
    user_message = st.session_state.chat_history[i]
    assistant_message = st.session_state.chat_history[i + 1] if i + 1 < len(st.session_state.chat_history) else None
    paired_messages.append((user_message, assistant_message))
    i += 2

# Mostrar los pares en orden inverso
for user_message, assistant_message in reversed(paired_messages):
    if user_message:
        st.write(f"**Usuario:** {user_message['content']}")
    if assistant_message:
        st.write(f"**Asistente:** {assistant_message['content']}")
    st.markdown("<hr>", unsafe_allow_html=True)

# Guardar el historial actual al archivo JSON
guardar_historial(st.session_state.previous_chats)






