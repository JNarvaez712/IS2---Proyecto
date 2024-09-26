from abc import ABC, abstractmethod

class AlmacenamientoChunks(ABC):
    @abstractmethod
    def almacenar_chunks(self, id_documento, chunks, metadatos):
        pass

class ProcesadorConsultas(ABC):
    @abstractmethod
    def responder_consulta(self, consulta, contexto):
        pass