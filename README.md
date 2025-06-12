# SVG Font Analyzer

A web application for analyzing SVG files with obfuscated fonts and mapping glyphs to readable characters. Upload SVG files along with their font files, then interactively map each glyph to its corresponding character for decoding obfuscated text.

## Features

- **Individual File Upload**: Upload SVG files with their required font files
- **Bulk ZIP Processing**: Upload ZIP files containing multiple SVGs and fonts with automatic matching
- **Real-time Glyph Mapping**: Interactive interface for mapping font glyphs to characters
- **Live Preview**: See decoded text update in real-time as you map glyphs
- **Progress Tracking**: Monitor mapping completion across all fonts
- **Font Analysis**: Automatic extraction and preview of font glyphs using FontTools

## Architecture

### Backend (FastAPI + SQLAlchemy)

```
backend/
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── routers/                 # API endpoint organization
│   ├── svg.py               # SVG upload, ZIP processing, progress tracking
│   ├── fonts.py             # Font file upload and serving
│   └── glyphs.py            # Glyph mapping updates
├── services/                # Business logic layer
│   ├── font_service.py      # Font processing & glyph extraction
│   └── svg_service.py       # SVG analysis & ZIP processing
├── database/                # Data layer
│   ├── database.py          # SQLAlchemy configuration
│   └── models.py            # Database models (SVGFile, FontFile, Glyph)
└── uploads/                 # File storage
    ├── svg/                 # Uploaded SVG files
    └── fonts/               # Uploaded font files
```

### Frontend (Svelte 5 + TypeScript)

```
frontend/
├── .env                     # Environment configuration
├── src/
│   ├── App.svelte           # Main application component
│   ├── lib/
│   │   ├── api.ts           # Backend API client
│   │   ├── types.ts         # TypeScript interfaces
│   │   └── components/      # Reusable UI components
│   │       ├── FileUpload.svelte     # Individual file upload
│   │       ├── ZipUpload.svelte      # Bulk ZIP upload
│   │       ├── SVGSelector.svelte    # SVG selection from ZIP
│   │       ├── GlyphEditor.svelte    # Glyph mapping interface
│   │       ├── SourceOfTruth.svelte  # Raw SVG display
│   │       ├── LivePreview.svelte    # Decoded SVG preview
│   │       └── ui/                   # shadcn-svelte components
└── package.json
```

## Application Flow

### 1. Upload Phase

#### Individual Upload:

1. User uploads an SVG file
2. System extracts font-family references from SVG content
3. User uploads matching font files (.woff, .woff2)
4. System processes fonts and extracts glyphs using FontTools
5. Proceeds to mapping interface

#### ZIP Upload:

1. User uploads ZIP file containing SVGs and fonts
2. Background processing extracts and analyzes all files
3. System automatically matches fonts to SVG requirements
4. User selects which SVG to work with (if multiple)
5. Proceeds to mapping interface

### 2. Mapping Phase

**Three-Panel Interface:**

- **Source of Truth (Left)**: Shows raw SVG with obfuscated symbols
- **Live Preview (Center)**: Shows decoded SVG that updates as glyphs are mapped
- **Glyph Editor (Right)**: Interactive mapping interface

**Mapping Process:**

1. System displays all glyphs from uploaded fonts with preview images
2. User maps each glyph to its corresponding character
3. Live preview updates in real-time showing decoded text
4. Progress bar tracks completion percentage
5. Bulk mapping tools available for efficiency

## Data Flow

### Database Models

- **SVGFile**: Stores SVG content and metadata
- **FontFile**: Links to SVG files, stores font metadata
- **Glyph**: Individual font glyphs with user mappings

### API Endpoints

- `POST /upload-svg` - Upload single SVG file
- `POST /upload-zip` - Upload ZIP file for bulk processing
- `GET /upload-progress/{task_id}` - Track ZIP processing progress
- `POST /upload-fonts/{svg_file_id}` - Upload font files for SVG
- `GET /fonts/{svg_file_id}` - Get fonts and glyphs for SVG
- `PUT /glyph/{glyph_id}/mapping` - Update glyph mapping
- `GET /font-file/{font_id}` - Serve font files to browser
- `GET /svg/{svg_file_id}/source-of-truth` - Get SVG with fixed font URLs
- `GET /svgs` - List all processed SVG files

## Quick Start

### Prerequisites

- Node.js v18+
- Python 3.9+
- pnpm (or npm)

### Environment Configuration

The frontend requires an environment file to configure the API endpoint:

**frontend/.env:**

```
VITE_API_URL=http://localhost:8000
```

This file configures the frontend to communicate with the backend API server. Make sure the URL matches your backend server configuration.

### Installation & Startup

```bash
# Clone the repository
git clone <repository-url>
cd svg-font-analyzer

# Start both frontend and backend
./start.sh
```

The start script will:

1. Check prerequisites
2. Create Python virtual environment
3. Install backend dependencies
4. Start FastAPI backend server (port 8000)
5. Install frontend dependencies
6. Start Svelte development server (port 5173)

### Manual Setup (Alternative)

**Backend:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
pnpm install
pnpm run dev
```

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage Guide

### Individual File Upload

1. Select "Individual Files" tab
2. Upload an SVG file (drag & drop or click to browse)
3. System will detect required fonts and show them
4. Upload matching font files (.woff/.woff2)
5. Wait for processing to complete
6. Use the glyph editor to map characters

### Bulk ZIP Upload

1. Select "ZIP Upload (Bulk)" tab
2. Upload a ZIP file containing SVGs and fonts
3. Monitor progress as files are processed
4. Select which SVG to work with
5. Use the glyph editor to map characters

### Glyph Mapping

- Each glyph shows a preview image and Unicode codepoint
- Type characters in the mapping field for each glyph
- Use arrow keys or Enter to navigate between fields
- Watch live preview update as you map glyphs
- Use "Bulk Fill" for mapping multiple glyphs at once

## Technical Details

### Font Processing

- Uses Python FontTools library for font analysis
- Extracts all glyphs with Unicode mappings
- Generates SVG preview images for each glyph
- Supports .woff, .woff2, .ttf, and .otf formats

### Background Processing

- ZIP uploads processed in background threads
- Real-time progress updates via polling
- Automatic font-to-SVG matching based on filename similarity
- Handles complex ZIP structures with nested folders

### Font URL Replacement

- SVG font URLs automatically replaced with backend endpoints
- Enables proper font loading in browser previews
- Maintains font-family references while fixing paths

## Dependencies

### Backend

- **FastAPI**: Web framework
- **SQLAlchemy**: ORM and database management
- **FontTools**: Font file processing
- **Pillow**: Image processing
- **python-multipart**: File upload handling

### Frontend

- **Svelte 5**: Reactive UI framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **shadcn-svelte**: UI component library
- **Lucide Svelte**: Icons
