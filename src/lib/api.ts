import type {
  FontsResponse,
  FontUploadResponse,
  SVGListResponse,
  SVGUploadResponse,
  UploadProgress,
  ZipUploadResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async uploadSvg(file: File): Promise<SVGUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/upload-svg`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  }

  async uploadZip(file: File): Promise<ZipUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/upload-zip`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  }

  async getUploadProgress(taskId: string): Promise<UploadProgress> {
    const response = await fetch(`${this.baseUrl}/upload-progress/${taskId}`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  }

  async getSvgs(page: number = 1, limit: number = 50): Promise<SVGListResponse> {
    const response = await fetch(`${this.baseUrl}/svgs?page=${page}&limit=${limit}`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  }

  async uploadFonts(svgFileId: number, files: File[]): Promise<FontUploadResponse> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await fetch(`${this.baseUrl}/upload-fonts/${svgFileId}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  }

  async getFonts(svgFileId: number): Promise<FontsResponse> {
    const response = await fetch(`${this.baseUrl}/fonts/${svgFileId}`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  }

  async updateGlyphMapping(glyphId: number, mapping: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/glyph/${glyphId}/mapping`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mapping }),
    });

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  }

  async getSourceOfTruthSvg(svgFileId: number): Promise<{ source_of_truth_content: string }> {
    const response = await fetch(`${this.baseUrl}/svg/${svgFileId}/source-of-truth`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  }

  getFontFileUrl(fontId: number): string {
    return `${this.baseUrl}/font-file/${fontId}`;
  }
}

export const apiClient = new APIClient();
