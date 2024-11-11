import pytest
import os
import json
from app.api.dependencies import configure_openai, get_mongo_client
from app.adapters.openAI_adapter import OpenAIConsultas
from app.adapters.mongodb_adapter import MongoDBAdapter
from app.usecases import responder_consulta, guardar_historial, cargar_historial, dividir_texto_en_chunks, \
    registrar_usuario, autenticar_usuario, actualizar_rol_usuario


@pytest.fixture(scope="module")
def setup_dependencies():
    # Configurar OpenAI
    configure_openai()

    # Configurar cliente de MongoDB y adaptador
    mongo_client = get_mongo_client()
    mongo_adapter = MongoDBAdapter(mongo_client)

    # Inicializar OpenAIConsultas
    openai_consultas = OpenAIConsultas()

    return {
        "mongo_adapter": mongo_adapter,
        "openai_consultas": openai_consultas
    }


def test_responder_consulta(setup_dependencies):
    # Caso de prueba para responder una consulta usando OpenAI
    consulta = "¿Cuál es la capital de Francia?"
    contexto = "Información geográfica"
    respuesta = setup_dependencies["openai_consultas"].responder_consulta(consulta, contexto)

    assert isinstance(respuesta, str)  # Verifica que la respuesta sea un string
    assert "París" in respuesta  # Ajusta según la posible respuesta esperada


def test_guardar_y_cargar_historial():
    # Caso de prueba para guardar y cargar historial de chat
    historial = [{"user": "Hola", "bot": "Hola, ¿en qué puedo ayudarte?"}]

    # Guardar historial
    guardar_historial(historial)

    # Cargar historial y verificar
    historial_cargado = cargar_historial()
    assert historial_cargado == historial

    # Limpiar archivo después de la prueba
    if os.path.exists("../chat_history.json"):
        os.remove("../chat_history.json")


def test_dividir_texto_en_chunks():
    # Caso de prueba para dividir texto en fragmentos
    texto = "Este es un texto muy largo que debe ser dividido en varios chunks o fragmentos para su procesamiento."
    chunks = dividir_texto_en_chunks(texto, tamano_chunk=10, solapamiento=2)

    assert len(chunks) > 1  # Verificar que haya más de un chunk
    assert all(len(chunk) <= 10 for chunk in chunks)  # Verificar que el tamaño de cada chunk no exceda el límite


def test_registrar_y_autenticar_usuario(setup_dependencies):
    # Caso de prueba para registrar y autenticar usuario
    username = "testuser"
    password = "securepassword"
    role = "Usuario"

    # Registrar usuario
    registro = registrar_usuario(username, password, role)
    assert registro is not None  # Verificar que el registro fue exitoso

    # Autenticar usuario
    autenticacion = autenticar_usuario(username, password)
    assert autenticacion is not None  # Verificar que la autenticación fue exitosa

    # Eliminar el usuario de la base de datos de prueba
    setup_dependencies["mongo_adapter"].eliminar_usuario(username)


def test_actualizar_rol_usuario(setup_dependencies):
    # Caso de prueba para actualizar el rol de un usuario
    username = "testuser"
    password = "securepassword"
    nuevo_rol = "Admin"

    # Registrar usuario para la prueba
    registrar_usuario(username, password)

    # Actualizar rol del usuario
    actualizacion = actualizar_rol_usuario(username, nuevo_rol)
    assert actualizacion is True  # Verificar que la actualización fue exitosa

    # Verificar que el rol se actualizó en la base de datos
    usuario = setup_dependencies["mongo_adapter"].obtener_usuario(username)
    assert usuario["role"] == nuevo_rol  # Asegura que el rol sea "Admin"

    # Eliminar el usuario de la base de datos de prueba
    setup_dependencies["mongo_adapter"].eliminar_usuario(username)
