import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { PageContainer } from '../components/layout/PageContainer';
import { Navbar as UploadNavbar } from '../components/Navbar';
import { AppLayout } from '../components/layout/AppLayout';
import { DashboardView } from '../views/DashboardView';
import { UploadView } from '../views/UploadView';
import { DocumentWorkspace } from '../components/workspace/DocumentWorkspace';
import { api } from '../services/api';
import { PDF_DOCUMENT } from './pdfFixtures';

vi.mock('react-pdf', async () => import('./pdfMock'));

beforeEach(() => {
  sessionStorage.clear();
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  vi.spyOn(api, 'getDocumentSummary').mockImplementation(() => new Promise(() => {}));
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it('uses one shared content frame when navigating between dashboard and upload', () => {
  const select = vi.fn();
  const view = render(
    <AppLayout activeTab="dashboard" onSelectTab={select} activeDoc={null}>
      <DashboardView documents={[]} onSelectDocument={vi.fn()} onNavigateUpload={select} />
    </AppLayout>,
  );
  const main = screen.getByRole('main');
  expect(screen.getAllByTestId('page-frame')).toHaveLength(1);
  expect(screen.getAllByTestId('page-container')).toHaveLength(1);
  expect(within(main).getByRole('heading', { name: 'Paper Library' })).toBeInTheDocument();
  fireEvent.click(within(screen.getByRole('navigation', { name: 'Main Navigation' })).getByRole('button', { name: 'Upload Paper' }));
  expect(select).toHaveBeenCalledWith('upload');

  view.rerender(
    <AppLayout activeTab="upload" onSelectTab={select} activeDoc={null}>
      <UploadView onUploadSuccess={vi.fn()} />
    </AppLayout>,
  );
  expect(screen.getAllByTestId('page-frame')).toHaveLength(1);
  expect(screen.getAllByTestId('page-container')).toHaveLength(1);
  expect(screen.getByTestId('page-container')).toContainElement(screen.getByRole('heading', { name: 'Upload a research paper' }));
  expect(screen.getByTestId('page-container')).toContainElement(screen.getByTestId('main-upload-trigger'));
  const uploadColumn = screen.getByRole('heading', { name: 'Upload a research paper' }).parentElement?.parentElement;
  expect(uploadColumn).toHaveClass('max-w-5xl');
  expect(uploadColumn).toContainElement(screen.getByTestId('main-upload-trigger'));
  expect(screen.queryByRole('heading', { name: 'Paper Library' })).not.toBeInTheDocument();
  expect(screen.queryByRole('region', { name: 'PDF pane' })).not.toBeInTheDocument();
});

it('keeps workspace panes in one shared frame and preserves tab switching', async () => {
  await act(async () => {
    render(
      <AppLayout activeTab="workspace" onSelectTab={vi.fn()} activeDoc={PDF_DOCUMENT}>
        <DocumentWorkspace document={PDF_DOCUMENT} />
      </AppLayout>,
    );
  });
  expect(screen.getAllByRole('main')).toHaveLength(1);
  expect(screen.getAllByTestId('page-container')).toHaveLength(1);
  expect(screen.getAllByTestId('page-frame')).toHaveLength(1);
  const content = screen.getByTestId('page-container');
  expect(content).toHaveClass('max-w-[1440px]');
  expect(screen.getByTestId('navigation-container')).toHaveClass('max-w-[1440px]');
  expect(content).toContainElement(screen.getByRole('region', { name: 'Summary and chat' }));
  expect(screen.queryByRole('region', { name: 'Original PDF' })).not.toBeInTheDocument();
  expect(screen.queryByTestId('pdf-viewer-panel')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('tab', { name: 'AI Chatbot' }));
  expect(screen.getByRole('textbox', { name: 'Question' })).toBeInTheDocument();
  expect(screen.getAllByTestId('page-container')).toHaveLength(1);
});

it('uses the same application boundary for Dashboard and Upload navigation', () => {
  const view = render(<AppLayout activeTab="dashboard" onSelectTab={vi.fn()} activeDoc={PDF_DOCUMENT}><PageContainer>Dashboard</PageContainer></AppLayout>);
  expect(screen.getByTestId('navigation-container')).toHaveClass('max-w-[1440px]');
  expect(screen.getByTestId('page-container')).toHaveClass('max-w-[1440px]');
  view.rerender(<AppLayout activeTab="upload" onSelectTab={vi.fn()} activeDoc={PDF_DOCUMENT}><PageContainer>Upload</PageContainer></AppLayout>);
  expect(screen.getByTestId('navigation-container')).toHaveClass('max-w-[1440px]');
  expect(screen.getByTestId('page-container')).toHaveClass('max-w-[1440px]');
});

it('aligns the upload-to-workspace shell header with the same wide Workspace boundary', () => {
  const view = render(<><UploadNavbar activeFilename={PDF_DOCUMENT.filename} /><PageContainer>Workspace</PageContainer></>);
  expect(screen.getByTestId('navigation-container')).toHaveClass('max-w-[1440px]');
  expect(screen.getByTestId('page-container')).toHaveClass('max-w-[1440px]');
  view.rerender(<><UploadNavbar /><PageContainer>Upload</PageContainer></>);
  expect(screen.getByTestId('navigation-container')).toHaveClass('max-w-[1440px]');
  expect(screen.getByTestId('page-container')).toHaveClass('max-w-[1440px]');
});

it('preserves real document counts, filtering and selection in the responsive library', () => {
  const select = vi.fn();
  const other: typeof PDF_DOCUMENT = {
    ...PDF_DOCUMENT, id: '507f1f77bcf86cd799439012', sha256: '2'.repeat(64),
    filename: 'other-research.pdf', status: 'PENDING',
  };
  render(<DashboardView documents={[PDF_DOCUMENT, other]} onSelectDocument={select} onNavigateUpload={vi.fn()} />);
  const stats = screen.getByRole('region', { name: 'Library statistics' });
  expect(within(stats).getByText('Total Research Papers').parentElement?.firstElementChild).toHaveTextContent('2');
  expect(within(stats).getByText('Ready to explore').parentElement?.firstElementChild).toHaveTextContent('1');
  expect(within(screen.getByRole('region', { name: 'Research papers' })).getAllByTestId('document-card')).toHaveLength(2);
  fireEvent.change(screen.getByRole('searchbox', { name: 'Search papers' }), { target: { value: 'synthetic' } });
  const cards = screen.getByRole('region', { name: 'Research papers' });
  expect(within(cards).getAllByTestId('document-card')).toHaveLength(1);
  fireEvent.click(within(cards).getByRole('button', { name: PDF_DOCUMENT.filename }));
  expect(select).toHaveBeenCalledWith(PDF_DOCUMENT);
  fireEvent.change(screen.getByRole('searchbox', { name: 'Search papers' }), { target: { value: 'missing-paper' } });
  expect(screen.getByRole('heading', { name: 'No matching papers found' })).toBeInTheDocument();
  expect(screen.queryByTestId('document-card')).not.toBeInTheDocument();
});
