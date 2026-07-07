import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_statistics():
    response = client.get("/api/v1/statistics/")
    assert response.status_code == 200
    data = response.json()
    
    assert "numerical" in data
    assert "percentages" in data
    
    # Assert data types and structure
    assert isinstance(data["numerical"]["total_tasks"], int)
    assert isinstance(data["numerical"]["total_users"], int)
    assert isinstance(data["percentages"]["site_activity"], float)
    assert "freelancers" in data["percentages"]["registration"]
