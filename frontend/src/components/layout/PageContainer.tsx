import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  /** Workspace panels manage their own scrolling. */
  scrollable?: boolean;
}

export function PageContainer({ children, scrollable = true }: Props) {
  return (
    <div data-testid="page-frame" className={'min-h-0 min-w-0 w-full flex-1 '
      + (scrollable ? 'overflow-y-auto' : 'flex flex-col overflow-hidden')}>
      <div data-testid="page-container" className={'mx-auto min-w-0 w-full max-w-6xl px-4 sm:px-6 lg:px-8 '
        + (scrollable ? 'py-6 sm:py-8' : 'flex min-h-0 flex-1 flex-col')}>
        {children}
      </div>
    </div>
  );
}
