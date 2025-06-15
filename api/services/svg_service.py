import re
import os
import uuid
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from fastapi import Request
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import SVGFile, FontFile
from services.font_service import FontService

# Upload directory setup
UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / 'svg').mkdir(exist_ok=True)

# Global progress storage (in production, use Redis or similar)
upload_progress: Dict[str, Dict[str, Any]] = {}

# Thread pool for background tasks
thread_pool = ThreadPoolExecutor(max_workers=4)


class SVGService:
    @staticmethod
    def extract_font_references(svg_content: str) -> List[str]:
        """Extract font-family references from SVG content"""
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

    @staticmethod
    def fix_font_urls_in_svg(svg_content: str, svg_file_id: int, db: Session, request: Request) -> str:
        """Replace font URLs in SVG with absolute URLs to backend endpoints"""
        base_url = str(request.base_url).rstrip('/')

        def replace_font_url(match):
            # Extract the full path from the url(), e.g., "fonts/my_font.woff"
            url_path = match.group(1)
            # Get just the filename, e.g., "my_font.woff"
            font_filename = os.path.basename(url_path)

            # Find the font in the database with an exact filename match for this SVG
            font_file = (
                db.query(FontFile)
                .filter(FontFile.svg_file_id == svg_file_id, FontFile.filename == font_filename)
                .first()
            )

            if font_file:
                # Replace with an absolute URL to the backend's font-serving endpoint
                absolute_url = f'{base_url}/font-file/{font_file.id}'
                return f'url("{absolute_url}")'

            # If no match is found, leave the original URL unchanged
            return match.group(0)

        # This regex finds all font URLs in the SVG content
        pattern = r'url\(["\']?([^"\')\s]+\.(woff2?|ttf|otf))["\']?\)'
        return re.sub(pattern, replace_font_url, svg_content, flags=re.IGNORECASE)

    @staticmethod
    def save_svg_file(file_content: bytes, filename: str, db: Session) -> Dict[str, Any]:
        """Save uploaded SVG file and extract font references"""
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / 'svg' / f'{file_id}_{filename}'

        # Save file to disk
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Decode content and extract font references
        svg_content = file_content.decode('utf-8')
        font_references = SVGService.extract_font_references(svg_content)

        # Store SVG in database
        db_svg = SVGFile(
            filename=filename,
            content=svg_content,
            upload_path=str(file_path),
        )
        db.add(db_svg)
        db.commit()

        return {'file_id': db_svg.id, 'filename': filename, 'required_fonts': font_references}

    @staticmethod
    def update_progress(task_id: str, current: int, total: int, message: str):
        """Update progress for a task"""
        upload_progress[task_id] = {
            'current': current,
            'total': total,
            'percentage': int((current / total) * 100) if total > 0 else 0,
            'message': message,
            'completed': current >= total,
        }

    @staticmethod
    def get_progress(task_id: str) -> Dict[str, Any]:
        """Get progress for a task"""
        return upload_progress.get(
            task_id, {'current': 0, 'total': 0, 'percentage': 0, 'message': 'Task not found', 'completed': False}
        )

    @staticmethod
    def process_zip_in_background(task_id: str, zip_content: bytes, filename: str):
        """Process ZIP file in background thread"""
        try:
            # Create a new database session for the background thread
            db = SessionLocal()

            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Save uploaded ZIP file
                zip_path = temp_path / 'upload.zip'
                SVGService.update_progress(task_id, 1, 100, 'Saving ZIP file...')

                with open(zip_path, 'wb') as f:
                    f.write(zip_content)

                # Extract ZIP file
                SVGService.update_progress(task_id, 5, 100, 'Extracting ZIP file...')
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_path)
                except zipfile.BadZipFile:
                    SVGService.update_progress(task_id, 100, 100, 'Error: Invalid ZIP file')
                    return

                SVGService.update_progress(task_id, 10, 100, 'Scanning for files...')

                # Find all SVG and font files, filtering out system/metadata files
                def is_valid_svg_file(file_path):
                    """Check if file is a valid SVG (not a system/metadata file)"""
                    filename = file_path.name
                    if filename.startswith('._') or filename.startswith('.') or '__MACOSX' in str(file_path):
                        return False
                    return filename.lower().endswith('.svg')

                def is_valid_font_file(file_path):
                    """Check if file is a valid font file (not a system/metadata file)"""
                    filename = file_path.name
                    if filename.startswith('._') or filename.startswith('.') or '__MACOSX' in str(file_path):
                        return False
                    return True

                all_svg_files = list(temp_path.rglob('*.svg'))
                svg_files = [f for f in all_svg_files if is_valid_svg_file(f)]

                all_font_files = (
                    list(temp_path.rglob('*.woff'))
                    + list(temp_path.rglob('*.woff2'))
                    + list(temp_path.rglob('*.ttf'))
                    + list(temp_path.rglob('*.otf'))
                )
                font_files = [f for f in all_font_files if is_valid_font_file(f)]

                if not svg_files:
                    skipped_count = len(all_svg_files) - len(svg_files)
                    message = (
                        f'Error: No valid SVG files found (skipped {skipped_count} system files)'
                        if skipped_count > 0
                        else 'Error: No SVG files found in ZIP'
                    )
                    SVGService.update_progress(task_id, 100, 100, message)
                    return

                SVGService.update_progress(
                    task_id, 15, 100, f'Found {len(svg_files)} SVG files and {len(font_files)} font files'
                )

                processed_svgs = []
                all_matched_fonts = set()

                # Process each SVG file
                for i, svg_file in enumerate(svg_files):
                    svg_progress = int(15 + (85 * i / len(svg_files)))
                    SVGService.update_progress(
                        task_id, svg_progress, 100, f'Processing SVG {i + 1}/{len(svg_files)}: {svg_file.name}'
                    )

                    try:
                        # Read SVG content with encoding handling
                        try:
                            svg_content = svg_file.read_text(encoding='utf-8')
                        except UnicodeDecodeError:
                            try:
                                svg_content = svg_file.read_text(encoding='latin-1')
                            except UnicodeDecodeError:
                                print(f"Error: Cannot decode SVG file '{svg_file.name}' - skipping")
                                continue

                        # Basic validation
                        if not ('<svg' in svg_content.lower() or 'xml' in svg_content.lower()):
                            print(f"Warning: File '{svg_file.name}' doesn't appear to be a valid SVG - skipping")
                            continue

                        # Extract required fonts
                        required_fonts = SVGService.extract_font_references(svg_content)

                        # Create unique file path for this SVG
                        file_id = str(uuid.uuid4())
                        final_svg_path = UPLOAD_DIR / 'svg' / f'{file_id}_{svg_file.name}'

                        # Copy SVG to final location
                        shutil.copy(svg_file, final_svg_path)

                        # Store SVG in database
                        db_svg = SVGFile(
                            filename=svg_file.name,
                            content=svg_content,
                            upload_path=str(final_svg_path),
                        )
                        db.add(db_svg)
                        db.commit()

                        # Match and process fonts
                        matched_fonts = FontService.match_fonts_to_svg(required_fonts, font_files)

                        # Track matched fonts
                        for font_file in matched_fonts:
                            all_matched_fonts.add(font_file.name)

                        processed_fonts = []
                        for font_file in matched_fonts:
                            try:
                                font_result = FontService.process_font_from_zip(font_file, db_svg.id, db)
                                processed_fonts.append(font_result)
                            except Exception as e:
                                print(f"Error processing font '{font_file.name}': {e}")
                                continue

                        # Get list of matched font names
                        matched_font_names = [font['font_name'] for font in processed_fonts]

                        processed_svgs.append(
                            {
                                'svg_file_id': db_svg.id,
                                'filename': svg_file.name,
                                'required_fonts': required_fonts,
                                'matched_fonts': matched_font_names,
                            }
                        )

                    except Exception as e:
                        print(f"Error processing SVG '{svg_file.name}': {e}")
                        continue

                # Find unmatched fonts
                unmatched_fonts = [f.name for f in font_files if f.name not in all_matched_fonts]

                # Store final result
                upload_progress[task_id] = {
                    'current': 100,
                    'total': 100,
                    'percentage': 100,
                    'message': f'Completed! Processed {len(processed_svgs)} SVG files',
                    'completed': True,
                    'result': {'processed_svgs': processed_svgs, 'unmatched_fonts': unmatched_fonts},
                }

        except Exception as e:
            print(f'Error in background processing: {e}')
            import traceback

            traceback.print_exc()
            upload_progress[task_id] = {
                'current': 100,
                'total': 100,
                'percentage': 100,
                'message': f'Error: {str(e)}',
                'completed': True,
                'error': str(e),
            }
        finally:
            db.close()

    @staticmethod
    def start_zip_processing(zip_content: bytes, filename: str) -> str:
        """Start background ZIP processing and return task ID"""
        task_id = str(uuid.uuid4())
        SVGService.update_progress(task_id, 0, 100, 'Starting processing...')
        thread_pool.submit(SVGService.process_zip_in_background, task_id, zip_content, filename)
        return task_id
