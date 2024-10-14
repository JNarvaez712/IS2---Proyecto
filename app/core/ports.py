from abc import ABC, abstractmethod
import docx
from PyPDF2 import PdfReader

class AlmacenamientoChunks(ABC):
    @abstractmethod
    def almacenar_chunks(self, id_documento, chunks, metadatos):
        pass

class GestionUsuarios(ABC):
    @abstractmethod
    def registrar_usuario(self, username, password, role="Usuario"):
        pass

    @abstractmethod
    def autenticar_usuario(self, username, password):
        pass

    @abstractmethod
    def actualizar_rol_usuario(self, username, nuevo_rol):
        pass

class ProcesadorConsultas(ABC):
    @abstractmethod
    def responder_consulta(self, consulta, contexto):
        pass

class FileProcessor(ABC):
    @abstractmethod
    def extract_text(self, file) -> str:
        pass

    @abstractmethod
    def get_file_type(self) -> str:
        pass

class PDFProcessor(FileProcessor):
    def extract_text(self, file) -> str:
        reader = PdfReader(file)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text()
        return texto

    def get_file_type(self) -> str:
        return "PDF"

class TXTProcessor(FileProcessor):
    def extract_text(self, file) -> str:
        return file.read().decode("utf-8")

    def get_file_type(self) -> str:
        return "TXT"

class DOCXProcessor(FileProcessor):
    def extract_text(self, file) -> str:
        doc = docx.Document(file)
        texto = ""
        for para in doc.paragraphs:
            texto += para.text + "\n"
        return texto

    def get_file_type(self) -> str:
        return "DOCX"
