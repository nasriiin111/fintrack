from urllib import response

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, test_engine, get_db
import pytest

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=test_engine)

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

def test_home():
    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Welcome to the FinTrack API",
        "status": "running"
    }

def test_users_me_without_token():
    response = client.get("/users/me")

    assert response.status_code == 401

def test_users_me_invalid_token():
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer invalidtoken"
        }
    )

    assert response.status_code == 401

def test_transaction_negative_amount():
    client.post(
        "/users/register",
        json={
            "username": "validationuser",
            "email": "validation123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "validation123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": -100,
            "transaction_type": "expense",
            "category": "Food",
            "description": "Invalid transaction"
        }
    )

    assert response.status_code == 422


def test_invalid_transaction_type():
    client.post(
        "/users/register",
        json={
            "username": "typeuser",
            "email": "typeuser123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "typeuser123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 500,
            "transaction_type": "shopping",
            "category": "Food",
            "description": "Invalid type"
        }
    )

    assert response.status_code == 422


def test_register_user():
    response = client.post(
        "/users/register",
        json={
            "username": "testuser",
            "email": "testuser123@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "testuser123@example.com"
    assert "password_hash" not in data

def test_login_user():
    client.post(
        "/users/register",
        json={
            "username": "testuser",
            "email": "testuser123@example.com",
            "password": "password123"
        }
    )

    response = client.post(
        "/users/login",
        json={
            "email": "testuser123@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_users_me_with_valid_token():
    register_response = client.post(
        "/users/register",
        json={
            "username": "authuser",
            "email": "authuser123@example.com",
            "password": "password123"
        }
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/users/login",
        json={
            "email": "authuser123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    profile_response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert profile_response.status_code == 200   

    data = profile_response.json()

    assert data["username"] == "authuser"
    assert data["email"] == "authuser123@example.com"
    assert "password_hash" not in data    


def test_create_transaction():
    client.post(
        "/users/register",
        json={
            "username": "transactionuser",
            "email": "transaction123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "transaction123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    transaction_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 500,
            "transaction_type": "expense",
            "category": "Food",
            "description": "Lunch"
        }
    )

    assert transaction_response.status_code == 200

    data = transaction_response.json()

    assert data["amount"] == "500.00"
    assert data["transaction_type"] == "expense"
    assert data["category"] == "Food"
    assert data["description"] == "Lunch"

def test_get_transactions():
    client.post(
        "/users/register",
        json={
            "username": "getuser",
            "email": "getuser123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "getuser123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    transaction_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 1000,
            "transaction_type": "expense",
            "category": "Shopping",
            "description": "Shoes"
        }
    )

    transaction_id = transaction_response.json()["id"]

    response = client.get(
        f"/transactions/{transaction_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == transaction_id
    assert data["amount"] == "1000.00"
    assert data["transaction_type"] == "expense"
    assert data["category"] == "Shopping"
    assert data["description"] == "Shoes"

    response = client.get(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    
    data = response.json()

    assert len(data) == 1
    assert data[0]["amount"] == "1000.00"
    assert data[0]["transaction_type"] == "expense"
    assert data[0]["category"] == "Shopping"
    assert data[0]["description"] == "Shoes"


def test_update_transaction():
    client.post(
        "/users/register",
        json={
            "username": "updateuser",
            "email": "updateuser123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "updateuser123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    transaction_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 500,
            "transaction_type": "expense",
            "category": "Food",
            "description": "Lunch"
        }
    )

    assert transaction_response.status_code == 200

    transaction_id = transaction_response.json()["id"]

    update_response = client.put(
        f"/transactions/{transaction_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 750,
            "transaction_type": "expense",
            "category": "Shopping",
            "description": "New shoes"
        }
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["id"] == transaction_id
    assert data["amount"] == "750.00"
    assert data["transaction_type"] == "expense"
    assert data["category"] == "Shopping"
    assert data["description"] == "New shoes"

def test_delete_transaction():
    client.post(
        "/users/register",
        json={
            "username": "deleteuser",
            "email": "deleteuser123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "deleteuser123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    transaction_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 300,
            "transaction_type": "expense",
            "category": "Food",
            "description": "Dinner"
        }
    )

    assert transaction_response.status_code == 200

    transaction_id = transaction_response.json()["id"]

    delete_response = client.delete(
        f"/transactions/{transaction_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert delete_response.status_code == 200

    get_response = client.get(
        f"/transactions/{transaction_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert get_response.status_code == 404


def test_user_cannot_access_other_users_transaction():
    client.post(
        "/users/register",
        json={
            "username": "userone",
            "email": "userone123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "userone123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token_user_one = login_response.json()["access_token"]

    client.post(
        "/users/register",
        json={
            "username": "usertwo",
            "email": "usertwo123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "usertwo123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token_user_two = login_response.json()["access_token"]
    transaction_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token_user_two}"
        },
        json={
            "amount": 1000,
            "transaction_type": "expense",
            "category": "Shopping",
            "description": "User B purchase"
        }
    )

    assert transaction_response.status_code == 200

    transaction_id = transaction_response.json()["id"]

    response = client.get(
        f"/transactions/{transaction_id}",
        headers={
            "Authorization": f"Bearer {token_user_one}"
        }
    )

    assert response.status_code == 404


def test_duplicate_email():
    client.post(
        "/users/register",
        json={
            "username": "duplicateuser",
            "email": "duplicate123@example.com",
            "password": "password123"
        }
    )

    response = client.post(
        "/users/register",
        json={
            "username": "anotheruser",
            "email": "duplicate123@example.com",
            "password": "password456"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_wrong_password():
    client.post(
        "/users/register",
        json={
            "username": "wrongpassuser",
            "email": "wrongpass123@example.com",
            "password": "password123"
        }
    )

    response = client.post(
        "/users/login",
        json={
            "email": "wrongpass123@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect password"


def test_analytics_summary():
    client.post(
        "/users/register",
        json={
            "username": "analyticsuser",
            "email": "analytics123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "analytics123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    income_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 5000,
            "transaction_type": "income",
            "category": "Salary",
            "description": "Monthly salary"
        }
    )

    assert income_response.status_code == 200

    expense_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 1500,
            "transaction_type": "expense",
            "category": "Food",
            "description": "Groceries"
        }
    )

    assert expense_response.status_code == 200

    response = client.get(
        "/analytics/summary",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_income"] == 5000.00
    assert data["total_expense"] == 1500.00
    assert data["balance"] == 3500.00

def test_analytics_categories():
    client.post(
        "/users/register",
        json={
            "username": "categoryuser",
            "email": "category123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "category123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    food_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 1000,
            "transaction_type": "expense",
            "category": "Food",
            "description": "Groceries"
        }
    )

    assert food_response.status_code == 200

    food_response_2 = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 500,
            "transaction_type": "expense",
            "category": "Food",
            "description": "Lunch"
        }
    )

    assert food_response_2.status_code == 200

    shopping_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 2000,
            "transaction_type": "expense",
            "category": "Shopping",
            "description": "Clothes"
        }
    )

    assert shopping_response.status_code == 200

    response = client.get(
        "/analytics/categories",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["Food"] == 1500.0
    assert data["Shopping"] == 2000.0

def test_analytics_monthly():
    client.post(
        "/users/register",
        json={
            "username": "monthlyuser",
            "email": "monthly123@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "monthly123@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    income_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 10000,
            "transaction_type": "income",
            "category": "Salary",
            "description": "Monthly salary"
        }
    )

    assert income_response.status_code == 200

    expense_response = client.post(
        "/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "amount": 3000,
            "transaction_type": "expense",
            "category": "Rent",
            "description": "Monthly rent"
        }
    )

    assert expense_response.status_code == 200

    response = client.get(
        "/analytics/monthly",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    month = list(data.keys())[0]

    assert data[month]["income"] == 10000.0
    assert data[month]["expense"] == 3000.0


def test_create_transaction_with_custom_date():
    client.post(
        "/users/register",
        json={
            "username": "dateuser",
            "email": "dateuser@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/users/login",
        json={
            "email": "dateuser@example.com",
            "password": "password123"
        }
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/transactions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "amount": 1500,
            "transaction_type": "expense",
            "category": "Shopping",
            "description": "New shoes",
            "date": "2026-08-15T10:30:00"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["amount"] == "1500.00"
    assert data["category"] == "Shopping"
    assert data["description"] == "New shoes"
    assert "2026-08-15" in data["date"]