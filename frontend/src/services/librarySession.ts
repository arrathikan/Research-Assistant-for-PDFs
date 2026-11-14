import type { NavigationTab, WorkspaceTab } from '../types';

export const LIBRARY_SESSION_KEY = 'researchai.library.v1';
export interface LibrarySession {
  ids: string[];
  activeId?: string;
  activeTab: NavigationTab;
  workspaceTab: WorkspaceTab;
}
const empty = (): LibrarySession => ({ ids: [], activeTab: 'dashboard', workspaceTab: 'summary' });

/** Store references only; restored metadata always comes from the API. */
export function readLibrarySession(): LibrarySession {
  try {
    const value = JSON.parse(sessionStorage.getItem(LIBRARY_SESSION_KEY) ?? 'null');
    if (!value || !Array.isArray(value.ids)) return empty();
    const ids = [...new Set<string>(value.ids.filter((id: unknown): id is string =>
      typeof id === 'string' && /^[0-9a-f]{24}$/i.test(id)))];
    return {
      ids, activeId: ids.includes(value.activeId) ? value.activeId : undefined,
      activeTab: ['dashboard', 'upload', 'workspace'].includes(value.activeTab) ? value.activeTab : 'dashboard',
      workspaceTab: value.workspaceTab === 'chat' ? 'chat' : 'summary',
    };
  } catch { return empty(); }
}

export function saveLibrarySession(session: LibrarySession): void {
  try { sessionStorage.setItem(LIBRARY_SESSION_KEY, JSON.stringify(session)); }
  catch { /* Optional browser storage must not prevent normal use. */ }
}
