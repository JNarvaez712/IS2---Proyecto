from pymongo import MongoClient


MONGO_URI = "mongodb+srv://davideduquiceno:MongoAdmin@cluster0.tcpsp5o.mongodb.net/"



client = MongoClient(MONGO_URI)

try:
    # Intenta listar las bases de datos para verificar la conexión
    print(client.list_database_names())
    print("Conexión exitosa a MongoDB.")
except Exception as e:
    print(f"Error de conexión: {e}")