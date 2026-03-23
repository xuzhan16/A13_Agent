from pathlib import Path
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging


STATIC_DIR = Path(__file__).resolve().parent / 'static'
INDEX_FILE = STATIC_DIR / 'index.html'


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

        @app.get('/demo', include_in_schema=False)
        def demo() -> FileResponse:
            return FileResponse(INDEX_FILE)

    return app


app = create_app()
