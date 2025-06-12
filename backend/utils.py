import re
import base64

try:
    from fontTools.ttLib import TTFont
    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False


def extract_font_references(svg_content: str):
    pattern = r'font-family[:\s=]*["\']?([^"\';\s>]+)["\']?'
    matches = re.findall(pattern, svg_content, re.IGNORECASE)
    generic_fonts = {'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy'}
    unique_fonts = []
    seen = set()
    for font in matches:
        font = font.strip()
        if font and font not in generic_fonts and font not in seen:
            unique_fonts.append(font)
            seen.add(font)
    return unique_fonts


def generate_glyphs_from_font(db, font_file_id: int, font_path: str):
    if not FONTTOOLS_AVAILABLE:
        print(f"Warning: fonttools not available for {font_path}")
        return

    try:
        font = TTFont(font_path)
        cmap = font.getBestCmap()
        reverse_cmap = {glyph_name: unicode_val for unicode_val, glyph_name in cmap.items()}
        glyph_set = font.getGlyphSet()

        for glyph_name in glyph_set.keys():
            if glyph_name == '.notdef':
                continue

            if glyph_name in reverse_cmap:
                unicode_val = reverse_cmap[glyph_name]
                try:
                    character = chr(unicode_val)
                    if unicode_val in [0, 0x0D, 0x0A]:
                        continue
                except ValueError:
                    character = f"[{glyph_name}]"
                codepoint = f"U+{unicode_val:04X}"
                display_text = character
            else:
                character = f"[{glyph_name}]"
                codepoint = f"[{glyph_name}]"
                display_text = glyph_name[:8]

            if len(display_text) > 8:
                display_text = display_text[:6] + "..."

            svg_data = f"""<svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6"/>
                <text x="24" y="24" text-anchor="middle" font-family="serif" font-size="14" fill="#212529">{display_text}</text>
                <text x="24" y="42" text-anchor="middle" font-size="6" fill="#6c757d">{codepoint[:12]}</text>
            </svg>"""
            preview_b64 = base64.b64encode(svg_data.encode()).decode()

            from .models import Glyph  # if moved to utils.py

            glyph = Glyph(
                font_file_id=font_file_id,
                codepoint=codepoint,
                preview_image=f"data:image/svg+xml;base64,{preview_b64}",
                mapping="",
                is_mapped=False
            )
            db.add(glyph)

        font.close()
        db.commit()
    except Exception as e:
        print(f"Error processing font {font_path}: {e}")