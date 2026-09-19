import os
import random
import string
from locust import HttpUser, task, between, events

# Helper pour générer des chaînes aléatoires
def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class BaseTestUser(HttpUser):
    abstract = True
    token = None
    user_id = None

    # Temps d'attente réaliste pour ne pas saturer le CPU local
    wait_time = between(5, 10)

    def on_start(self):
        self.login()
        self.fetch_initial_data()

    def login(self):
        email = getattr(self, "default_email", "user@example.com")
        password = getattr(self, "default_password", "password")

        response = self.client.post("/api/v1/auth/login", data={
            "username": email,
            "password": password
        }, name="/auth/login")

        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
            try:
                me = self.client.get("/api/v1/users/me", name="/users/me").json()
                self.user_id = me.get("id")
            except: pass
        else:
            print(f"Login failed for {email}")

    def fetch_initial_data(self):
        """Placeholder pour éviter les AttributeError"""
        pass

class FreelanceUser(BaseTestUser):
    default_email = os.getenv("LOCUST_FREELANCE_EMAIL", "freelancer1@freelance.example.com")
    default_password = os.getenv("LOCUST_FREELANCE_PASSWORD", "freelancer1pass")

    project_ids = []
    proposal_project_ids = []

    def fetch_initial_data(self):
        if self.token:
            # Projets ouverts pour pouvoir postuler
            res = self.client.get("/api/v1/freelance/projects", name="/freelance/projects")
            if res.status_code == 200:
                self.project_ids = [p['id'] for p in res.json()]

            # Projets où on a déjà postulé pour pouvoir chatter (évite le 403)
            res_p = self.client.get("/api/v1/freelance/proposals", name="/freelance/proposals")
            if res_p.status_code == 200:
                self.proposal_project_ids = [p['project_id'] for p in res_p.json()]

    @task(10)
    def dashboard(self):
        self.client.get("/api/v1/freelance/projects", name="/freelance/projects")
        self.client.get("/api/v1/freelance/stats", name="/freelance/stats")

    @task(5)
    def chat(self):
        # Utilise les projets où on a une proposal pour éviter le 403 Forbidden
        pids = self.proposal_project_ids if self.proposal_project_ids else self.project_ids
        if pids:
            pid = random.choice(pids)
            with self.client.get(f"/api/v1/projects/{pid}/messages", name="/projects/{id}/messages", catch_response=True) as response:
                if response.status_code == 403:
                    response.success() # On accepte le 403 car c'est une règle métier

            self.client.post(f"/api/v1/projects/{pid}/messages",
                             json={"content": "Update automatique."},
                             name="/projects/{id}/messages [POST]")

    @task(2)
    def update_profile(self):
        self.client.put("/api/v1/users/me/profile", json={
            "bio": f"Freelance expert {random_string(5)}",
            "skills": "FastAPI, Docker, PostgreSQL"
        }, name="/users/me/profile")

class ClientUser(BaseTestUser):
    default_email = os.getenv("LOCUST_CLIENT_EMAIL", "client1@freelance.example.com")
    default_password = os.getenv("LOCUST_CLIENT_PASSWORD", "client1pass")

    my_project_ids = []

    def fetch_initial_data(self):
        if self.token:
            res = self.client.get("/api/v1/client/projects", name="/client/projects")
            if res.status_code == 200:
                self.my_project_ids = [p['id'] for p in res.json()]

    @task(10)
    def monitor_projects(self):
        self.client.get("/api/v1/client/projects", name="/client/projects")
        self.client.get("/api/v1/client/stats", name="/client/stats")

    @task(2)
    def post_project(self):
        res = self.client.post("/api/v1/client/projects", json={
            "title": f"Besoin Urgent {random_string(5)}",
            "description": "Test de charge massif.",
            "country_id": 1,
            "city_id": 1,
            "district_id": 1,
            "budget": random.randint(100, 2000),
            "scheduled_at": "2026-11-20T10:00:00",
            "category_id": 1
        }, name="/client/projects [POST]")
        if res.status_code == 200:
            self.my_project_ids.append(res.json().get("id"))

class AdminUser(BaseTestUser):
    default_email = os.getenv("LOCUST_ADMIN_EMAIL", "admin1@freelance.example.com")
    default_password = os.getenv("LOCUST_ADMIN_PASSWORD", "admin1pass")

    @task(10)
    def overview(self):
        self.client.get("/api/v1/admin/overview", name="/admin/overview")
        self.client.get("/api/v1/admin/users", params={"limit": 50}, name="/admin/users")

class PublicUser(HttpUser):
    wait_time = between(2, 5)
    @task(10)
    def browse(self):
        self.client.get("/api/v1/locations/countries", name="/locations/countries")
