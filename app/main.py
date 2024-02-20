from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.logger import logger
from fastapi.responses import PlainTextResponse
from jose import JWTError
from sqlalchemy.orm import Session
from .database import SessionLocal
from .auth import create_jwt_token, decode_jwt_token
from .models import User, VinylRecord
from .config import settings
from datetime import timedelta, datetime

from pydantic import BaseModel

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Схема VinylRecord
class Record(BaseModel):
    id: int
    title: str
    author: str
    duration: int
    description: str


# POST запрос на создание пользователя или обновление его токена
@app.post("/registration")
def register_user(username: str = Query(..., alias="user"), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        # Если пользователь уже существует, обновляем токен и возвращаем его
        token_data = {"sub": db_user.username}
        access_token_expires = timedelta(minutes=settings['ACCESS_TOKEN_EXPIRE_MINUTES'])
        new_token = create_jwt_token(token_data, expires_delta=access_token_expires)
        db_user.updated_at = datetime.utcnow()
        db.commit()
        token = new_token

    else:
        # Создаем нового пользователя
        new_user = User(username=username)
        db.add(new_user)
        db.commit()

        # Создаем токен для нового пользователя без сохранения в бд
        token_data = {"sub": new_user.username}
        access_token_expires = timedelta(minutes=settings['ACCESS_TOKEN_EXPIRE_MINUTES'])
        access_token = create_jwt_token(token_data, expires_delta=access_token_expires)
        token = access_token

    # Возвращаем токен текстом
    return PlainTextResponse(content=token)


# GET запрос для проверки доступа пользователя
@app.get("/user_check")
def check_user_access(token: str = Query(..., alias="token"), db: Session = Depends(get_db)):
    # try для случая, когда токена нет или он не валидный
    try:
        token_data = decode_jwt_token(token)
        username = token_data["sub"]
        user = db.query(User).filter(User.username == username).first()
        if user:
            return {
                "username": user.username,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "token_expires_at": token_data["exp"]
            }
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=404, detail="User not found")


# POST запрос для создания Виниловой Пластинки
@app.post("/records/create")
def create_record(
    record: Record, token: str = Query(..., alias="token"), db: Session = Depends(get_db)
):
    # try для случая, когда токена нет или он не валидный
    try:
        token_data = decode_jwt_token(token)
        username = token_data["sub"]
        user = db.query(User).filter(User.username == username).first()
        if user:
            new_record = VinylRecord(title=record.title, author=record.author, duration=record.duration, description=record.description, created_by=user.id)
            db.add(new_record)
            db.commit()
            return {"message": "Record created successfully"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# DELETE запрос для удаления Виниловой Пластинки
@app.delete("/records/delete")
def delete_record(record_id: int, token: str = Query(..., alias="token"), db: Session = Depends(get_db)):
    # try для случая, когда токена нет или он не валидный
    try:
        token_data = decode_jwt_token(token)
        username = token_data["sub"]
        user = db.query(User).filter(User.username == username).first()
        if user:
            db.query(VinylRecord).filter(VinylRecord.id == record_id).delete()
            db.commit()
            return {"message": "Record deleted successfully"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# PUT запрос для редактирования Виниловой Пластинки
@app.put("/records/update")
def update_record(
    record: Record, token: str = Query(..., alias="token"), db: Session = Depends(get_db)
):
    # try для случая, когда токена нет или он не валидный
    try:
        token_data = decode_jwt_token(token)
        username = token_data["sub"]
        user = db.query(User).filter(User.username == username).first()
        if user:
            db.query(VinylRecord).filter(VinylRecord.id == record.id).update({
                "title": record.title,
                "author": record.author,
                "duration": record.duration,
                "description": record.description,
                "created_by": user.id
            })
            db.commit()
            return {"message": "Record updated successfully"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# GET запрос для получения списка Виниловых Пластинок
@app.get("/records/get")
def get_records(
    token: str = Query(..., alias="token"),
    title: str = Query(None, alias="title"),
    author: str = Query(None, alias="author"),
    db: Session = Depends(get_db)
):
    # try для случая, когда токена нет или он не валидный
    try:
        token_data = decode_jwt_token(token)
        username = token_data["sub"]
        user = db.query(User).filter(User.username == username).first()
        if user:
            query = db.query(VinylRecord)
            # опциональный фильтр по полю title и author
            if title:
                query = query.filter(VinylRecord.title == title)
            if author:
                query = query.filter(VinylRecord.author == author)
            records = query.all()
            return records
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# GET запрос без авторизации для получения списка Виниловых Пластинок
@app.get("/records", response_model=None)
def get_public_records(db: Session = Depends(get_db)):
    # первые 10 пластинок с сортировкой по дате изменения
    records = db.query(VinylRecord).order_by(VinylRecord.updated_at.desc()).limit(10).all()
    return records

