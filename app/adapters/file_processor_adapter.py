from app.core.ports import PDFProcessor, TXTProcessor, DOCXProcessor

class FileProcessorFactory:
    @staticmethod
    def get_processor(file_type: str):
        if file_type == "application/pdf":
            return PDFProcessor()
        elif file_type == "text/plain":
            return TXTProcessor()
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return DOCXProcessor()
        else:
            raise ValueError("Unsupported file type")