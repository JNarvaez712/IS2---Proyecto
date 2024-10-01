import os
import openai

import json
from PyPDF2 import PdfReader
import docx
from app.api.dependencies import configure_openai

# Inicializar dependencias
configure_openai()

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