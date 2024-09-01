import openai
import chromadb
from chromadb.config import Settings
import os

# Configurar la API de OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Función para obtener incrustaciones usando OpenAI
def get_embeddings(text):
    response = openai.Embedding.create(model="text-embedding-ada-002", input=text)
    return response['data'][0]['embedding']

# Crear una base de datos en memoria usando ChromaDB
client = chromadb.Client(Settings(persist_directory="."))
collection = client.create_collection(name="documentos")

# Insertar documentos y sus incrustaciones en la base de datos
documentos = [
    {"id": "1", "content": "Python es un lenguaje de programación de alto nivel"},
    {"id": "2", "content": "JavaScript se utiliza principalmente en desarrollo web"},
    {"id": "3", "content": "El aprendizaje automático es una rama de la inteligencia artificial"}
]

for doc in documentos:
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

# Método principal para ejecutar el programa y permitir al usuario realizar consultas
def main():
    modo = input("Seleccione el modo (1: Buscar documentos similares, 2: Responder consulta): ")
    if modo == "1":
        consulta = input("Ingrese su consulta: ")
        n_results = int(input("Ingrese el número de resultados que desea ver: "))
        resultados = realizar_consulta(consulta, n_results)
        for resultado in resultados:
            print(f"Documento similar (ID: {resultado['id']}): {resultado['texto']}")
    elif modo == "2":
        consulta = input("Ingrese su consulta: ")
        respuesta = responder_consulta(consulta)
        print(f"Respuesta: {respuesta}")
    else:
        print("Modo no válido. Por favor, seleccione 1 o 2.")

if __name__ == "__main__":
    main()







