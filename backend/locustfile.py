from locust import HttpUser, task, between
import random

class SentinelLoadTest(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # In a real scenario we would login and get a token here.
        # Assuming endpoints might be public for testing or we use an API Key
        self.headers = {"Authorization": "Bearer TEST_TOKEN"}

    @task(3)
    def get_incidents(self):
        self.client.get("/api/v1/incidents/", headers=self.headers)

    @task(1)
    def get_metrics(self):
        self.client.get("/api/v1/analytics/service-health", headers=self.headers)

    @task(1)
    def view_incident(self):
        # Just hitting a dummy id to test database read throughput
        self.client.get("/api/v1/incidents/INC-TEST-9999", headers=self.headers)
