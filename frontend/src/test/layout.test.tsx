import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
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
  expect(screen.getByTestId('page-container')).toContainElement(screen.getByTestId('dropzone'));
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
  expect(content).toContainElement(screen.getByRole('region', { name: 'Summary and chat' }));
  expect(content).toContainElement(screen.getByRole('region', { name: 'PDF pane' }));
  expect(screen.getAllByTestId('pdf-viewer-panel')).toHaveLength(1);
  fireEvent.click(screen.getByRole('button', { name: 'AI Chatbot' }));
  expect(screen.getByRole('textbox', { name: 'Question' })).toBeInTheDocument();
  expect(screen.getAllByTestId('page-container')).toHaveLength(1);
});
