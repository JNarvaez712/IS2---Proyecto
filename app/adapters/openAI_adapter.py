from app.core.ports import ProcesadorConsultas
import openai

class OpenAIConsultas(ProcesadorConsultas):
    def responder_consulta(self, consulta, contexto):
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