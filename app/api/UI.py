from datetime import datetime

import streamlit as st

from app.usecases import *

from app.adapters.mongodb_adapter import MongoDBAdapter
from app.adapters.chromadb_adapter import ChromaDBAdapter
from app.api.dependencies import *
from app.core.ports import *

# Configurar la API de OpenAI
configure_openai()

# Inicializar clientes de base de datos
mongo_client = get_mongo_client()
chroma_client = get_chroma_client()


# Crear instancias de los adaptadores
mongo_adapter = MongoDBAdapter(mongo_client)
chroma_adapter = ChromaDBAdapter(chroma_client)

# Crear la interfaz gráfica con Streamlit
st.title("Sistema de Gestión de Respuestas (RAG)")

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
            mensaje_registro = mongo_adapter.registrar_usuario(nuevo_usuario, nueva_contraseña)
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
            role, mensaje_login = mongo_adapter.autenticar_usuario(usuario, contraseña)
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
            chroma_adapter.almacenar_chunks(idDocumento, chunks)

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
                res = mongo_adapter.rol_admin(usuario, nuevo_rol)
                if "actualizado" in res:
                    st.success(res)
                else:
                    st.error(res)






