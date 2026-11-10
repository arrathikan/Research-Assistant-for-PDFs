import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { UploadZone } from '../components/upload/UploadZone';

describe('UploadZone Component', () => {
  it('renders upload instructions and initial dropzone state', () => {
    const onUpload = vi.fn();
    render(<UploadZone onUpload={onUpload} />);

    expect(screen.getByText(/Drag & Drop your research paper here/i)).toBeInTheDocument();
    expect(screen.getByText(/PDF format only/i)).toBeInTheDocument();
    expect(screen.getByText(/Max 25 MB/i)).toBeInTheDocument();
  });

  it('rejects non-PDF files with a validation error', async () => {
    const onUpload = vi.fn();
    render(<UploadZone onUpload={onUpload} />);

    const fileInput = screen.getByTestId('file-input');
    const invalidFile = new File(['dummy text content'], 'report.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });

    fireEvent.change(fileInput, { target: { files: [invalidFile] } });

    await waitFor(() => {
      expect(
        screen.getByText(/Invalid file format. Please upload an academic research paper in PDF format./i)
      ).toBeInTheDocument();
    });
    expect(onUpload).not.toHaveBeenCalled();
  });

  it('rejects files larger than 25 MB with a clear error', async () => {
    const onUpload = vi.fn();
    render(<UploadZone onUpload={onUpload} />);

    const fileInput = screen.getByTestId('file-input');
    // Create a mock oversized file (26 MB)
    const largeFile = new File(['x'.repeat(1024)], 'giant_paper.pdf', {
      type: 'application/pdf',
    });
    Object.defineProperty(largeFile, 'size', { value: 26 * 1024 * 1024 });

    fireEvent.change(fileInput, { target: { files: [largeFile] } });

    await waitFor(() => {
      expect(
        screen.getByText(/exceeds maximum allowed limit of 25 MB/i)
      ).toBeInTheDocument();
    });
    expect(onUpload).not.toHaveBeenCalled();
  });

  it('accepts valid PDF file and displays the file details card with submit button', async () => {
    const onUpload = vi.fn().mockResolvedValue(undefined);
    render(<UploadZone onUpload={onUpload} />);

    const fileInput = screen.getByTestId('file-input');
    const validPdf = new File(['%PDF-1.4 sample content'], 'attention_is_all_you_need.pdf', {
      type: 'application/pdf',
    });

    fireEvent.change(fileInput, { target: { files: [validPdf] } });

    await waitFor(() => {
      expect(screen.getByText('attention_is_all_you_need.pdf')).toBeInTheDocument();
      expect(screen.getByText('Process Paper')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Process Paper'));
    expect(onUpload).toHaveBeenCalledWith(validPdf);
  });

  it('renders loading spinner and disabled state during upload', () => {
    const onUpload = vi.fn();
    render(<UploadZone onUpload={onUpload} isUploading={true} />);

    expect(screen.getByText(/Uploading and analyzing research PDF.../i)).toBeInTheDocument();
    expect(screen.getByText(/Computing SHA-256 hash & checking duplicates/i)).toBeInTheDocument();
  });
});
