from typing import List
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Request
from sqlalchemy.orm import Session, selectinload
from datetime import datetime
from pydantic import BaseModel

from database.session import get_db
from database.models import SVGFile, FontFile
from services.svg_service import SVGService


# Pydantic schemas
class GlyphOut(BaseModel):
    id: int
    codepoint: str
    preview_image: str
    mapping: str
    is_mapped: bool

    class Config:
        from_attributes = True


class FontFileOut(BaseModel):
    id: int
    svg_file_id: int
    font_name: str
    filename: str
    created_at: datetime
    glyphs: List[GlyphOut] = []

    class Config:
        from_attributes = True


router = APIRouter(tags=['SVG'])


@router.post('/upload-zip')
async def upload_zip(file: UploadFile = File(...)):
    """Upload ZIP file containing SVG and font files, process all SVGs"""

    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail='Only ZIP files are allowed')

    # Read the file content
    content = await file.read()

    # Start background processing
    task_id = SVGService.start_zip_processing(content, file.filename)

    # Return immediately with task_id
    return {'message': 'ZIP upload started, processing in background', 'task_id': task_id, 'status': 'processing'}


@router.post('/upload-svg')
async def upload_svg(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload single SVG file"""
    if not file.filename.endswith('.svg'):
        raise HTTPException(status_code=400, detail='Only SVG files are allowed')

    content = await file.read()
    result = SVGService.save_svg_file(content, file.filename, db)

    return {
        'file_id': result['file_id'],
        'filename': result['filename'],
        'required_fonts': result['required_fonts'],
        'message': 'SVG uploaded successfully',
    }


@router.get('/svg/{svg_file_id}/source-of-truth')
async def get_source_of_truth_svg(svg_file_id: int, request: Request, db: Session = Depends(get_db)):
    """Get SVG content with fixed font URLs"""
    svg_file = db.query(SVGFile).filter(SVGFile.id == svg_file_id).first()
    if not svg_file:
        raise HTTPException(status_code=404, detail='SVG file not found')

    content_with_fonts = SVGService.fix_font_urls_in_svg(svg_file.content, svg_file_id, db, request)

    return {'source_of_truth_content': content_with_fonts}


@router.get('/svg/{svg_file_id}/fonts', response_model=List[FontFileOut])
async def get_svg_fonts(svg_file_id: int, db: Session = Depends(get_db)):
    """Get fonts associated with an SVG file"""
    fonts = db.query(FontFile).filter(FontFile.svg_file_id == svg_file_id).options(selectinload(FontFile.glyphs)).all()
    return fonts


@router.get('/upload-progress/{task_id}')
async def get_upload_progress(task_id: str):
    """Get upload progress for a task"""
    return SVGService.get_progress(task_id)


@router.get('/svgs')
async def get_all_svgs(page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    """Get paginated list of all processed SVG files"""
    offset = (page - 1) * limit

    # Get total count
    total = db.query(SVGFile).count()

    # Get paginated SVG files (most recent first)
    svgs = db.query(SVGFile).order_by(SVGFile.created_at.desc()).offset(offset).limit(limit).all()

    svg_list = []
    for svg in svgs:
        svg_list.append({'svg_file_id': svg.id, 'filename': svg.filename, 'upload_date': svg.created_at.isoformat()})

    return {
        'svgs': svg_list,
        'pagination': {
            'current_page': page,
            'total_pages': (total + limit - 1) // limit,
            'total_items': total,
            'items_per_page': limit,
            'has_next': page * limit < total,
            'has_previous': page > 1,
        },
    }
