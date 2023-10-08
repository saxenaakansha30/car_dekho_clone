from fastapi import FastAPI, Request, Query, Form, status, HTTPException, Depends
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from database import cars
from starlette.responses import HTMLResponse
from starlette.status import HTTP_400_BAD_REQUEST
from typing import Optional, List
from fastapi.encoders import jsonable_encoder

## for Login ##
from user_db import users
from passlib.context import CryptContext
from fastapi_login import LoginManager
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta

templates = Jinja2Templates(directory="templates")

class Car(BaseModel):
  brand: Optional[str]
  model: Optional[str]
  year: Optional[int]
  price: Optional[int]
  color: Optional[str]

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
  return templates.TemplateResponse("index.html", {"request": request, "response": "Home Page"})

@app.get("/cars", response_class=HTMLResponse)
def list_cars(request: Request, limit: Optional[str] = Query(9, max_length=3)):
  response = []
  for id, car in list(cars.items())[:int(limit)]:
    response.append((id, car))
  # return response
  return templates.TemplateResponse("see-all-cars.html", {"request": request, "cars": response, "title": "See All Cars"})

@app.get("/create-car", response_class=HTMLResponse)
def create_car(request: Request):
  return templates.TemplateResponse("create-car.html", {"request": request})

@app.post("/cars", status_code=status.HTTP_201_CREATED)
def add_car(
  brand: Optional[str] = Form(...),
  model: Optional[str] = Form(...),
  year: Optional[int] = Form(...),
  price: Optional[int] = Form(...),
  color: Optional[str] = Form(...),
  ):
  body_car = [Car(brand=brand, model=model, year=year, price=price, color=color)]
  if (len(body_car) < 1):
    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, default="No cars to add.")
  min_id = len(cars) + 1
  cars[min_id] = jsonable_encoder(body_car[0])

  return RedirectResponse(url="/cars", status_code = 302)

@app.get("/car/{id}", response_class=HTMLResponse)
def get_car(request: Request, id: int):
  car = cars.get(id)
  response = [];
  if not car:
    return RedirectResponse(url="/404", status_code = 302)

  return templates.TemplateResponse("car.html", {"request": request, "id": id, "car" : car})

@app.post("/update-car/{id}")
def update_car(
  request: Request,
  id: int,
  brand: Optional[str] = Form(...),
  model: Optional[str] = Form(...),
  year: Optional[int] = Form(...),
  price: Optional[int] = Form(...),
  color: Optional[str] = Form(...),
):
  stored = cars[id]

  if not stored:
    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="The car does not exist")

  body_car = Car(brand=brand, model=model, year=year, price=price, color=color)
  cars[id] = jsonable_encoder(body_car)

  return RedirectResponse(url="/cars", status_code = 302)

@app.get("/update-car/{id}")
def update_car(request: Request, id: int):
  car = cars[id]

  if not car:
    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="The car does not exist")

  return templates.TemplateResponse("edit-car.html", {"request": request, "id": id, "car" : car})

@app.get("/delete-car/{id}")
def delete_car(request: Request, id: int):
  car = cars.get(id)
  if not car:
    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="The car does not exist")

  del cars[id]
  return RedirectResponse(url="/cars", status_code = 302)

@app.post("/search")
def search(
  request: Request,
  id: Optional[int] = Form(...)
  ):

  car = cars[id]

  if not car:
    return RedirectResponse(url="/404", status_code = 302)

  return RedirectResponse(url=f"/car/{id}", status_code = 302)

@app.get("/404", response_class=HTMLResponse)
def search(request: Request):
  return templates.TemplateResponse("404.html", {"request": request})

### Login Functionality ####

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRES_MINUTES = 60

manager = LoginManager(secret=SECRET_KEY, token_url="/login", use_cookie=True)
manager.cookie_name = "auth"

@manager.user_loader()
def get_user_from_db(username: str):
  if username in users.keys():
    return UserDB(**users[username])

def authenticate_user(username: str, password: str):
  user = get_user_from_db(username)
  if not user:
    return None
  if not verify_password(password, user.hashed_password):
    return None

  return user

password_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hashed_password(plain_password: str):
  return password_ctx.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str):
  return password_ctx.verify(plain_password, hashed_password)

class Notification(BaseModel):
  author: str
  description: str

class User(BaseModel):
  name: str
  username: str
  email: str
  birthday: Optional[str] = ""
  friends: Optional[List[str]] = []
  notifications: Optional[List[Notification]] = []

class UserDB(User):
  hashed_password: str

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
  return templates.TemplateResponse("login.html", {"request": request,  "invalid": False})

@app.post("/login")
def login(
  request: Request,
  form_data: OAuth2PasswordRequestForm = Depends()
  ):

  user = authenticate_user(form_data.username, form_data.password)
  if not user:
      return templates.TemplateResponse("login.html", {"request": request, "invalid": True}, status_code=status.HTTP_401_UNAUTHORIZED)
  # Create session.
  access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
  access_token = manager.create_access_token(
      data={"sub": user.username},
      expires=access_token_expires
  )
  resp = RedirectResponse("/user", status_code=status.HTTP_302_FOUND)
  manager.set_cookie(resp,access_token)

  return resp

@app.get("/user")
def get_user(request: Request, user: User = Depends(manager)):
  user = User(**dict(user))
  return templates.TemplateResponse("user-info.html", {"request": request, "user": user})

@app.get("/logout", response_class=RedirectResponse)
def logout():
    response = RedirectResponse("/")
    manager.set_cookie(response, None)
    return response

@app.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse("register.html",{"request": request, "title": "FriendConnect - Register"})


@app.post("/register")
def register(request: Request, username: str = Form(...), name: str = Form(...), password: str = Form(...), email: str = Form(...)):
    hashed_password = get_hashed_password(password)
    invalid = False
    for db_username in users.keys():
        if username == db_username:
            invalid = True
        elif users[db_username]["email"] == email:
            invalid = True

    if invalid:
        return templates.TemplateResponse("register.html",{"request": request, "title": "FriendConnect - Register", "invalid": True},status_code=status.HTTP_400_BAD_REQUEST)

    users[username] = jsonable_encoder(UserDB(username=username,email=email,name=name,hashed_password=hashed_password))
    response = RedirectResponse("/login",status_code=status.HTTP_302_FOUND)
    manager.set_cookie(response,None)
    return response
