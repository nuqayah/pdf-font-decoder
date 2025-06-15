from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import Glyph

router = APIRouter(tags=['Glyphs'])


@router.put('/glyph/{glyph_id}/mapping')
async def update_glyph_mapping(glyph_id: int, mapping_data: dict, db: Session = Depends(get_db)):
    """Update glyph mapping"""
    glyph = db.query(Glyph).filter(Glyph.id == glyph_id).first()
    if not glyph:
        raise HTTPException(status_code=404, detail='Glyph not found')

    glyph.mapping = mapping_data.get('mapping', '')
    glyph.is_mapped = bool(glyph.mapping.strip())
    db.commit()

    return {'glyph_id': glyph.id, 'mapping': glyph.mapping, 'is_mapped': glyph.is_mapped}
