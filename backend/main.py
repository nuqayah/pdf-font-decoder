import uuid
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from concurrent.futures import ThreadPoolExecutor

from models import Base, SVGFile, FontFile, Glyph
from utils import extract_font_references, generate_glyphs_from_font

app = FastAPI(
    title="SVG Font Analyzer API",
    description="API for analyzing SVG files, identify obfuscated text that uses custom embedded fonts, and mapping glyphs to their corresponding characters, effectively 'decoding' the content",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./svg_font_analyzer.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / "svg").mkdir(exist_ok=True)
(UPLOAD_DIR / "fonts").mkdir(exist_ok=True)

upload_progress: Dict[str, Dict[str, Any]] = {}
thread_pool = ThreadPoolExecutor(max_workers=4)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def update_progress(task_id: str, current: int, total: int, message: str):
    upload_progress[task_id] = {
        "current": current,
        "total": total,
        "percentage": int((current / total) * 100) if total > 0 else 0,
        "message": message,
        "completed": current >= total
    }

@app.post("/upload-svg")
async def upload_svg(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".svg"):
        raise HTTPException(status_code=400, detail="Only SVG files are allowed")
    file_id = str(uuid.uuid4())
    path = UPLOAD_DIR / "svg" / f"{file_id}_{file.filename}"
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    text = content.decode("utf-8")
    fonts = extract_font_references(text)
    svg = SVGFile(filename=file.filename, content=text, upload_path=str(path))
    db.add(svg)
    db.commit()
    return {"file_id": svg.id, "filename": file.filename, "required_fonts": fonts}

@app.post("/upload-fonts/{svg_file_id}")
async def upload_fonts(svg_file_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    svg = db.query(SVGFile).filter(SVGFile.id == svg_file_id).first()
    if not svg:
        raise HTTPException(status_code=404, detail="SVG file not found")
    uploaded = []
    for file in files:
        if not (file.filename.endswith(".woff") or file.filename.endswith(".woff2") or file.filename.endswith(".ttf") or file.filename.endswith(".otf")):
            continue
        file_id = str(uuid.uuid4())
        path = UPLOAD_DIR / "fonts" / f"{file_id}_{file.filename}"
        content = await file.read()
        with open(path, "wb") as f:
            f.write(content)
        name = file.filename.rsplit(".", 1)[0]
        font = FontFile(svg_file_id=svg_file_id, font_name=name, filename=file.filename, upload_path=str(path))
        db.add(font)
        db.commit()
        generate_glyphs_from_font(db, font.id, str(path))
        uploaded.append({"font_id": font.id, "font_name": name, "filename": file.filename})
    return {"svg_file_id": svg_file_id, "uploaded_fonts": uploaded}

@app.get("/fonts/{svg_file_id}")
async def get_fonts(svg_file_id: int, db: Session = Depends(get_db)):
    fonts = db.query(FontFile).filter(FontFile.svg_file_id == svg_file_id).options(selectinload(FontFile.glyphs)).all()
    return [{
        "font_id": f.id,
        "font_name": f.font_name,
        "filename": f.filename,
        "font_url": f"/font-file/{f.id}",
        "glyphs": [{
            "glyph_id": g.id,
            "codepoint": g.codepoint,
            "preview_image": g.preview_image,
            "mapping": g.mapping,
            "is_mapped": g.is_mapped
        } for g in f.glyphs]
    } for f in fonts]

@app.get("/svg/{svg_file_id}/source-of-truth")
async def get_source_svg(svg_file_id: int, db: Session = Depends(get_db)):
    svg = db.query(SVGFile).filter(SVGFile.id == svg_file_id).first()
    if not svg:
        raise HTTPException(status_code=404, detail="SVG file not found")
    return {"source_of_truth_content": svg.content}

@app.get("/font-file/{font_id}")
async def get_font_file(font_id: int, db: Session = Depends(get_db)):
    font = db.query(FontFile).filter(FontFile.id == font_id).first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")
    path = Path(font.upload_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Font file not found on disk")
    media_type = "font/woff2" if font.filename.endswith(".woff2") else "font/woff"
    return FileResponse(str(path), media_type=media_type)

@app.put("/glyph/{glyph_id}/mapping")
async def update_glyph_mapping(glyph_id: int, mapping_data: Dict[str, str], db: Session = Depends(get_db)):
    glyph = db.query(Glyph).filter(Glyph.id == glyph_id).first()
    if not glyph:
        raise HTTPException(status_code=404, detail="Glyph not found")
    glyph.mapping = mapping_data.get("mapping", "")
    glyph.is_mapped = bool(glyph.mapping.strip())
    db.commit()
    return {"glyph_id": glyph.id, "mapping": glyph.mapping, "is_mapped": glyph.is_mapped}

@app.get("/upload-progress/{task_id}")
async def get_upload_progress(task_id: str):
    return upload_progress.get(task_id, {
        "current": 0,
        "total": 0,
        "percentage": 0,
        "message": "Task not found",
        "completed": False
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)