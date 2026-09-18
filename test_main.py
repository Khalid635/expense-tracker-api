import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
from decimal import Decimal

from main import app, get_db
from models import Base, User, Transaction
from auth import hash_password

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_user_registration_success():
    """Test successful user registration"""
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    assert response.json()["message"] == "User registered successfully"
    assert "user_id" in response.json()


def test_user_registration_duplicate_username():
    """Test registration with duplicate username"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test1@example.com",
        "password": "password123"
    })
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test2@example.com",
        "password": "password123"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_user_registration_duplicate_email():
    """Test registration with duplicate email"""
    client.post("/auth/register", json={
        "username": "user1",
        "email": "test@example.com",
        "password": "password123"
    })
    response = client.post("/auth/register", json={
        "username": "user2",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 400

def test_user_login_success():
    """Test successful login"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_user_login_invalid_password():
    """Test login with wrong password"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_create_transaction_success():
    """Test successful transaction creation"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]

    response = client.post(
        "/transactions",
        json={
            "title": "Salary",
            "amount": 5000.50,
            "type": "income",
            "category": "Salary",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Salary"
    assert response.json()["type"] == "income"
    assert response.json()["owner_id"] == 1


def test_create_transaction_invalid_amount():
    """Test transaction creation with negative amount"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]

    response = client.post(
        "/transactions",
        json={
            "title": "Invalid",
            "amount": -100,
            "type": "expense",
            "category": "Food",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


def test_create_transaction_invalid_type():
    """Test transaction creation with invalid type"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]

    response = client.post(
        "/transactions",
        json={
            "title": "Invalid",
            "amount": 100,
            "type": "invalid",
            "category": "Food",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

def test_get_all_transactions():
    """Test getting all transactions for a user"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]


    client.post(
        "/transactions",
        json={
            "title": "Income",
            "amount": 5000,
            "type": "income",
            "category": "Salary",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        "/transactions",
        json={
            "title": "Expense",
            "amount": 500,
            "type": "expense",
            "category": "Food",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    response = client.get("/transactions", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_specific_transaction():
    """Test getting a specific transaction by ID"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]

    create_response = client.post(
        "/transactions",
        json={
            "title": "Test",
            "amount": 100,
            "type": "expense",
            "category": "Food",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    transaction_id = create_response.json()["id"]

    response = client.get(
        f"/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == transaction_id


def test_get_transaction_unauthorized():
    """Test accessing another user's transaction"""
    client.post("/auth/register", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    login1 = client.post("/auth/login", json={
        "username": "user1",
        "password": "password123"
    })
    token1 = login1.json()["access_token"]

    client.post("/auth/register", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })
    login2 = client.post("/auth/login", json={
        "username": "user2",
        "password": "password123"
    })
    token2 = login2.json()["access_token"]

    create_response = client.post(
        "/transactions",
        json={
            "title": "User1 Transaction",
            "amount": 100,
            "type": "expense",
            "category": "Food",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token1}"}
    )
    transaction_id = create_response.json()["id"]

    response = client.get(
        f"/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 404

def test_update_transaction_success():
    """Test successful transaction update"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]

    create_response = client.post(
        "/transactions",
        json={
            "title": "Original",
            "amount": 100,
            "type": "expense",
            "category": "Food",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    transaction_id = create_response.json()["id"]

    response = client.put(
        f"/transactions/{transaction_id}",
        json={"title": "Updated", "amount": 200},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert float(response.json()["amount"]) == 200.0

def test_delete_transaction_success():
    """Test successful transaction deletion"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]

    create_response = client.post(
        "/transactions",
        json={
            "title": "ToDelete",
            "amount": 100,
            "type": "expense",
            "category": "Food",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    transaction_id = create_response.json()["id"]

    response = client.delete(
        f"/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    get_response = client.get(
        f"/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404

def test_filter_transactions_by_type():
    """Test filtering transactions by type"""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]

    client.post(
        "/transactions",
        json={
            "title": "Income1",
            "amount": 5000,
            "type": "income",
            "category": "Salary",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        "/transactions",
        json={
            "title": "Expense1",
            "amount": 500,
            "type": "expense",
            "category": "Food",
            "date": str(date.today())
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.get(
        "/transactions/filter?type=expense",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["type"] == "expense"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
