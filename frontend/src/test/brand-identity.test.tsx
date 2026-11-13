import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { AppLayout } from '../components/layout/AppLayout';
import { Navbar as UploadNavbar } from '../components/Navbar';

it('shares the supplied logo between both existing navigation shells', () => {
  const view = render(<AppLayout activeTab="dashboard" activeDoc={null} onSelectTab={vi.fn()}>Library</AppLayout>);
  const source = screen.getByTestId('brand-logo').querySelector('image')?.getAttribute('href');
  expect(source).toContain('researchai-logo.png');
  expect(screen.getByRole('button', { name: 'ResearchAI home' })).toBeInTheDocument();
  expect(screen.getByText('Academic Paper Assistant')).toBeInTheDocument();
  expect(screen.getByTestId('brand-logo')).toHaveAttribute('aria-hidden', 'true');
  view.rerender(<UploadNavbar />);
  expect(screen.getByTestId('brand-logo').querySelector('image')).toHaveAttribute('href', source);
});

it('updates the browser page title as the existing navigation changes', () => {
  const view = render(<AppLayout activeTab="dashboard" activeDoc={null} onSelectTab={vi.fn()}>Library</AppLayout>);
  expect(document.title).toBe('Paper Library | ResearchAI');
  view.rerender(<AppLayout activeTab="upload" activeDoc={null} onSelectTab={vi.fn()}>Upload</AppLayout>);
  expect(document.title).toBe('Upload Paper | ResearchAI');
  view.rerender(<AppLayout activeTab="workspace" activeDoc={null} onSelectTab={vi.fn()}>Workspace</AppLayout>);
  expect(document.title).toBe('Workspace | ResearchAI');
});
