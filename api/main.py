import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.models import Base
from database.database import engine
from routers import svg, fonts, glyphs

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description='API for PDF Font Analysis',
    version='1.0.0',
    debug=settings.IS_DEBUG,
    default_response_class=ORJSONResponse,
)

if settings.ALLOWED_HOSTS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_HOSTS],
        allow_credentials=True,
        allow_methods=['GET', 'POST'],
        allow_headers=['*'],
    )

app.include_router(svg.router, prefix='/api')
app.include_router(fonts.router, prefix='/api')
app.include_router(glyphs.router, prefix='/api')


@app.get('/')
async def root():
    """Root endpoint providing basic information about the API"""
    return {
        'message': 'PDF Font Analyzer API',
        'version': '1.0.0',
        'features': [
            'PDF font upload and analysis',
            'Glyph extraction',
            'Font metadata retrieval',
        ],
    }
