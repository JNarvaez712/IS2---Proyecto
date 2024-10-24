import uuid
from datetime import datetime
import bcrypt

class MongoDBAdapter:
    def __init__(self, mongo_client):
        self.db = mongo_client["RAGSystem"]
        self.coleccionUsuarios = self.db["Usuario"]

    def relacionar_documento_con_usuario(self, id_usuario, id_documento, metadatos):
       self.coleccionUsuarios.update_one(
           {"id_usuario":id_usuario},
           {
               "$addToSet":{
                   "documentos":{
                       "id_documento":id_documento,
                       "metadatos": metadatos,
                       "fecha": datetime.utcnow(),
                   }
               }
           },
           upsert=True
       )

    # Función para registrar un nuevo usuario
    def registrar_usuario(self, username, password, role="Usuario"):
        # Verificar si el usuario ya existe
        if self.coleccionUsuarios.find_one({"username": username}):
            return "El usuario ya existe"

        # Hashear la contraseña
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insertar el nuevo usuario en la colección
        self.coleccionUsuarios.insert_one({"username": username, "password": hashed_password.decode("utf-8"), "role": role, "user_id": str(uuid.uuid4())})
        return "Usuario registrado exitosamente"

    # Función para autenticar un usuario
    def autenticar_usuario(self, username, password):
        # Buscar el usuario en la colección
        usuario = self.coleccionUsuarios.find_one({"username": username})
        if not usuario:
            return None, "Usuario no encontrado", None

        # Verificar la contraseña
        if bcrypt.checkpw(password.encode('utf-8'), usuario["password"].encode("utf-8")):
            return usuario['role'], "Inicio de sesión exitoso", usuario["user_id"]  # Devuelve el rol y user_id

        else:
            return None, "Contraseña incorrecta", None

    # Función para actualizar el rol de un usuario
    def actualizar_rol_usuario(self, username, nuevo_rol):
        # Verificar si el usuario existe
        usuario_encontrado = self.coleccionUsuarios.find_one({"username": username})
        if usuario_encontrado:
            # Actualizar el rol del usuario
            self.coleccionUsuarios.update_one({"username": username}, {"$set": {"role": nuevo_rol}})
            return f"Rol de {username} actualizado a {nuevo_rol}"
        else:
            return "Usuario no encontrado"

