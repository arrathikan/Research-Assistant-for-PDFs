import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Navbar } from '../components/layout/Navbar';
import { DocumentMetadata } from '../types';

describe('Navbar Component', () => {
  const mockDoc: DocumentMetadata = {
    sha256: 'a1b2c3d4',
    filename: 'attention_is_all_you_need.pdf',
    file_size_bytes: 1048576,
    status: 'READY',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  it('renders brand and navigation links correctly', () => {
    const onSelectTab = vi.fn();
    render(
      <Navbar
        activeTab="dashboard"
        onSelectTab={onSelectTab}
        activeDoc={null}
      />
    );

    expect(screen.getByText('ResearchAI')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Upload Paper')).toBeInTheDocument();
    // Workspace button is hidden when no document is active
    expect(screen.queryByText('Workspace')).not.toBeInTheDocument();
  });

  it('displays active document filename, status badge, and workspace tab when document is selected', () => {
    const onSelectTab = vi.fn();
    render(
      <Navbar
        activeTab="workspace"
        onSelectTab={onSelectTab}
        activeDoc={mockDoc}
      />
    );

    expect(screen.getByText('attention_is_all_you_need.pdf')).toBeInTheDocument();
    expect(screen.getByTestId('document-status-pill')).toHaveTextContent('READY');
    expect(screen.getByText('Workspace')).toBeInTheDocument();
  });

  it('triggers onSelectTab callback on navigation button click', () => {
    const onSelectTab = vi.fn();
    render(
      <Navbar
        activeTab="dashboard"
        onSelectTab={onSelectTab}
        activeDoc={mockDoc}
      />
    );

    fireEvent.click(screen.getByText('Upload Paper'));
    expect(onSelectTab).toHaveBeenCalledWith('upload');

    fireEvent.click(screen.getByText('Workspace'));
    expect(onSelectTab).toHaveBeenCalledWith('workspace');
  });
});
