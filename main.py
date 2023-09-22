from fastapi import FastAPI, Request, Query
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database import cars
from starlette.responses import HTMLResponse
from typing import Optional

templates = Jinja2Templates(directory="templates")

class Car(BaseModel):
  brand: str
  model: str
  year: str
  price: float
  color: str

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

@app.get("/car/{id}")
def get_car(id: int):
  car = cars.get(id)
  response = [];
  if (car):
    response.append(car);
  else:
    response.append("Car not found.")

  return response

@app.post("/add-car")
def add_car(
  brand: str,
  model: str,
  year: str,
  price: float,
  color: str,
  ):
  body_car = [Car(brand=brand, model=model, year=year, price=price, color=color)]
  if (len(body_car) < 1):
    return {"Oh ho!! Error Occured."}
  min_id = len(cars) + 1
  cars[min_id] = body_car

  return {"Added a carr"}

@app.post("/update-car/{id}")
def update_car(id: int):
  return {"Update the car info"}

@app.delete("/delete-car/{id}")
def delete_car(id: str):
  car = cars.get(id)
  if (car):
    del cars[id]
  else:
    return cars

  return {"Deleted the car"}
