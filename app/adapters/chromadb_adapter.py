from app.core.ports import AlmacenamientoChunks

class ChromaDBAdapter(AlmacenamientoChunks):
    def __init__(self, chroma_client):
        self.collection = chroma_client.get_or_create_collection("document_chunks")

    def almacenar_chunks(self, id_documento, chunks, metadatos):
        for i, chunk in enumerate(chunks):
            self.collection.add(
                ids=[f"chunk_{i}"],
                documents=[chunk],
                metadatas=[{"chunk_id": i}]
            )

