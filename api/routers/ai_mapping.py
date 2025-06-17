from sqlalchemy.orm import Session
from database.session import get_db
from database.models import FontFile, Glyph
from services.font_service import FontService
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(tags=['AI Mapping'])


@router.post('/fonts/{font_id}/generate-ai-suggestions')
async def generate_ai_suggestions(font_id: int, db: Session = Depends(get_db)):
    """Generate AI suggestions for all unmapped glyphs in a font"""

    font_file = db.query(FontFile).filter(FontFile.id == font_id).first()
    if not font_file:
        raise HTTPException(status_code=404, detail='Font not found')

    unmapped_glyphs = db.query(Glyph).filter(Glyph.font_file_id == font_id, Glyph.mapping == '').all()

    if not unmapped_glyphs:
        return {'message': 'No unmapped glyphs found', 'processed': 0}

    processed = 0
    errors = 0

    for glyph in unmapped_glyphs:
        png_data = FontService.generate_png_for_glyph(glyph, font_file.upload_path)
        if not png_data:
            errors += 1
            continue

        ai_char = FontService.get_ai_suggestion_for_png(png_data)
        if ai_char:
            glyph.mapping = ai_char
            glyph.is_mapped = True
            processed += 1
        else:
            errors += 1

    db.commit()

    return {'font_id': font_id, 'processed': processed, 'errors': errors, 'total_unmapped': len(unmapped_glyphs)}
