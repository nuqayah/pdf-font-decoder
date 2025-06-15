from pathlib import Path
from typing import List
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload

from database.session import get_db
from database.models import FontFile, SVGFile
from services.font_service import FontService

router = APIRouter(tags=['Fonts'])


@router.get('/font-file/{font_id}')
async def get_font_file(font_id: int, db: Session = Depends(get_db)):
    font_file = db.query(FontFile).filter(FontFile.id == font_id).first()
    if not font_file:
        raise HTTPException(status_code=404, detail='Font file not found')

    file_path = Path(font_file.upload_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='Font file not found on disk')

    media_type = 'font/woff2' if font_file.filename.endswith('.woff2') else 'font/woff'

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={'Access-Control-Allow-Origin': '*', 'Cache-Control': 'public, max-age=31536000'},
    )


@router.post('/upload-fonts/{svg_file_id}')
async def upload_fonts(svg_file_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Upload font files for an SVG"""
    svg_file = db.query(SVGFile).filter(SVGFile.id == svg_file_id).first()
    if not svg_file:
        raise HTTPException(status_code=404, detail='SVG file not found')

    uploaded_fonts = []

    for file in files:
        if not (file.filename.endswith('.woff') or file.filename.endswith('.woff2')):
            continue

        content = await file.read()
        font_result = FontService.save_font_file(content, file.filename, svg_file_id, db)
        uploaded_fonts.append(font_result)

    return {
        'svg_file_id': svg_file_id,
        'uploaded_fonts': uploaded_fonts,
        'message': f'Uploaded {len(uploaded_fonts)} font files',
    }


@router.get('/fonts/{svg_file_id}')
async def get_fonts(svg_file_id: int, db: Session = Depends(get_db)):
    fonts = db.query(FontFile).filter(FontFile.svg_file_id == svg_file_id).options(selectinload(FontFile.glyphs)).all()

    result = []
    for font in fonts:
        result.append(
            {
                'font_id': font.id,
                'font_name': font.font_name,
                'filename': font.filename,
                'font_url': f'/font-file/{font.id}',
                'glyphs': [
                    {
                        'glyph_id': glyph.id,
                        'codepoint': glyph.codepoint,
                        'preview_image': glyph.preview_image,
                        'mapping': glyph.mapping,
                        'is_mapped': glyph.is_mapped,
                    }
                    for glyph in font.glyphs
                ],
            }
        )

    return {'fonts': result}
