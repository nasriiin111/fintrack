from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import engine, Base, get_db
from . import models, schemas
from .security import hash_password, verify_password, create_access_token, get_current_user_id
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
def current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    return get_current_user_id(token)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinTrack API", description="Personal Finance and Transaction Management API", version="1.0.0")

@app.get("/")
def home():
    return {"message": "Welcome to the FinTrack API",
            "status": "running"}


@app.post("/users/register", response_model=schemas.UserResponse)
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = hash_password(user.password)

    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/users/login")
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not verify_password(user.password, existing_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect password"
        )

    access_token = create_access_token(existing_user.id)

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/users/me")
def get_my_profile(
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }

@app.post("/transactions", response_model=schemas.TransactionResponse)
def create_transaction(
    transaction: schemas.TransactionCreate,
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db)
):

    new_transaction = models.Transaction(
        user_id=user_id,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        category=transaction.category,
        description=transaction.description
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction

@app.get("/transactions", response_model=list[schemas.TransactionResponse])
def get_transactions(
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db)
):

    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id
    ).all()

    return transactions

@app.get("/transactions/{transaction_id}", response_model=schemas.TransactionResponse)
def get_transaction(
    transaction_id: int,
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db)
):

    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == user_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction

@app.put("/transactions/{transaction_id}", response_model=schemas.TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_data: schemas.TransactionUpdate,
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db)
):

    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == user_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    transaction.amount = transaction_data.amount
    transaction.transaction_type = transaction_data.transaction_type
    transaction.category = transaction_data.category
    transaction.description = transaction_data.description

    db.commit()
    db.refresh(transaction)

    return transaction

@app.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db)
):

    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == user_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transaction deleted successfully"
    }


@app.get("/analytics/summary")
def get_summary(
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db)
):

    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id
    ).all()

    total_income = sum(
        transaction.amount
        for transaction in transactions
        if transaction.transaction_type == "income"
    )

    total_expense = sum(
        transaction.amount
        for transaction in transactions
        if transaction.transaction_type == "expense"
    )

    balance = total_income - total_expense

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance
    }


@app.get("/analytics/categories")
def get_category_summary(
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db)
):

    results = db.query(
        models.Transaction.category,
        func.sum(models.Transaction.amount).label("total")
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.transaction_type == "expense"
    ).group_by(
        models.Transaction.category
    ).all()

    return {
        category: total
        for category, total in results
    }

@app.get("/analytics/monthly")
def get_monthly_summary(
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db)
):

    results = db.query(
        func.date_trunc(
            "month",
            models.Transaction.date
        ).label("month"),
        models.Transaction.transaction_type,
        func.sum(models.Transaction.amount).label("total")
    ).filter(
        models.Transaction.user_id == user_id
    ).group_by(
        func.date_trunc(
            "month",
            models.Transaction.date
        ),
        models.Transaction.transaction_type
    ).order_by(
        func.date_trunc(
            "month",
            models.Transaction.date
        )
    ).all()

    monthly_data = {}

    for month, transaction_type, total in results:

        month_name = month.strftime("%Y-%m")

        if month_name not in monthly_data:
            monthly_data[month_name] = {
                "income": 0,
                "expense": 0
            }

        monthly_data[month_name][transaction_type] = total

    return monthly_data