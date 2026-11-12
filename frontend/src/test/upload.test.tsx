import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
      expect(screen.getByText('Upload paper')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Upload paper'));
    expect(onUpload).toHaveBeenCalledWith(validPdf);
  });

  it('renders loading spinner and disabled state during upload', () => {
    const onUpload = vi.fn();
    render(<UploadZone onUpload={onUpload} isUploading={true} />);

    expect(screen.getByText(/Uploading your paper…/i)).toBeInTheDocument();
    expect(screen.getByTestId('file-input')).toBeDisabled();
    expect(screen.getByTestId('dropzone')).toBeDisabled();
  });
});


it('supports drag and drop, empty-file validation, and exactly one PDF', () => {
  render(<UploadZone onUpload={vi.fn()} />);
  fireEvent.drop(screen.getByTestId('dropzone'), { dataTransfer: { files: [new File([], 'empty.pdf', { type: 'application/pdf' })] } });
  expect(screen.getByRole('alert')).toHaveTextContent('empty');
  const file = new File(['%PDF-1.7'], 'dropped.pdf');
  fireEvent.drop(screen.getByTestId('dropzone'), { dataTransfer: { files: [file, file] } });
  expect(screen.getByRole('alert')).toHaveTextContent('exactly one');
  fireEvent.drop(screen.getByTestId('dropzone'), { dataTransfer: { files: [file] } });
  expect(screen.getByText('dropped.pdf')).toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('provides a keyboard-focusable picker and allows removing/reselecting the same PDF', () => {
  render(<UploadZone onUpload={vi.fn()} />);
  const input = screen.getByTestId('file-input');
  const click = vi.spyOn(input, 'click');
  const picker = screen.getByTestId('dropzone');
  expect(picker.tagName).toBe('BUTTON');
  fireEvent.click(picker);
  expect(click).toHaveBeenCalledOnce();
  const file = new File(['pdf'], 'repeat.pdf', { type: 'application/pdf' });
  fireEvent.change(input, { target: { files: [file] } });
  fireEvent.click(screen.getByRole('button', { name: 'Remove selected PDF' }));
  expect(screen.queryByText('repeat.pdf')).not.toBeInTheDocument();
  fireEvent.change(input, { target: { files: [file] } });
  expect(screen.getAllByText('repeat.pdf')).toHaveLength(1);
});

it('prevents duplicate submissions while a request is pending', () => {
  const upload = vi.fn().mockImplementation(() => new Promise(() => {}));
  render(<UploadZone onUpload={upload} />);
  fireEvent.change(screen.getByTestId('file-input'), { target: { files: [new File(['pdf'], 'paper.pdf')] } });
  fireEvent.click(screen.getByRole('button', { name: 'Upload paper' }));
  fireEvent.click(screen.getByRole('button', { name: 'Upload paper' }));
  expect(upload).toHaveBeenCalledTimes(1);
});
