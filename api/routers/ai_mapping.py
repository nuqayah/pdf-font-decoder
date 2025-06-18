from sqlalchemy.orm import Session
from database.session import get_db
from database.models import FontFile, Glyph
from services.font_service import FontService
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(tags=['AI Mapping'])

@router.post('/fonts/{font_id}/generate-ai-suggestions')
async def generate_ai_suggestions(font_id: int, db: Session = Depends(get_db)):
    """Generate AI suggestions for all unmapped glyphs in a font using existing rendered previews"""
    
    font_file = db.query(FontFile).filter(FontFile.id == font_id).first()
    if not font_file:
        raise HTTPException(status_code=404, detail='Font not found')
    
    unmapped_glyphs = db.query(Glyph).filter(
        Glyph.font_file_id == font_id,
        Glyph.mapping == '',
        Glyph.rendered_preview.isnot(None)
    ).all()
    
    if not unmapped_glyphs:
        return {
            'message': 'No unmapped glyphs with previews found', 
            'processed': 0,
            'errors': 0,
            'total_unmapped': 0,
            'font_id': font_id,
            'font_name': font_file.font_name
        }
    
    processed = 0
    errors = 0
    
    # print(f"Processing {len(unmapped_glyphs)} unmapped glyphs for font '{font_file.font_name}'")
    
    for glyph in unmapped_glyphs:
        try:
            ai_char = FontService.get_ai_suggestion_for_png(glyph.rendered_preview)
            
            if ai_char and ai_char.strip():
                glyph.mapping = ai_char.strip()
                glyph.is_mapped = True
                processed += 1
                # print(f"  {glyph.codepoint} → '{ai_char}'")
            else:
                errors += 1
                # print(f"  {glyph.codepoint} → AI failed")
                
        except Exception as e:
            errors += 1
            # print(f"  {glyph.codepoint} → Error: {e}")
    
    db.commit()
    
    # print(f"AI processing complete: {processed} processed, {errors} errors")
    
    return {
        'font_id': font_id,
        'font_name': font_file.font_name,
        'processed': processed,
        'errors': errors,
        'total_unmapped': len(unmapped_glyphs),
        'success_rate': round((processed / len(unmapped_glyphs)) * 100, 1) if unmapped_glyphs else 0,
        'message': f'AI processed {processed} out of {len(unmapped_glyphs)} unmapped glyphs'
    }