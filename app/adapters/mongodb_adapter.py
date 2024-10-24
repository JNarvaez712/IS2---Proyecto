from datetime import datetime

import bcrypt

from app.core.ports import AlmacenamientoChunks
from app.api.dependencies import get_mongo_client

class MongoDBAdapter(AlmacenamientoChunks):
    def __init__(self, mongoClient: get_mongo_client()):
        self.db = mongoClient["RAGSystem"]
        self.coleccionDocumentos = self.db["Documento"]
        self.coleccionUsuarios = self.db["Usuario"]

    # Función para almacenar los chunks en MongoDB
    def almacenar_chunks(self, idDocumento, chunks, metadatos):

         for i, chunk in enumerate(chunks):
             chroma_id = f"chunk_{idDocumento}_{i}"
             documento = {
                 "chunk_id": i,
                 "idDocumento": idDocumento,
                 "chroma_id": chroma_id,
                 "texto": chunk,
                 "metadatos": metadatos,
                 "fecha_subida": datetime.utcnow(),
                 "tipo_documento": metadatos.get("tipo_documento", "desconocido"),
             }
             self.coleccionDocumentos.insert_one(documento)

    # Función para registrar un nuevo usuario en la base de datos
    def registrar_usuario(self, username, password, role="Usuario"):
        # Verificar si el usuario ya existe
        if self.coleccionUsuarios.find_one({"username": username}):
            return "El usuario ya existe"

        # Hashear la contraseña
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insertar el nuevo usuario en la colección
        self.coleccionUsuarios.insert_one({"username": username, "password": hashed_password, "role": role})
        return "Usuario registrado exitosamente"

    # Función para autenticar un usuario en la base de datos
    def autenticar_usuario(self, username, password):
        # Buscar el usuario en la colección
        usuario = self.coleccionUsuarios.find_one({"username": username})
        if not usuario:
            return None, "Usuario no encontrado"

        # Verificar la contraseña
        if bcrypt.checkpw(password.encode('utf-8'), usuario["password"]):
            role = usuario.get("role", "Usuario")  # Asignar rol predeterminado si no tiene uno
            return role, "Autenticación exitosa"
        else:
            return None, "Contraseña incorrecta"

    def rol_admin(self, username, nuevo_rol):
        usuario_encontrado = self.coleccionUsuarios.find_one({"username": username})
        if usuario_encontrado:
            self.coleccionUsuarios.update_one({"username": username}, {"$set": {"role": nuevo_rol}})
            return f"Rol de {username} actualizado a {nuevo_rol}"
        else:
            return "Usuario no encontrado"