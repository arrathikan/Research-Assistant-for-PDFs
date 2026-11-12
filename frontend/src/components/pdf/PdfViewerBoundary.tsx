import { Component, type ReactNode } from 'react';
import { api } from '../../services/api';

/** A failed optional code download must not take the research conversation with it. */
export class PdfViewerBoundary extends Component<{ children: ReactNode; documentId?: string }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (!this.state.failed) return this.props.children;
    return <div className="p-6">
      <p role="alert" className="text-sm leading-6 text-slate-700">The PDF viewer couldn’t open. You can still read the original in a new tab.</p>
      {this.props.documentId && <a className="ui-button ui-button-secondary mt-4" href={api.getPdfStreamUrl(this.props.documentId)} target="_blank" rel="noreferrer">Open original PDF<span className="sr-only"> (opens in a new tab)</span></a>}
    </div>;
  }
}
