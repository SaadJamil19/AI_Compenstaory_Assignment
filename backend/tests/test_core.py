import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///./test_crm.db"
os.environ["GEMINI_API_KEY"] = ""
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from database import Base, engine, init_db  # noqa: E402
from main import app  # noqa: E402


def setup_module():
    Base.metadata.drop_all(bind=engine)
    init_db()


client = TestClient(app)


def login(email="admin@test.com", password="admin123"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_login_returns_jwt():
    headers = login()
    assert headers["Authorization"].startswith("Bearer ")


def test_customer_crud_works():
    headers = login()
    create = client.post(
        "/api/customers",
        json={"full_name": "Test Customer", "email": "test.customer@example.com", "phone": "123", "company": "TestCo"},
        headers=headers,
    )
    assert create.status_code == 201
    customer_id = create.json()["id"]
    update = client.put(f"/api/customers/{customer_id}", json={"company": "UpdatedCo"}, headers=headers)
    assert update.status_code == 200
    assert update.json()["company"] == "UpdatedCo"
    delete = client.delete(f"/api/customers/{customer_id}", headers=headers)
    assert delete.status_code == 204


def test_ticket_creation_stores_ai_fallback_fields():
    headers = login()
    customer = client.get("/api/customers", headers=headers).json()[0]
    res = client.post(
        "/api/tickets",
        json={"title": "Need help", "description": "Please help with my account", "customer_id": customer["id"], "priority": "medium"},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["category"] in {"billing", "technical", "account", "shipping", "general"}
    assert data["sentiment"] in {"positive", "neutral", "negative", "frustrated"}
    assert any(a["action_type"] == "created" for a in data["activities"])


def test_dashboard_stats_works():
    headers = login()
    res = client.get("/api/dashboard/stats", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_tickets" in data
    assert "tickets_by_status" in data
