# mongodb_adapter.py
from datetime import datetime
from app.core.ports import AlmacenamientoChunks
import bcrypt

class MongoDBAdapter(AlmacenamientoChunks):
    def __init__(self, mongo_client):
        self.db = mongo_client["RAGSystem"]
        self.coleccionDocumentos = self.db["Documento"]
        self.coleccionUsuarios = self.db["Usuario"]

    # Función para almacenar los chunks en MongoDB
    def almacenar_chunks(self, id_documento, chunks, metadatos):
        for i, chunk in enumerate(chunks):
            documento = {
                "chunk_id": i,
                "id_documento": id_documento,
                "texto": chunk,
                "metadatos": metadatos,
                "fecha_subida": datetime.utcnow(),
                "tipo_documento": metadatos.get("tipo_documento", "desconocido"),
            }
            self.coleccionDocumentos.insert_one(documento)

    # Función para registrar un nuevo usuario
    def registrar_usuario(self, username, password, role="Usuario"):
        if self.coleccionUsuarios.find_one({"username": username}):
            return "El usuario ya existe"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.coleccionUsuarios.insert_one({"username": username, "password": hashed_password, "role": role})
        return "Usuario registrado exitosamente"

    # Función para autenticar un usuario
    def autenticar_usuario(self, username, password):
        usuario = self.coleccionUsuarios.find_one({"username": username})
        if not usuario:
            return None, "Usuario no encontrado"
        if bcrypt.checkpw(password.encode('utf-8'), usuario["password"]):
            role = usuario.get("role", "Usuario")
            return role, "Autenticación exitosa"
        else:
            return None, "Contraseña incorrecta"

    # Función para actualizar el rol de un usuario
    def actualizar_rol_usuario(self, username, nuevo_rol):
        result = self.coleccionUsuarios.update_one({"username": username}, {"$set": {"role": nuevo_rol}})
        return result.modified_count > 0

    # Función para eliminar un usuario (para limpieza en pruebas)
    def eliminar_usuario(self, username):
        result = self.coleccionUsuarios.delete_one({"username": username})
        return result.deleted_count > 0

    # Función para obtener un usuario por username
    def obtener_usuario(self, username):
        usuario = self.coleccionUsuarios.find_one({"username": username})
        return usuario  # Retorna el documento del usuario o None si no existe


