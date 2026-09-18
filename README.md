# FinTrack — Personal Finance & Transaction API

FinTrack is a backend REST API for managing personal finances and tracking income and expenses.

The application provides secure user authentication, transaction management, PostgreSQL database integration, and financial analytics through RESTful API endpoints.

## Key Features

* User registration and login
* JWT-based authentication
* Secure password hashing using Argon2
* Income and expense tracking
* Transaction CRUD operations
* User-specific transaction access
* Category-based expense analytics
* Monthly financial summaries
* PostgreSQL database integration
* Input validation with Pydantic
* Automated API testing with Pytest
* Environment-based configuration for sensitive credentials

## Technology Stack

| Technology   | Purpose                           |
| ------------ | --------------------------------- |
| Python       | Backend programming language      |
| FastAPI      | REST API framework                |
| PostgreSQL   | Relational database               |
| SQLAlchemy   | Database ORM                      |
| Pydantic     | Data validation and serialization |
| JWT          | Authentication                    |
| Argon2       | Secure password hashing           |
| Pytest       | Automated testing                 |
| HTTPX        | API testing                       |
| Uvicorn      | ASGI server                       |
| Git & GitHub | Version control                   |

## System Architecture

```text
                     Client
                       |
                       v
                +--------------+
                |   FastAPI    |
                |   REST API   |
                +--------------+
                       |
          +------------+------------+
          |            |            |
          v            v            v
      Users API   Transactions   Analytics
          |            |            |
          +------------+------------+
                       |
                       v
                +--------------+
                |  SQLAlchemy  |
                |     ORM      |
                +--------------+
                       |
                       v
                +--------------+
                | PostgreSQL   |
                |   Database   |
                +--------------+
```

## Authentication Flow

FinTrack uses JWT-based authentication.

```text
User
 |
 | Register
 v
Password Hashing
 |
 v
PostgreSQL
 |
 | Login
 v
Password Verification
 |
 v
JWT Access Token
 |
 v
Authenticated API Requests
```

Passwords are never stored as plain text. Passwords are hashed before being stored in the database.

Protected endpoints require a valid Bearer token.

## Database Design

FinTrack currently uses two primary tables:

### Users

Stores registered user information.

| Field         | Description              |
| ------------- | ------------------------ |
| id            | Unique user identifier   |
| username      | User's username          |
| email         | Unique email address     |
| password_hash | Securely hashed password |

### Transactions

Stores financial transactions belonging to users.

| Field            | Description                      |
| ---------------- | -------------------------------- |
| id               | Unique transaction identifier    |
| user_id          | ID of the transaction owner      |
| amount           | Transaction amount               |
| transaction_type | Income or expense                |
| category         | Transaction category             |
| description      | Optional transaction description |
| date             | Transaction timestamp            |

The `user_id` field creates a relationship between transactions and their corresponding users.

## API Endpoints

### User Endpoints

| Method | Endpoint          | Description                           | Authentication |
| ------ | ----------------- | ------------------------------------- | -------------- |
| POST   | `/users/register` | Register a new user                   | No             |
| POST   | `/users/login`    | Authenticate user and receive JWT     | No             |
| GET    | `/users/me`       | Retrieve authenticated user's profile | Yes            |

### Transaction Endpoints

| Method | Endpoint             | Description                     | Authentication |
| ------ | -------------------- | ------------------------------- | -------------- |
| POST   | `/transactions`      | Create a transaction            | Yes            |
| GET    | `/transactions`      | Retrieve user's transactions    | Yes            |
| GET    | `/transactions/{id}` | Retrieve a specific transaction | Yes            |
| PUT    | `/transactions/{id}` | Update a transaction            | Yes            |
| DELETE | `/transactions/{id}` | Delete a transaction            | Yes            |

### Analytics Endpoints

| Method | Endpoint                | Description                                   | Authentication |
| ------ | ----------------------- | --------------------------------------------- | -------------- |
| GET    | `/analytics/summary`    | Calculate total income, expenses and balance  | Yes            |
| GET    | `/analytics/categories` | Calculate expenses by category                | Yes            |
| GET    | `/analytics/monthly`    | Generate monthly income and expense summaries | Yes            |

## API Validation

FinTrack validates incoming data before processing requests.

Examples include:

* Email format validation
* Minimum username length
* Minimum password length
* Positive transaction amounts
* Restricted transaction types (`income` or `expense`)
* Required transaction fields

Invalid input is rejected with an appropriate HTTP validation response.

## Authorization

Users can access only their own transactions.

For transaction operations, the authenticated user's ID is checked against the transaction's `user_id`.

For example:

```text
User A
  |
  | Request transaction #10
  v
API checks:
transaction.user_id == authenticated_user.id
  |
  +---- Yes ---> Allow request
  |
  +---- No ----> Return 404
```

This prevents one user from accessing another user's financial records through the API.

## Testing

The project includes automated tests using Pytest and FastAPI's testing tools.

The test suite currently contains **18 automated tests** covering:

* API health check
* Authentication requirements
* Invalid JWT tokens
* User registration
* User login
* User profile retrieval
* Password validation
* Duplicate email handling
* Transaction creation
* Transaction retrieval
* Transaction updates
* Transaction deletion
* Transaction validation
* Invalid transaction types
* User authorization
* Financial summary calculations
* Category-based analytics
* Monthly analytics

Run the complete test suite with:

```bash
python -m pytest -v
```

Expected result:

```text
18 passed
```

## Project Structure

```text
FinTrack/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── security.py
│
├── tests/
│   └── test_main.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

### Application Modules

**`main.py`**

Contains the FastAPI application and API endpoints.

**`database.py`**

Handles PostgreSQL database configuration and SQLAlchemy database sessions.

**`models.py`**

Defines the SQLAlchemy database models.

**`schemas.py`**

Defines Pydantic request and response schemas and validates incoming data.

**`security.py`**

Handles password hashing, password verification and JWT token creation/validation.

**`tests/test_main.py`**

Contains the automated API test suite.

## Environment Configuration

Sensitive configuration is stored in environment variables rather than directly in the source code.

The local `.env` file contains values such as:

```text
SECRET_KEY=your-secret-key
DB_PASSWORD=your-postgresql-password
```

The `.env` file is excluded from Git using `.gitignore`.

**Never commit real passwords, API keys, JWT secrets, or other credentials to GitHub.**

## Local Setup

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd FinTrack
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```text
SECRET_KEY=your-secret-key
DB_PASSWORD=your-postgresql-password
```

### 5. Create the PostgreSQL database

Create a PostgreSQL database named:

```text
fintrack
```

The application creates the required tables using SQLAlchemy when it starts.

### 6. Start the API

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 7. Open the API documentation

FastAPI automatically provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

## Running Tests

The test suite uses a separate PostgreSQL database for testing.

The local test database is:

```text
fintrack_test
```

Run:

```bash
python -m pytest -v
```

The test database is separate from the application's main database so that automated tests do not operate on normal development data.

## Example API Workflow

A typical user workflow is:

```text
1. Register
      ↓
2. Login
      ↓
3. Receive JWT access token
      ↓
4. Send authenticated transaction request
      ↓
5. Store transaction in PostgreSQL
      ↓
6. Retrieve financial analytics
```

## Future Improvements

Planned improvements include:

* Docker containerization
* GitHub Actions CI/CD
* Improved database configuration
* Database migrations using Alembic
* Pagination and filtering for transactions
* Date-range analytics
* Budget management
* Recurring transactions
* Frontend dashboard
* Improved API documentation
* Production deployment

## Learning Outcomes

This project demonstrates practical experience with:

* Python backend development
* REST API design
* FastAPI
* PostgreSQL
* SQL and relational databases
* SQLAlchemy ORM
* Authentication and authorization
* JWT
* Password hashing
* Data validation
* Error handling
* Automated testing
* Git and GitHub
* Environment-based configuration

## License

This project is intended as a personal portfolio and learning project.
