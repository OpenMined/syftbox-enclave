from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from syft_core import Client
from syft_rds import init_session
from typing import List
import tempfile
import shutil
import os
from loguru import logger

app = FastAPI(title="Farming Coop Web Server")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

client = Client.load()

@app.get("/datasets", response_class=JSONResponse)
def list_datasets():
    datasite_client = init_session(client.email)
    datasets = datasite_client.dataset.get_all()
    # Convert Pydantic objects to dicts for JSON serialization
    return {"datasets": [ds.model_dump() for ds in datasets]}

@app.get("/jobs", response_class=JSONResponse)
def list_jobs():
    datasite_client = init_session(client.email)
    jobs = datasite_client.jobs.get_all()
    # Convert Pydantic objects to dicts for JSON serialization
    return {"jobs": [job.model_dump() for job in jobs]}

def save_uploads_to_temp(upload, allow_multiple=False):
    """
    Save one or more UploadFile(s) to a temp directory or file.
    If allow_multiple is True, expects a list of UploadFile and returns a temp dir path.
    If allow_multiple is False, expects a single UploadFile and returns a file path.
    Returns only the path to the temp dir or file.
    If a folder is selected, returns the path to the folder itself (not the parent temp dir).
    """
    if allow_multiple:
        # Try to find the common root folder from the uploaded files
        filenames = [up.filename for up in upload]
        # Remove any leading slashes
        filenames = [f.lstrip(os.sep) for f in filenames]
        # Find the common prefix (folder)
        common_prefix = os.path.commonprefix(filenames)
        # If the common prefix is a partial folder name, trim to the last full folder
        if common_prefix and not common_prefix.endswith(os.sep):
            common_prefix = os.path.dirname(common_prefix)
        temp_dir = tempfile.mkdtemp()
        for up in upload:
            file_path = os.path.join(temp_dir, up.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(up.file, f)
        # If a folder was selected, return the path to that folder inside temp_dir
        if common_prefix:
            folder_path = os.path.join(temp_dir, common_prefix)
            if os.path.isdir(folder_path):
                return folder_path
        return temp_dir  # fallback: return the temp dir
    else:
        suffix = Path(upload.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(upload.file, tmp)
            return tmp.name  # Only return the file path

@app.post("/create-dataset", response_class=JSONResponse)
def create_dataset(
    name: str = Form(...),
    summary: str = Form(...),
    private_path: List[UploadFile] = File(...),
    mock_path: List[UploadFile] = File(...),
    description_path: UploadFile = File(...),
    auto_approval: str = Form(...)
):
    try:
        datasite_client = init_session(client.email)
        # Save private_path and mock_path (can be folder or file)
        private_path_on_disk = save_uploads_to_temp(private_path, allow_multiple=True)
        mock_path_on_disk = save_uploads_to_temp(mock_path, allow_multiple=True)
        # Save description_path (single file)
        description_path_on_disk = save_uploads_to_temp(description_path, allow_multiple=False)
        logger.info(f"Private path saved to: {private_path_on_disk}")
        logger.info(f"Mock path saved to: {mock_path_on_disk}")
        logger.info(f"Description path saved to: {description_path_on_disk}")
        dataset = datasite_client.dataset.create(
            name=name,
            summary=summary,
            path=private_path_on_disk,
            mock_path=mock_path_on_disk,
            description_path=description_path_on_disk,
            auto_approval=[auto_approval]
        )
        logger.info(f"Dataset created: {dataset}")
        return JSONResponse(status_code=201, content={"message": f"Dataset created successfully: {dataset.name}"})
    except Exception as e:
        logger.error(f"Error creating dataset: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

