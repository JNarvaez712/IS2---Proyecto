import os
import openai
import json
from PyPDF2 import PdfReader
import docx
from app.api.dependencies import configure_openai, get_mongo_client  # Importar la función para obtener el cliente de MongoDB
from app.adapters.mongodb_adapter import MongoDBAdapter

# Inicializar dependencias
configure_openai()

# Inicializar el cliente de MongoDB
mongo_client = get_mongo_client()  # Obtener el cliente de MongoDB

# Inicializar el adaptador de MongoDB con el cliente
mongo_adapter = MongoDBAdapter(mongo_client)

# Función para responder a cualquier consulta usando OpenAI
def responder_consulta(consulta, contexto):

    print(f"Contexto: {contexto}")
    print(f"Consulta: {consulta}")

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

# Función para dividir el texto en fragmentos (chunks)
def dividir_texto_en_chunks(texto, tamano_chunk=500, solapamiento=50):
    chunks = []
    for i in range(0, len(texto), tamano_chunk - solapamiento):
        chunks.append(texto[i:i + tamano_chunk])
    return chunks

# Funciones relacionadas con los usuarios utilizando el adaptador de MongoDB
def registrar_usuario(username, password, role="Usuario"):
    return mongo_adapter.registrar_usuario(username, password, role)

def autenticar_usuario(username, password):
    return mongo_adapter.autenticar_usuario(username, password)

def actualizar_rol_usuario(username, nuevo_rol):
    return mongo_adapter.actualizar_rol_usuario(username, nuevo_rol)
