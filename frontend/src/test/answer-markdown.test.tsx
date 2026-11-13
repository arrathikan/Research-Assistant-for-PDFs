import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { CitedAnswer } from '../components/chat/CitedAnswer';
import { PDF_CITATION } from './pdfFixtures';

it('renders structured summaries, emphasis and lists with accurate inline citations', () => {
  const open = vi.fn();
  render(<CitedAnswer answer={'## Findings\n\nThe result is **important** [1].\n\n- First finding\n- Second finding\n\n1. Read\n2. Compare'} citations={[PDF_CITATION]} onCitationClick={open} />);
  expect(screen.getByRole('heading', { name: 'Findings' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Open citation 1, page 2' })).toHaveTextContent('[Page 2]');
  expect(screen.getByText('important').tagName).toBe('STRONG');
  expect(screen.getAllByRole('list')).toHaveLength(2);
  expect(screen.getAllByRole('listitem')).toHaveLength(4);
  fireEvent.click(screen.getByRole('button', { name: 'Open citation 1, page 2' }));
  expect(open).toHaveBeenCalledWith(PDF_CITATION);
});

it('renders comparison tables without injecting HTML or model links', () => {
  render(<CitedAnswer answer={'| Group | Finding |\n| --- | --- |\n| A | Same outcome |\n| B | Not reported |\n\n<script>alert(1)</script> [unsafe](javascript:alert(1)) [9]'} citations={[]} />);
  expect(screen.getByRole('table')).toBeInTheDocument();
  expect(screen.getAllByRole('columnheader')).toHaveLength(2);
  expect(screen.getAllByRole('row')).toHaveLength(3);
  expect(document.querySelector('script')).toBeNull();
  expect(screen.queryByRole('link')).not.toBeInTheDocument();
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
});

it('keeps code literal and never turns unknown references into source links', () => {
  render(<CitedAnswer answer={'```\n<img src=x> [1]\n```\n\nUnknown [8].'} citations={[PDF_CITATION]} onCitationClick={vi.fn()} />);
  expect(document.querySelector('pre code')).toHaveTextContent('<img src=x> [1]');
  expect(document.querySelector('img')).toBeNull();
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
});
