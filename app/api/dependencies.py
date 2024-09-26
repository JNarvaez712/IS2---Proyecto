import chromadb
from chromadb.config import Settings
from pymongo import MongoClient
import os
import openai

# Configurar la API de OpenAI
def configure_openai():
    openai.api_key = os.getenv('OPENAI_API_KEY')

# Configurar ChromaDB
def get_chroma_client(persist_directory="./chroma_db"):
    return chromadb.Client(Settings(persist_directory=persist_directory))


# Configurar MongoDB
def get_mongo_client():
    return MongoClient(os.getenv("MONGO_URI"))
