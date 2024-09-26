

class Documento:
    def __init__(self, chunk_id, idDocumento, texto, metadatos, fecha_subida, tipo_documento):
        self.chunk_id = chunk_id
        self.idDocumento = idDocumento
        self.texto = texto
        self.fecha_subida = fecha_subida
        self.metadatos = metadatos
        self.tipo_documento = tipo_documento

class Metadato:
    def __init__(self, titulo, fecha_creacion, tipo_documento):
        self.titulo = titulo
        self.fecha_creacion = fecha_creacion
        self.tipo_documento = tipo_documento