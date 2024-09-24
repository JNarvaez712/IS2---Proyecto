import os

from pymongo import MongoClient


MONGO_URI = "mongodb+srv://davideduquiceno:L8VjsUftwaTv9CY@cluster0.tcpsp5o.mongodb.net/"



try:
    mongoClient = MongoClient(os.getenv("MONGO_URI"))
    db = mongoClient["RAGSystem"]
    coleccionDocumentos = db["Documento"]

    # Verifica si puedes contar los documentos en la colección
    print(f"Conexión a MongoDB exitosa. Documentos en la colección: {coleccionDocumentos.count_documents({})}")
except Exception as e:
    print(f"Error de conexión a MongoDB: {e}")