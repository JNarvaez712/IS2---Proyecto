from abc import ABC, abstractmethod
import docx
from PyPDF2 import PdfReader
from typing import List, Dict, Any

# prueba workflow5


class AlmacenamientoChunks(ABC):
    @abstractmethod
    def almacenar_chunks(
        self, id_documento: str, chunks: List[str], metadatos: Dict[str, Any]
    ) -> None:
        pass


class GestionUsuarios(ABC):
    @abstractmethod
    def registrar_usuario(
        self, username: str, password: str, role: str = "Usuario"
    ) -> None:
        pass

    @abstractmethod
    def autenticar_usuario(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def actualizar_rol_usuario(self, username: str, nuevo_rol: str) -> bool:
        pass


class ProcesadorConsultas(ABC):
    @abstractmethod
    def responder_consulta(self, consulta: str, contexto: List[str]) -> str:
        pass


class FileProcessor(ABC):
    @abstractmethod
    def extract_text(self, file: Any) -> str:
        pass

    @abstractmethod
    def get_file_type(self) -> str:
        pass


class PDFProcessor(FileProcessor):
    def extract_text(self, file: Any) -> str:
        reader = PdfReader(file)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() or ""
        return texto

    def get_file_type(self) -> str:
        return "PDF"


class TXTProcessor(FileProcessor):
    def extract_text(self, file: Any) -> str:
        content = file.read()
        return content.decode("utf-8") if content else ""

    def get_file_type(self) -> str:
        return "TXT"


class DOCXProcessor(FileProcessor):
    def extract_text(self, file: Any) -> str:
        doc = docx.Document(file)
        texto = ""
        for para in doc.paragraphs:
            texto += para.text + "\n"
        return texto

    def get_file_type(self) -> str:
        return "DOCX"
