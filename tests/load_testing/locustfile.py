from locust import HttpUser, task, between

class DividendScreeningUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def screen_high_yield(self):
        self.client.get("/api/v1/screen?min_yield=3.0")

    @task(3)
    def screen_high_yield_with_heavy_load(self):
        self.client.get("/api/v1/screen?min_yield=3.0&years=5")