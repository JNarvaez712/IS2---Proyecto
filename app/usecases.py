from abc import ABC, abstractmethod

class FileProcessor(ABC):
    @abstractmethod
    def extract_text(self, file) -> str:
        pass

    @abstractmethod
    def get_file_type(self) -> str:
        pass


class PDFProcessor(FileProcessor):
    def extract_text(self, file) -> str:
        # Lógica para extraer texto de un PDF
        return "Texto de PDF"

    def get_file_type(self) -> str:
        return "PDF"


class TXTProcessor(FileProcessor):
    def extract_text(self, file) -> str:
        return file.read().decode("utf-8")

    def get_file_type(self) -> str:
        return "TXT"


class DOCXProcessor(FileProcessor):
    def extract_text(self, file) -> str:
        # Lógica para extraer texto de un DOCX
        return "Texto de DOCX"

    def get_file_type(self) -> str:
        return "DOCX"