import openai
import chromadb
from chromadb.config import Settings
import os
import streamlit as st
import json

# Configurar la API de OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Función para obtener incrustaciones usando OpenAI
def get_embeddings(text):
    response = openai.Embedding.create(model="text-embedding-ada-002", input=text)
    return response['data'][0]['embedding']

# Crear una base de datos en memoria usando ChromaDB
client = chromadb.Client(Settings(persist_directory="."))
collection_name = "documentos"

# Verificar si la colección ya existe
collections = client.list_collections()
if collection_name in [col.name for col in collections]:
    collection = client.get_collection(name=collection_name)
else:
    collection = client.create_collection(name=collection_name)

# Insertar documentos y sus incrustaciones en la base de datos si no están ya insertados
documentos = [
    {"id": "1", "content": "Python es un lenguaje de programación de alto nivel"},
    {"id": "2", "content": "JavaScript se utiliza principalmente en desarrollo web"},
    {"id": "3", "content": "El aprendizaje automático es una rama de la inteligencia artificial"}
]

# Obtener los IDs existentes en la colección
existing_ids = set(collection.get()['ids'])

for doc in documentos:
    if doc["id"] not in existing_ids:
        embedding = get_embeddings(doc["content"])
        collection.add(
            ids=[doc["id"]],
            embeddings=[embedding],
            metadatas=[{"texto": doc["content"]}],
        )

# Función para realizar una consulta y retornar los resultados filtrados
def realizar_consulta(consulta, n_results=3):
    consulta_embedding = get_embeddings(consulta)
    resultados = collection.query(
        query_embeddings=[consulta_embedding],
        n_results=n_results
    )
    resultados_formateados = [
        {"id": id, "texto": resultado['texto']}
        for resultado, id in zip(resultados['metadatas'][0], resultados['ids'][0])
    ]
    return resultados_formateados

# Función para responder a cualquier consulta usando OpenAI sin tener en cuenta los documentos almacenados
def responder_consulta(consulta):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": consulta}
        ],
        max_tokens=150
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
            st.experimental_rerun()

modo = st.radio("Seleccione el modo:", ("1: Buscar documentos similares", "2: Responder consulta"))

with st.form(key='consulta_form'):
    consulta = st.text_input("Ingrese su consulta:")
    if modo == "1: Buscar documentos similares":
        n_results = st.number_input("Número de resultados que desea ver:", min_value=1, max_value=10, value=3)
    submit_button = st.form_submit_button(label='Enviar')

if submit_button:
    if modo == "1: Buscar documentos similares":
        resultados = realizar_consulta(consulta, n_results)
        st.session_state.chat_history.append({"role": "user", "content": consulta})
        for resultado in resultados:
            st.session_state.chat_history.append({"role": "system", "content": f"Documento similar (ID: {resultado['id']}): {resultado['texto']}"})
    elif modo == "2: Responder consulta":
        respuesta = responder_consulta(consulta)
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







