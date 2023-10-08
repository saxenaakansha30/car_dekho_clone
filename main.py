from fastapi import FastAPI, Request, Query, Form, status, HTTPException
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from database import cars
from starlette.responses import HTMLResponse
from starlette.status import HTTP_400_BAD_REQUEST
from typing import Optional
from fastapi.encoders import jsonable_encoder

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

@app.get("/car/{id}", response_class=HTMLResponse)
def get_car(request: Request, id: int):
  car = cars.get(id)
  response = [];
  if not car:
    return RedirectResponse(url="/404", status_code = 302)

  return templates.TemplateResponse("car.html", {"request": request, "id": id, "car" : car})

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

