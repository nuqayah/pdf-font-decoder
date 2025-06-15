export interface SVGUploadResponse {
  file_id: number;
  filename: string;
  required_fonts: string[];
  message: string;
}

export interface FontUploadResponse {
  svg_file_id: number;
  uploaded_fonts: Array<{
    font_id: number;
    font_name: string;
    filename: string;
  }>;
  message: string;
}

export interface ZipUploadResponse {
  message: string;
  task_id: string;
  status: string;
  processed_svgs?: Array<{
    svg_file_id: number;
    filename: string;
    required_fonts: string[];
    matched_fonts: string[];
  }>;
  unmatched_fonts?: string[];
}

export interface UploadProgress {
  current: number;
  total: number;
  percentage: number;
  message: string;
  completed: boolean;
  result?: {
    processed_svgs: Array<{
      svg_file_id: number;
      filename: string;
      required_fonts: string[];
      matched_fonts: string[];
    }>;
    unmatched_fonts: string[];
  };
  error?: string;
}

export interface SVGListItem {
  svg_file_id: number;
  filename: string;
  upload_date: string;
}

export interface SVGListResponse {
  svgs: SVGListItem[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_items: number;
    items_per_page: number;
    has_next: boolean;
    has_previous: boolean;
  };
}

export interface Glyph {
  glyph_id: number;
  codepoint: string;
  preview_image: string;
  mapping: string;
  is_mapped: boolean;
}

export interface Font {
  font_id: number;
  font_name: string;
  filename: string;
  font_url: string;
  glyphs: Glyph[];
}

export interface FontsResponse {
  fonts: Font[];
}
