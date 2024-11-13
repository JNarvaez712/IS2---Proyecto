from locust import HttpUser, task, between

class SimpleLoadTest(HttpUser):
    wait_time = between(1, 5)

    @task
    def test_main_endpoint(self):
        self.client.get("/")  # Ruta principal de tu aplicación

