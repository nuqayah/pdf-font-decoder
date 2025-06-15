import base64
import uuid
import shutil
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database.models import FontFile, Glyph

try:
    from fontTools.ttLib import TTFont

    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False

# Upload directory setup
UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / 'fonts').mkdir(exist_ok=True)


class FontService:
    @staticmethod
    def generate_glyphs_from_font(db: Session, font_file_id: int, font_path: str):
        """Extract glyphs from a font file and store them in the database"""
        if not FONTTOOLS_AVAILABLE:
            print(f'Warning: fonttools not available, skipping glyph extraction for font {font_path}')
            return

        try:
            font = TTFont(font_path)

            cmap = font.getBestCmap()
            reverse_cmap = {glyph_name: unicode_val for unicode_val, glyph_name in cmap.items()}

            glyph_set = font.getGlyphSet()
            all_glyph_names = list(glyph_set.keys())

            print(f'Processing font with {len(all_glyph_names)} total glyphs ({len(cmap)} Unicode-mapped)')

            glyph_count = 0

            for glyph_name in all_glyph_names:
                if glyph_name == '.notdef':
                    continue

                if glyph_name in reverse_cmap:
                    unicode_val = reverse_cmap[glyph_name]
                    try:
                        character = chr(unicode_val)
                        if unicode_val in [0, 0x0D, 0x0A]:
                            continue
                    except ValueError:
                        character = f'[{glyph_name}]'
                    codepoint = f'U+{unicode_val:04X}'
                    display_text = character
                else:
                    character = f'[{glyph_name}]'
                    codepoint = f'[{glyph_name}]'
                    display_text = glyph_name[:8]

                if len(display_text) > 8:
                    display_text = display_text[:6] + '...'

                svg_data = f"""<svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6"/>
                    <text x="24" y="24" text-anchor="middle" font-family="serif" font-size="14" fill="#212529">{display_text}</text>
                    <text x="24" y="42" text-anchor="middle" font-size="6" fill="#6c757d">{codepoint[:12]}</text>
                </svg>"""

                preview_b64 = base64.b64encode(svg_data.encode()).decode()

                glyph = Glyph(
                    font_file_id=font_file_id,
                    codepoint=codepoint,
                    preview_image=f'data:image/svg+xml;base64,{preview_b64}',
                    mapping='',
                    is_mapped=False,
                )
                db.add(glyph)
                glyph_count += 1

            print(f'Extracted {glyph_count} glyphs from font (excluding .notdef)')

            font.close()
            db.commit()

        except Exception as e:
            print(f'Error processing font {font_path}: {e}')
            import traceback

            traceback.print_exc()

    @staticmethod
    def match_fonts_to_svg(required_fonts: List[str], available_fonts: List[Path]) -> List[Path]:
        """Match required fonts to available font files"""
        matched_fonts = []

        for font_file in available_fonts:
            font_filename = font_file.stem.lower()

            for required_font in required_fonts:
                required_font_lower = required_font.lower()

                if (
                    required_font_lower in font_filename
                    or font_filename in required_font_lower
                    or required_font_lower.replace(' ', '') == font_filename.replace(' ', '')
                ):
                    matched_fonts.append(font_file)
                    break

        return matched_fonts

    @staticmethod
    def save_font_file(file_content: bytes, filename: str, svg_file_id: int, db: Session) -> Dict[str, Any]:
        """Save uploaded font file and process glyphs"""
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / 'fonts' / f'{file_id}_{filename}'

        # Save file to disk
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Extract font name
        font_name = Path(filename).stem

        # Store font in database
        db_font = FontFile(
            svg_file_id=svg_file_id,
            font_name=font_name,
            filename=filename,
            upload_path=str(file_path),
        )
        db.add(db_font)
        db.commit()

        # Process glyphs
        FontService.generate_glyphs_from_font(db, db_font.id, str(file_path))

        return {'font_id': db_font.id, 'font_name': font_name, 'filename': filename}

    @staticmethod
    def process_font_from_zip(font_file: Path, svg_file_id: int, db: Session) -> Dict[str, Any]:
        """Process font file from ZIP extraction"""
        # Create unique file path for font
        font_file_id = str(uuid.uuid4())
        final_font_path = UPLOAD_DIR / 'fonts' / f'{font_file_id}_{font_file.name}'

        # Copy font to final location
        shutil.copy(font_file, final_font_path)

        # Extract font name
        font_name = font_file.stem

        # Store font in database
        db_font = FontFile(
            svg_file_id=svg_file_id,
            font_name=font_name,
            filename=font_file.name,
            upload_path=str(final_font_path),
        )
        db.add(db_font)
        db.commit()

        # Process glyphs
        FontService.generate_glyphs_from_font(db, db_font.id, str(final_font_path))

        return {'font_id': db_font.id, 'font_name': font_name, 'filename': font_file.name}
