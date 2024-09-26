from fastapi import APIRouter, UploadFile
from app.adapters.file_processor_adapter import FileProcessorFactory

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile):
    processor = FileProcessorFactory.get_processor(file.content_type)
    texto_documento = processor.extract_text(file.file)
    tipo_documento = processor.get_file_type()

    return {"file_type": tipo_documento, "text": texto_documento}