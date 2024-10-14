from datetime import datetime
import streamlit as st
from app.usecases import *
from app.adapters.mongodb_adapter import MongoDBAdapter
from app.adapters.chromadb_adapter import ChromaDBAdapter
from app.api.dependencies import get_mongo_client, get_chroma_client, configure_openai
from app.core.ports import *

# Configurar la API de OpenAI
configure_openai()

# Inicializar el estado de la sesión
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'show_register' not in st.session_state:
    st.session_state.show_register = False
if 'role' not in st.session_state:
    st.session_state.role = None

def mostrar_login():
    st.title("Inicio de Sesión")

    if st.session_state.show_register:
        # Formulario de registro
        with st.form(key='registro_form'):
            st.subheader("Registro de usuario")
            nuevo_usuario = st.text_input("Nombre de usuario")
            nueva_contraseña = st.text_input("Contraseña", type="password")

            # Organizando botones y el selectbox de rol en la misma fila
            col1, col2, col3 = st.columns([1, 1, 2])  # Se crean tres columnas, la última más grande para el selectbox
            with col1:
                boton_registro = st.form_submit_button(label='Registrar')
            with col2:
                boton_regresar = st.form_submit_button(label='Regresar')
            with col3:
                # Selección de roles a la derecha
                role = st.selectbox('Selecciona tu rol', ['Usuario', 'Administrador'])

        if boton_registro:
            mensaje_registro = registrar_usuario(nuevo_usuario, nueva_contraseña)
            st.success(mensaje_registro)
            st.session_state.show_register = False

        if boton_regresar:
            st.session_state.show_register = False
    else:
        # Formulario de inicio de sesión
        with st.form(key='login_form'):
            st.subheader("Iniciar sesión")
            usuario = st.text_input("Nombre de usuario")
            contraseña = st.text_input("Contraseña", type="password")

            col1, col2, col3 = st.columns([1, 1, 2])  # Tres columnas, para organizar los botones y selectbox
            with col1:
                boton_login = st.form_submit_button(label='Iniciar sesión')
            with col2:
                boton_registro = st.form_submit_button(label='Registrarse')
            with col3:
                # Selección de roles a la derecha
                role = st.selectbox('Selecciona tu rol', ['Usuario', 'Administrador'])

        if boton_login:
            # Intentar autenticar al usuario
            role, mensaje_login = autenticar_usuario(usuario, contraseña)
            if role:
                st.session_state.authenticated = True  # Cambiar el estado a autenticado
                st.session_state.role = role  # Guardar el rol del usuario
                st.success(mensaje_login)
            else:
                st.error(mensaje_login)

        if boton_registro:
            # Redirigir al formulario de registro
            st.session_state.show_register = True

def mostrar_chat():
    # Interfaz gráfica principal del usuario autenticado
    st.title(f"Bienvenido al Chat, {st.session_state.role}")

    # Botón para cerrar sesión
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

    # Función para mapear procesadores según el tipo de archivo
    def obtener_procesador(uploaded_file):
        mime_type = uploaded_file.type
        procesadores = {
            "application/pdf": PDFProcessor(),
            "text/plain": TXTProcessor(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DOCXProcessor()
        }
        return procesadores.get(mime_type, None)

    # Formulario para la consulta y subida de documentos
    with st.form(key='consulta_form'):
        consulta = st.text_input("Ingrese su consulta:")
        uploaded_file = st.file_uploader("Sube un documento (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"],
                                         label_visibility="collapsed")
        submit_button = st.form_submit_button(label='Enviar')

    contexto = ""
    texto_documento = ""
    tipo_documento = ""

    # Inicializar clientes de base de datos
    mongo_client = get_mongo_client()  # Consistencia con mongodb_adapter.py
    chroma_client = get_chroma_client()

    # Crear instancias de los adaptadores
    mongo_adapter = MongoDBAdapter(mongo_client)  # Consistencia con mongodb_adapter.py
    chroma_adapter = ChromaDBAdapter(chroma_client)

    if uploaded_file:
        procesador = obtener_procesador(uploaded_file)

        if procesador:
            # Extraer el texto y el tipo de archivo
            texto_documento = procesador.extract_text(uploaded_file)
            tipo_documento = procesador.get_file_type()

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
        chroma_adapter.almacenar_chunks(idDocumento, chunks, metadatos)

        # Almacenar chunks y metadatos en MongoDB
        mongo_adapter.almacenar_chunks(idDocumento, chunks, metadatos)

        # Agregar el contexto al historial de chat
        contexto = f"Texto del documento cargado: {uploaded_file.name}"
        st.session_state.chat_history.append({"role": "system", "content": contexto})

    if submit_button:
        respuesta = responder_consulta(consulta, texto_documento)
        st.session_state.chat_history.append({"role": "assistant", "content": respuesta})

    # Mostrar el historial de chat en orden inverso
    st.subheader("Historial de Chat")
    for message in reversed(st.session_state.chat_history):
        if message["role"] == "assistant":
            st.write(message['content'])
            st.markdown("<hr>", unsafe_allow_html=True)

    # Guardar el historial actual al archivo JSON
    guardar_historial(st.session_state.previous_chats)

# Mostrar el login o el chat en función del estado de autenticación
if st.session_state.authenticated:
    mostrar_chat()
else:
    mostrar_login()





