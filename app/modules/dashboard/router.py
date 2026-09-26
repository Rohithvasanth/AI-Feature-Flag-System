import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Dashboard"])

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "index.html")

@router.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)
