import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  /** Workspace panels manage their own scrolling. */
  scrollable?: boolean;
  /** Wider boundary for the research Workspace; ordinary pages keep their existing width. */
  wide?: boolean;
}

export function PageContainer({ children, scrollable = true, wide = false }: Props) {
  return (
    <div data-testid="page-frame" className={'min-h-0 min-w-0 w-full flex-1 '
      + (scrollable ? 'overflow-y-auto' : 'flex flex-col overflow-hidden')}>
      <div data-testid="page-container" className={'mx-auto min-w-0 w-full px-4 sm:px-6 lg:px-8 '
        + (wide ? 'max-w-[1440px] ' : 'max-w-6xl ')
        + (scrollable ? 'py-6 sm:py-8' : 'flex min-h-0 flex-1 flex-col')}>
        {children}
      </div>
    </div>
  );
}
