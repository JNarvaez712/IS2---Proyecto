from locust import HttpUser, TaskSet, task, between

class ConversationBehavior(TaskSet):
    @task
    def initiate_conversation(self):
        # Realiza una petición de inicio de conversación
        self.client.post("/start", json={"user_id": "test_user"})

    @task
    def send_message(self):
        # Simula el envío de un mensaje al modelo
        self.client.post("/message", json={"user_id": "test_user", "message": "Hello, how are you?"})

class LoadTestUser(HttpUser):
    tasks = [ConversationBehavior]
    wait_time = between(1, 5)  # Simula un tiempo de espera entre tareas para cada usuario simulado