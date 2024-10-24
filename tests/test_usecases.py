import unittest
from unittest.mock import patch, mock_open
from app.usecases import *


class TestUsecases(unittest.TestCase):

    @patch("app.adapters.openAI_adapter.openai.ChatCompletion.create")
    def test_responder_consulta_when_calling_responder_consulta(self, mock_openai_create):
        #Arrange (configurar las cosas)
        mock_openai_create.return_value = {
            "choices": [{"message": {"content": "Respuesta de prueba"}}]
        }
        consulta = "¿Qué es RAG?"
        contexto = "El contexto es informática"

        #Act (ejecutar la función)
        respuesta = responder_consulta(consulta, contexto)

        #Assert (verificar el resultado)
        self.assertEqual(respuesta, "Respuesta de prueba")
        mock_openai_create.assert_called_once()



    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_guardar_historial_when_calling_guardar_historial(self, mock_json_dump, mock_open):
        #Arrange
        historial = [{"user": "Pregunta 1"}]

        #Act
        guardar_historial(historial)

        #Assert
        mock_open.assert_called_once_with("../chat_history.json", "w")
        mock_json_dump.assert_called_once_with(historial, mock_open())



    @patch("builtins.open", new_callable=mock_open, read_data='[{"user": "Pregunta 1"}]')
    @patch("os.path.exists", return_value=True) #Para simular que existe el archivo
    def test_cargar_historial_when_calling_cargar_historial_if_document_exists(self, mock_exists, mock_open):
        #Act
        resultado = cargar_historial()

        #Assert
        mock_exists.assert_called_once_with("../chat_history.json")
        mock_open.assert_called_once_with("../chat_history.json", "r")
        self.assertEqual(resultado, [{"user": "Pregunta 1"}])

    @patch("os.path.exists", return_value=False)
    def test_cargar_historial_when_calling_cargar_historial_if_document_not_exists(self, mock_exists):
        #Act
        resultado = cargar_historial()

        #Assert
        mock_exists.assert_called_once_with("../chat_history.json")
        self.assertEqual(resultado, [])



    def test_dividir_texto_en_chunks_when_calling_dividir_texto_en_chunks(self):
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
        self.assertEqual(resultado, esperado)



    @patch('app.adapters.mongodb_adapter.MongoDBAdapter.registrar_usuario')
    def test_registrar_usuario_when_calling_registrar_usuario_with_default_role(self, mock_registrar_usuario):
        #Arrange
        mock_registrar_usuario.return_value = True
        username = "testuser"
        password = "password"
        role = "Usuario"

        #Act
        resultado = registrar_usuario(username, password)

        #Assert
        mock_registrar_usuario.assert_called_once_with(username, password, role)
        self.assertTrue(resultado)


    @patch('app.adapters.mongodb_adapter.MongoDBAdapter.registrar_usuario')
    def test_registrar_usuario_when_calling_registrar_usuario_with_admin_role(self, mock_registrar_usuario):
        # Arrange
        mock_registrar_usuario.return_value = True
        username = "testadminuser"
        password = "password2"
        role = "Administrador"

        # Act
        resultado = registrar_usuario(username, password, role)

        # Assert
        mock_registrar_usuario.assert_called_once_with(username, password, role)
        self.assertTrue(resultado)

    @patch('app.adapters.mongodb_adapter.MongoDBAdapter.autenticar_usuario')
    def test_autenticar_usuario_when_calling_autenticar_usuario_with_valid_credentials(self, mock_autenticar_usuario):
        #Arrange
        username = "testuser"
        password = "password"
        mock_autenticar_usuario.return_value=("Usuario", "Autenticación exitosa")

        #Act
        role, mensaje = autenticar_usuario(username, password)

        #Assert
        mock_autenticar_usuario.assert_called_once_with(username, password)
        self.assertEqual(role, "Usuario")
        self.assertEqual(mensaje, "Autenticación exitosa")

    @patch('app.adapters.mongodb_adapter.MongoDBAdapter.autenticar_usuario')
    def test_autenticar_usuario_when_calling_autenticar_usuario_with_invalid_credentials(self, mock_autenticar_usuario):
        # Arrange
        username = "testuser"
        password = "password"
        mock_autenticar_usuario.return_value = (None, "Contraseña incorrecta")

        # Act
        role, mensaje = autenticar_usuario(username, password)

        # Assert
        mock_autenticar_usuario.assert_called_once_with(username, password)
        self.assertIsNone(role)
        self.assertEqual(mensaje, "Contraseña incorrecta")


















