import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { DocumentChatPanel } from '../components/chat/DocumentChatPanel';
import { api, ApiError } from '../services/api';
import type { ChatResponse } from '../types/chat';

const ID = '507f1f77bcf86cd799439011';
const RESULT: ChatResponse = { document_id: ID, conversation_id: 'b'.repeat(32), turn_id: 'c'.repeat(32), answer: 'Synthetic answer [1]', is_out_of_scope: false,
  citations: [{ document_id: ID, citation_id: 'd'.repeat(64), chunk_id: 'e'.repeat(64), page_number: 1, quote_snippet: 'Synthetic evidence.' }] };
beforeEach(() => { sessionStorage.clear(); });
afterEach(() => { vi.restoreAllMocks(); });
function send() {
  fireEvent.change(screen.getByRole('textbox', { name: 'Question' }), { target: { value: 'Synthetic question?' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send Message' }));
}

it('shows pending state then a sourced API answer', async () => {
  let finish: (value: ChatResponse) => void = () => {};
  const post = vi.spyOn(api, 'sendChatQuery').mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const cite = vi.fn();
  render(<DocumentChatPanel documentId={ID} onCitationClick={cite} />); send();
  expect(screen.getByText('Preparing your answer…')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Send Message' })).toBeDisabled();
  await act(async () => { finish(RESULT); });
  expect(screen.getByText('Synthetic answer', { exact: false })).toHaveTextContent(RESULT.answer);
  expect(screen.getByText('Synthetic evidence.')).not.toBeVisible();
  fireEvent.click(screen.getByText('Sources (1)'));
  fireEvent.click(screen.getByRole('button', { name: 'Page 1' }));
  expect(cite).toHaveBeenCalledWith(RESULT.citations[0]);
  expect(post).toHaveBeenCalledWith(ID, 'Synthetic question?', undefined);
});

it('reports failure without inventing an assistant response', async () => {
  vi.spyOn(api, 'sendChatQuery').mockRejectedValue(new ApiError(503, 'unavailable'));
  render(<DocumentChatPanel documentId={ID} />); send();
  expect(await screen.findByRole('alert')).toHaveTextContent('Chat is unavailable');
  expect(screen.queryByText(RESULT.answer)).not.toBeInTheDocument();
  expect(screen.getByRole('textbox', { name: 'Question' })).toHaveValue('Synthetic question?');
});

it('loads saved history without a paid send', async () => {
  sessionStorage.setItem(`researchai.chat.${ID}`, RESULT.conversation_id);
  vi.spyOn(api, 'getChatHistory').mockResolvedValue({ document_id: ID, conversation_id: RESULT.conversation_id,
    turns: [{ question: 'Earlier question', response: RESULT, created_at: '2026-11-11T00:00:00Z' }] });
  const post = vi.spyOn(api, 'sendChatQuery');
  render(<DocumentChatPanel documentId={ID} />);
  expect(await screen.findByText('Earlier question')).toBeInTheDocument();
  expect(screen.getByText('Synthetic answer', { exact: false })).toHaveTextContent(RESULT.answer);
  expect(post).not.toHaveBeenCalled();
});

it('ignores a late answer after switching documents', async () => {
  let finish: (value: ChatResponse) => void = () => {};
  vi.spyOn(api, 'sendChatQuery').mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const view = render(<DocumentChatPanel documentId={ID} />); send();
  view.rerender(<DocumentChatPanel documentId="507f1f77bcf86cd799439012" />);
  await act(async () => { finish(RESULT); });
  expect(screen.queryByText(RESULT.answer)).not.toBeInTheDocument();
  expect(screen.queryByText('Synthetic question?')).not.toBeInTheDocument();
});

it('rejects a response from another document', async () => {
  vi.spyOn(api, 'sendChatQuery').mockResolvedValue({ ...RESULT, document_id: '507f1f77bcf86cd799439012' });
  render(<DocumentChatPanel documentId={ID} />); send();
  expect(await screen.findByRole('alert')).toBeInTheDocument();
  expect(screen.queryByText(RESULT.answer)).not.toBeInTheDocument();
});

it('displays insufficient-evidence answers without invented sources', async () => {
  vi.spyOn(api, 'sendChatQuery').mockResolvedValue({ ...RESULT, is_out_of_scope: true, answer: 'Insufficient evidence in this paper.', citations: [] });
  render(<DocumentChatPanel documentId={ID} />); send();
  expect(await screen.findByText('Insufficient evidence in this paper.')).toBeInTheDocument();
  expect(screen.queryByText('Source: Page 1')).not.toBeInTheDocument();
});

it('opens inline citations while keeping supporting passages optional', async () => {
  vi.spyOn(api, 'sendChatQuery').mockResolvedValue({ ...RESULT, answer: 'Supported [1]. Unknown [9]. <img src=x>' });
  const cite = vi.fn();
  render(<DocumentChatPanel documentId={ID} onCitationClick={cite} />); send();
  fireEvent.click(await screen.findByRole('button', { name: 'Open citation 1, page 1' }));
  expect(screen.getByText('Synthetic evidence.')).not.toBeVisible();
  fireEvent.click(screen.getByText('Sources (1)'));
  fireEvent.click(screen.getByRole('button', { name: 'Page 1' }));
  expect(cite).toHaveBeenCalledTimes(2);
  expect(cite).toHaveBeenLastCalledWith(RESULT.citations[0]);
  expect(screen.queryByRole('button', { name: /citation 9/ })).not.toBeInTheDocument();
  expect(screen.getByText(/Unknown \[9\]/)).toHaveTextContent('<img src=x>');
  expect(document.querySelector('img')).toBeNull();
});
