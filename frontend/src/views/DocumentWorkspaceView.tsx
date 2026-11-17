import type { DocumentMetadata } from '../types';
import { DocumentWorkspace } from '../components/workspace/DocumentWorkspace';

export function DocumentWorkspaceView({ document }: { document: DocumentMetadata }) {
  return <DocumentWorkspace document={document} />;
}
