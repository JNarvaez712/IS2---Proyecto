import os

from pymongo import MongoClient


MONGO_URI = "mongodb+srv://JNarvaez712:Diosteama777%2B%2B@cluster0.ikdbyp4.mongodb.net/RAGSystem?authSource=admin&retryWrites=true&w=majority"



try:
    mongoClient = MongoClient(os.getenv("MONGO_URI"))
    db = mongoClient["RAGSystem"]
    coleccionDocumentos = db["Documento"]

    # Verifica si puedes contar los documentos en la colección
    print(f"Conexión a MongoDB exitosa. Documentos en la colección: {coleccionDocumentos.count_documents({})}")
except Exception as e:
    print(f"Error de conexión a MongoDB: {e}")

