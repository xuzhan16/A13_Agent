from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging

from fastapi.responses import HTMLResponse
import os


STATIC_DIR = Path(__file__).resolve().parent / 'static'
INDEX_FILE = STATIC_DIR / 'index.html'
NEO4J_EXPLORER_FILE = STATIC_DIR / 'neo4j-explorer.html'


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version='0.1.0',
        description='Evidence-driven career planning agent backend.',
    )
    app.include_router(api_router, prefix='/api')

    if STATIC_DIR.exists():
        app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')

        @app.get('/', include_in_schema=False)
        def index() -> FileResponse:
            return FileResponse(INDEX_FILE)
        @app.get("/chat", response_class=HTMLResponse)
        async def chat_page():
            # 注意：static 文件夹的路径要正确，这里假设 chat.html 放在 backend/app/static/ 下
            file_path = os.path.join(os.path.dirname(__file__), "static", "chat.html")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                return HTMLResponse(content=html_content)
            except FileNotFoundError:
                return HTMLResponse(content="<h1>聊天页面未找到，请检查文件路径</h1>", status_code=404)
        @app.get('/demo', include_in_schema=False)
        def demo() -> FileResponse:
            return FileResponse(INDEX_FILE)

        if NEO4J_EXPLORER_FILE.exists():
            @app.get('/neo4j-explorer', include_in_schema=False)
            def neo4j_explorer() -> FileResponse:
                return FileResponse(NEO4J_EXPLORER_FILE)

    return app


app = create_app()
