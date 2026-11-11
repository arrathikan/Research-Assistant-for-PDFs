import { useEffect, type ReactNode } from 'react';
export const pdfjs = { GlobalWorkerOptions: { workerSrc: '' }, version: '3.11.174' };
export const pdfMock = { pages: 3, fail: false, text: 'Synthetic evidence.' };
interface DocumentProps { file: string; children: ReactNode; onLoadSuccess: (pdf: { numPages: number }) => void; onLoadError: () => void; error: ReactNode; }
export function Document({ file, children, onLoadSuccess, onLoadError, error }: DocumentProps) {
  useEffect(() => {
    let active = true;
    void Promise.resolve().then(() => { if (active) { if (pdfMock.fail) onLoadError(); else onLoadSuccess({ numPages: pdfMock.pages }); } });
    return () => { active = false; };
  }, [file, onLoadSuccess]);
  return <div data-testid="pdf-document" data-file={file}>{pdfMock.fail ? error : children}</div>;
}
interface PageProps { pageNumber: number; width: number; onLoadSuccess: (page: unknown) => void; onRenderSuccess: () => void; onRenderTextLayerSuccess: () => void; }
export function Page({ pageNumber, width, onLoadSuccess, onRenderSuccess, onRenderTextLayerSuccess }: PageProps) {
  useEffect(() => {
    onLoadSuccess({ pageNumber, rotate: 0, view: [0, 0, 600, 800], userUnit: 1, getViewport: () => ({ width: 600, height: 800 }) });
    onRenderSuccess(); onRenderTextLayerSuccess();
  }, [pageNumber, width, onLoadSuccess, onRenderSuccess, onRenderTextLayerSuccess]);
  return <div data-testid="pdf-page" data-page={pageNumber} style={{ width }}><canvas /><div className="react-pdf__Page__textContent"><span>{pdfMock.text}</span></div></div>;
}
