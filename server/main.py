from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List

app = FastAPI(title="Farming Coop Web Server")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

datasets = [
    {"name": "Crop Data 2024", "summary": "Yield and weather data", "auto_approval": "yes"},
    {"name": "Soil Quality", "summary": "Soil pH and nutrients", "auto_approval": "no"}
]

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/datasets", response_class=JSONResponse)
def list_datasets():
    return {"datasets": datasets}

@app.post("/create-dataset", response_class=JSONResponse)
def create_dataset(
    name: str = Form(...),
    summary: str = Form(...),
    private_path: UploadFile = File(...),
    mock_path: UploadFile = File(...),
    auto_approval: str = Form(...)
):
    # Dummy logic: just append to datasets list
    datasets.append({
        "name": name,
        "summary": summary,
        "auto_approval": auto_approval
    })
    return {"success": True, "message": "Dataset created successfully!"}

@app.post("/process", response_class=JSONResponse)
def process_data(data: str = Form(...)):
    # Placeholder for processing logic
    # You can import and call your backend logic here
    result = {"received": data, "status": "Processed successfully"}
    return result
