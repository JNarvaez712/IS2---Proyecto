from datetime import datetime
from app.core.ports import AlmacenamientoChunks
from app.api.dependencies import get_mongo_client

class MongoDBAdapter(AlmacenamientoChunks):
    def __init__(self, mongoClient: get_mongo_client()):
        self.db = mongoClient["RAGSystem"]
        self.coleccionDocumentos = self.db["Documento"]


    # Función para almacenar los chunks en MongoDB
    def almacenar_chunks(self, idDocumento, chunks, metadatos):

         for i, chunk in enumerate(chunks):
             documento = {
                 "chunk_id": i,
                 "idDocumento": idDocumento,
                 "texto": chunk,
                 "metadatos": metadatos,
                 "fecha_subida": datetime.utcnow(),
                 "tipo_documento": metadatos.get("tipo_documento", "desconocido"),
             }
             self.coleccionDocumentos.insert_one(documento)

