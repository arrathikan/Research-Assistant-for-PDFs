/**
 * Central API Client for ResearchAI.
 * Connects frontend with FastAPI Gateway REST endpoints.
 */

import {
  DocumentMetadata,
  DocumentStatus,
  ChatMessage,
  UploadResponse,
} from '../types';

import type { SummaryResponse } from '../types/summary';

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...options?.headers,
      },
    });

    if (!res.ok) {
      let errorMsg = `API request failed with status ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData?.detail) {
          errorMsg = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch {
        // Fallback to HTTP status text
      }
      throw new ApiError(res.status, errorMsg);
    }

    return (await res.json()) as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : 'Network error or backend unreachable';
    throw new ApiError(0, message);
  }
}

export const api = {
  /**
   * Check gateway service health.
   */
  async getHealth(): Promise<{ status: string; service: string }> {
    return request<{ status: string; service: string }>('/health');
  },

  /**
   * Upload an academic research PDF.
   * Validates MIME type and max size upfront.
   */
  async uploadDocument(file: File): Promise<UploadResponse> {
    if (!file.name.toLowerCase().endsWith('.pdf') || !['', 'application/pdf', 'application/octet-stream'].includes(file.type)) {
      throw new ApiError(400, 'Invalid file type: Only academic PDF documents (.pdf) are supported.');
    }

    if (file.size === 0) {
      throw new ApiError(400, 'The PDF file is empty.');
    }

    const maxSizeBytes = 25 * 1024 * 1024; // 25 MB
    if (file.size > maxSizeBytes) {
      throw new ApiError(413, 'File too large: Maximum supported size is 25 MB.');
    }

    const formData = new FormData();
    formData.append('file', file);

    return request<UploadResponse>('/documents', {
      method: 'POST',
      body: formData,
    });
  },

  /**
   * Poll ingestion status of a document.
   */
  async getDocumentStatus(documentId: string): Promise<{ document_id: string; status: DocumentStatus; error_message?: string }> {
    return request<{ document_id: string; status: DocumentStatus; error_message?: string }>(
      `/documents/${encodeURIComponent(documentId)}/status`
    );
  },

  /**
   * Fetch metadata of an uploaded document.
   */
  async getDocument(documentId: string): Promise<DocumentMetadata> {
    return request<DocumentMetadata>(`/documents/${encodeURIComponent(documentId)}`);
  },

  /**
   * Fetch 5-section structured summary.
   */
  async getDocumentSummary(documentId: string): Promise<SummaryResponse> {
    return request<SummaryResponse>(`/documents/${encodeURIComponent(documentId)}/summary`);
  },

  /**
   * Query document via Hybrid RAG chatbot.
   */
  async sendChatQuery(documentId: string, message: string): Promise<ChatMessage> {
    return request<ChatMessage>(`/documents/${encodeURIComponent(documentId)}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });
  },

  /**
   * Get direct PDF binary stream URL for viewer.
   */
  getPdfStreamUrl(documentId: string): string {
    return `${API_BASE_URL}/documents/${encodeURIComponent(documentId)}/pdf`;
  },
};
