import pytest
import json
from app.usecases import *


def test_responder_consulta_when_calling_responder_consulta(mocker):
    # Arrange
    mock_openai_create = mocker.patch("app.adapters.openAI_adapter.openai.ChatCompletion.create")
    mock_openai_create.return_value = {
        "choices": [{"message": {"content": "Respuesta de prueba"}}]
    }
    consulta = "¿Qué es RAG?"
    contexto = "El contexto es informática"

    # Act
    respuesta = responder_consulta(consulta, contexto)

    # Assert
    assert respuesta == "Respuesta de prueba"
    mock_openai_create.assert_called_once()


def test_guardar_historial_when_calling_guardar_historial(mocker):
    # Arrange
    mock_open = mocker.mock_open()
    mocker.patch("builtins.open", mock_open)
    mock_json_dump = mocker.spy(json, "dump")
    historial = [{"user": "Pregunta 1"}]

    # Act
    guardar_historial(historial)

    # Assert
    mock_open.assert_called_once_with("../chat_history.json", "w")
    mock_json_dump.assert_called_once_with(historial, mock_open())


def test_cargar_historial_when_calling_cargar_historial_if_document_exists(mocker):
    # Arrange
    mock_open = mocker.mock_open(read_data='[{"user": "Pregunta 1"}]')
    mocker.patch("builtins.open", mock_open)
    mock_exists = mocker.patch("os.path.exists", return_value=True)

    # Act
    resultado = cargar_historial()

    # Assert
    mock_exists.assert_called_once_with("../chat_history.json")
    mock_open.assert_called_once_with("../chat_history.json", "r")
    assert resultado == [{"user": "Pregunta 1"}]


def test_cargar_historial_when_calling_cargar_historial_if_document_not_exists(mocker):
    # Arrange
    mock_exists = mocker.patch("os.path.exists", return_value=False)

    # Act
    resultado = cargar_historial()

    # Assert
    mock_exists.assert_called_once_with("../chat_history.json")
    assert resultado == []


def test_dividir_texto_en_chunks_when_calling_dividir_texto_en_chunks():
    # Arrange
    texto = "Este es un texto largo que necesita ser dividido en fragmentos para ser procesado"

    # Act
    resultado = dividir_texto_en_chunks(texto, tamano_chunk=20, solapamiento=5)
    esperado = [
        "Este es un texto lar",
        "o largo que necesita",
        "esita ser dividido e",
        "ido en fragmentos pa",
        "os para ser procesad",
        "cesado"
    ]

    # Assert
    assert resultado == esperado


def test_registrar_usuario_when_calling_registrar_usuario_with_default_role(mocker):
    # Arrange
    mock_registrar_usuario = mocker.patch('app.adapters.mongodb_adapter.MongoDBAdapter.registrar_usuario', return_value=True)
    username = "testuser"
    password = "password"
    role = "Usuario"

    # Act
    resultado = registrar_usuario(username, password)

    # Assert
    mock_registrar_usuario.assert_called_once_with(username, password, role)
    assert resultado is True


def test_registrar_usuario_when_calling_registrar_usuario_with_admin_role(mocker):
    # Arrange
    mock_registrar_usuario = mocker.patch('app.adapters.mongodb_adapter.MongoDBAdapter.registrar_usuario', return_value=True)
    username = "testadminuser"
    password = "password2"
    role = "Administrador"

    # Act
    resultado = registrar_usuario(username, password, role)

    # Assert
    mock_registrar_usuario.assert_called_once_with(username, password, role)
    assert resultado is True


def test_autenticar_usuario_when_calling_autenticar_usuario_with_valid_credentials(mocker):
    # Arrange
    mock_autenticar_usuario = mocker.patch('app.adapters.mongodb_adapter.MongoDBAdapter.autenticar_usuario', return_value=("Usuario", "Autenticación exitosa"))
    username = "testuser"
    password = "password"

    # Act
    role, mensaje = autenticar_usuario(username, password)

    # Assert
    mock_autenticar_usuario.assert_called_once_with(username, password)
    assert role == "Usuario"
    assert mensaje == "Autenticación exitosa"


def test_autenticar_usuario_when_calling_autenticar_usuario_with_invalid_credentials(mocker):
    # Arrange
    mock_autenticar_usuario = mocker.patch('app.adapters.mongodb_adapter.MongoDBAdapter.autenticar_usuario', return_value=(None, "Contraseña incorrecta"))
    username = "testuser"
    password = "password"

    # Act
    role, mensaje = autenticar_usuario(username, password)

    # Assert
    mock_autenticar_usuario.assert_called_once_with(username, password)
    assert role is None
    assert mensaje == "Contraseña incorrecta"




















