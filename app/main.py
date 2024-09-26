import openai
import os
import streamlit as st
import json
from PyPDF2 import PdfReader
import docx
import chromadb
from chromadb.config import Settings
from pymongo import MongoClient
from datetime import datetime
import bcrypt

# Configurar MongoDB
mongoClient = MongoClient(os.getenv("MONGO_URI"))
db = mongoClient["RAGSystem"]
coleccionDocumentos = db["Documento"]
coleccionUsuarios = db["Usuario"]

# Configurar la API de OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configurar ChromaDB
chroma_client = chromadb.Client(Settings(persist_directory="./chroma_db"))

# Función para almacenar los chunks en MongoDB
def almacenar_chunks(idDocumento, chunks, metadatos):
    for i, chunk in enumerate(chunks):
        documento = {
            "chunk_id": i,
            "idDocumento": idDocumento,
            "texto": chunk,
            "metadata": metadatos,
            "fecha_subida": datetime.utcnow(),
            "tipo_documento": metadatos.get("tipo_documento", "desconocido"),
        }
        coleccionDocumentos.insert_one(documento)

# Función para almacenar los chunks en ChromaDB
def almacenar_chunks_en_chromadb(chunks):
    collection = chroma_client.get_or_create_collection("document_chunks")
    for i, chunk in enumerate(chunks):
        collection.add(
            ids=[f"chunk_{i}"],
            documents=[chunk],
            metadatas=[{"chunk_id": i}]
        )

# Función para responder a cualquier consulta usando OpenAI
def responder_consulta(consulta, contexto=""):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente útil."},
            {"role": "user", "content": f"{contexto}\n\n{consulta}"}
        ],
        max_tokens=1000
    )
    respuesta = response['choices'][0]['message']['content'].strip()
    return respuesta.replace('. ', '.\n')

# Función para extraer texto de un archivo PDF
def extraer_texto_pdf(file):
    reader = PdfReader(file)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text()
    return texto

# Función para extraer texto de un archivo DOCX
def extraer_texto_docx(file):
    doc = docx.Document(file)
    texto = ""
    for para in doc.paragraphs:
        texto += para.text + "\n"
    return texto

# Función para dividir el texto en fragmentos (chunks)
def dividir_texto_en_chunks(texto, tamano_chunk=500, solapamiento=50):
    chunks = []
    for i in range(0, len(texto), tamano_chunk - solapamiento):
        chunks.append(texto[i:i + tamano_chunk])
    return chunks

# Función para guardar el historial de chat en un archivo JSON
def guardar_historial(historial):
    with open("../chat_history.json", "w") as file:
        json.dump(historial, file)

# Función para cargar el historial de chat desde un archivo JSON
def cargar_historial():
    if os.path.exists("../chat_history.json"):
        with open("../chat_history.json", "r") as file:
            return json.load(file)
    return []

# Función para registrar un nuevo usuario en la base de datos
def registrar_usuario(username, password, role="Usuario"):
    # Verificar si el usuario ya existe
    if coleccionUsuarios.find_one({"username": username}):
        return "El usuario ya existe"

    # Hashear la contraseña
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Insertar el nuevo usuario en la colección
    coleccionUsuarios.insert_one({"username": username, "password": hashed_password, "role": role})
    return "Usuario registrado exitosamente"

# Función para autenticar un usuario en la base de datos
def autenticar_usuario(username, password):
    # Buscar el usuario en la colección
    usuario = coleccionUsuarios.find_one({"username": username})
    if not usuario:
        return None, "Usuario no encontrado"

    # Verificar la contraseña
    if bcrypt.checkpw(password.encode('utf-8'), usuario["password"]):
        role = usuario.get("role", "Usuario")  # Asignar rol predeterminado si no tiene uno
        return role, "Autenticación exitosa"
    else:
        return None, "Contraseña incorrecta"

# Inicializar el estado de la sesión
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'show_register' not in st.session_state:
    st.session_state.show_register = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'show_assign_roles' not in st.session_state:
    st.session_state.show_assign_roles = False

# Mostrar el formulario de inicio de sesión si el usuario no está autenticado
if not st.session_state.authenticated:
    if st.session_state.show_register:
        with st.form(key='registro_form'):
            st.subheader("Registro de usuario")
            nuevo_usuario = st.text_input("Nombre de usuario")
            nueva_contraseña = st.text_input("Contraseña", type="password")
            col1, col2 = st.columns([1, 1])
            with col1:
                boton_registro = st.form_submit_button(label='Registrar')
            with col2:
                boton_regresar = st.form_submit_button(label='Regresar')

        if boton_registro:
            mensaje_registro = registrar_usuario(nuevo_usuario, nueva_contraseña)
            st.success(mensaje_registro)
            st.session_state.show_register = False

        if boton_regresar:
            st.session_state.show_register = False
    else:
        with st.form(key='login_form'):
            st.subheader("Iniciar sesión")
            usuario = st.text_input("Nombre de usuario")
            contraseña = st.text_input("Contraseña", type="password")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                boton_login = st.form_submit_button(label='Iniciar sesión')
            with col2:
                boton_registro = st.form_submit_button(label='Registrarse')
            with col3:
                role = st.selectbox("Seleccione su rol", ["Cliente", "Administrador"])

        if boton_login:
            role, mensaje_login = autenticar_usuario(usuario, contraseña)
            if role:
                st.session_state.authenticated = True
                st.session_state.role = role
                st.success(mensaje_login)
            else:
                st.error(mensaje_login)

        if boton_registro:
            st.session_state.show_register = True
else:
    if 'role' in st.session_state and st.session_state.role == "Usuario":
        # Crear la interfaz gráfica con Streamlit para el usuario
        st.title("Sistema de Gestión de Respuestas (RAG)")

        # Botón para regresar al formulario de inicio de sesión
        st.markdown(
            """
            <style>
            .button-container {
                display: flex;
                justify-content: flex-end;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        if st.button("Cerrar sesión"):
            st.session_state.authenticated = False
            st.session_state.role = None
        st.markdown('</div>', unsafe_allow_html=True)

        # Inicializar el historial de chat y los chats anteriores
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'previous_chats' not in st.session_state:
            st.session_state.previous_chats = cargar_historial()

        # Botón para iniciar un nuevo chat
        if st.sidebar.button("Nuevo Chat"):
            if st.session_state.chat_history:
                st.session_state.previous_chats.append(st.session_state.chat_history)
                guardar_historial(st.session_state.previous_chats)
            st.session_state.chat_history = []

        # Mostrar los chats anteriores en la barra lateral
        st.sidebar.subheader("Chats Anteriores")
        for i, chat in enumerate(st.session_state.previous_chats):
            with st.sidebar.expander(f"Chat {i + 1}"):
                for message in chat:
                    st.write(message['content'])
                if st.button(f"Cargar Chat {i + 1}", key=f"load_{i}"):
                    st.session_state.chat_history = chat
                if st.button(f"Eliminar Chat {i + 1}", key=f"delete_{i}"):
                    st.session_state.previous_chats.pop(i)
                    guardar_historial(st.session_state.previous_chats)

        # Formulario para la consulta y subida de documentos
        with st.form(key='consulta_form'):
            consulta = st.text_input("Ingrese su consulta:")
            uploaded_file = st.file_uploader("Sube un documento (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"],
                                             label_visibility="collapsed")
            submit_button = st.form_submit_button(label='Enviar')

        contexto = ""
        texto_documento = ""
        tipo_documento = ""
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                texto_documento = extraer_texto_pdf(uploaded_file)
                tipo_documento = "PDF"
            elif uploaded_file.type == "text/plain":
                texto_documento = uploaded_file.read().decode("utf-8")
                tipo_documento = "TXT"
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                texto_documento = extraer_texto_docx(uploaded_file)
                tipo_documento = "DOCX"

            # Crear metadatos del documento
            metadatos = {
                "titulo": uploaded_file.name,
                "fecha_creacion": datetime.utcnow(),
                "tipo_documento": tipo_documento
            }

            # Generar un ID único para el documento
            idDocumento = f"doc_{int(datetime.utcnow().timestamp())}"

            # Dividir el texto en chunks
            chunks = dividir_texto_en_chunks(texto_documento)

            # Almacenar chunks en ChromaDB
            almacenar_chunks_en_chromadb(chunks)

            # Almacenar chunks y metadatos en MongoDB
            almacenar_chunks(idDocumento, chunks, metadatos)

            # Agregar el contexto al historial de chat
            contexto = f"Texto del documento cargado: {uploaded_file.name}"
            st.session_state.chat_history.append({"role": "system", "content": contexto})

        if submit_button:
            respuesta = responder_consulta(consulta, texto_documento)
            st.session_state.chat_history.append({"role": "assistant", "content": respuesta})

        # Mostrar el historial de chat en orden inverso
        st.subheader("Historial de Chat")
        # Mostrar solo las respuestas en orden inverso
        for message in reversed(st.session_state.chat_history):
            if message["role"] == "assistant":
                st.write(message['content'])
                st.markdown("<hr>", unsafe_allow_html=True)

        # Guardar el historial actual al archivo JSON
        guardar_historial(st.session_state.previous_chats)

    elif 'role' in st.session_state and st.session_state.role == "Administrador":
        # Crear la interfaz gráfica con Streamlit para el administrador
        st.title("Sistema de Gestión de Respuestas (RAG) - Administrador")

        # Botón para regresar al formulario de inicio de sesión
        st.markdown(
            """
            <style>
            .button-container {
                display: flex;
                justify-content: flex-end;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        if st.button("Cerrar sesión"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.show_assign_roles = False
        st.markdown('</div>', unsafe_allow_html=True)

        # Botón para acceder al formulario de asignar roles
        if st.button("Asignar Roles"):
            st.session_state.show_assign_roles = True

        # Mostrar el formulario de asignar roles si el administrador lo solicita
        if st.session_state.show_assign_roles:
            with st.form(key='asignar_roles_form'):
                usuario = st.text_input("Nombre de usuario")
                nuevo_rol = st.selectbox("Nuevo Rol", ["Usuario", "Administrador"])
                boton_asignar = st.form_submit_button(label='Asignar Rol')

            if boton_asignar:
                # Verificar si el usuario existe
                usuario_encontrado = coleccionUsuarios.find_one({"username": usuario})
                if usuario_encontrado:
                    # Actualizar el rol del usuario
                    coleccionUsuarios.update_one({"username": usuario}, {"$set": {"role": nuevo_rol}})
                    st.success(f"Rol de {usuario} actualizado a {nuevo_rol}")
                else:
                    st.error("Usuario no encontrado")


