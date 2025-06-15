import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import engine
from database.models import Base
from routers import svg, fonts, glyphs

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title='SVG Font Analyzer API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5020',
        'http://localhost:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5020',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include routers
app.include_router(svg.router)
app.include_router(fonts.router)
app.include_router(glyphs.router)


@app.get('/')
async def root():
    return {'message': 'SVG Font Analyzer API'}
