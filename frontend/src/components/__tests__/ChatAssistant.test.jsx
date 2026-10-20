import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ChatAssistant from '../ChatAssistant';
import { LanguageProvider } from '../../locales/LanguageContext';

function renderAssistant() {
  return render(<LanguageProvider language="en"><ChatAssistant/></LanguageProvider>);
}

test('chat uses offline mode by default and sends a question to the local endpoint', async () => {
  vi.stubGlobal('fetch', vi.fn(async (path, options) => ({
    ok: true,
    json: async () => path === '/api/chat/status'
      ? { online_available: false }
      : { answer: 'The heatmap does not confirm disease.' },
  })));
  renderAssistant();
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  fireEvent.click(await screen.findByRole('button', { name: 'What does the heatmap show?' }));
  expect(await screen.findByText('The heatmap does not confirm disease.')).toBeInTheDocument();
  const call = fetch.mock.calls.find(([path]) => path === '/api/chat');
  expect(JSON.parse(call[1].body)).toEqual({
    message: 'What does the heatmap show?',
    mode: 'offline',
    language: 'en',
    history: [],
  });
});

test('chat history and follow-up suggestions remain after closing and reopening', async () => {
  vi.stubGlobal('fetch', vi.fn(async (path, options) => ({
    ok: true,
    json: async () => path === '/api/chat/status'
      ? { online_available: false }
      : { answer: 'The heatmap does not confirm disease.' },
  })));
  renderAssistant();
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  fireEvent.click(await screen.findByRole('button', { name: 'What does the heatmap show?' }));
  expect(await screen.findByText('The heatmap does not confirm disease.')).toBeInTheDocument();
  expect(screen.getByRole('group', { name: 'Suggested questions' })).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Close chat' }));
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  expect(screen.getByText('The heatmap does not confirm disease.')).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText('Your question'), { target: { value: 'Why is that?' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send question' }));
  await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/chat', expect.objectContaining({
    body: expect.stringContaining('"message":"Why is that?"'),
  })));
  const followupCall = fetch.mock.calls.filter(([path]) => path === '/api/chat')[1];
  expect(JSON.parse(followupCall[1].body).history).toEqual([
    { role: 'user', content: 'What does the heatmap show?' },
    { role: 'assistant', content: 'The heatmap does not confirm disease.' },
  ]);
});

test('online mode remains unavailable unless the server reports it configured', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ online_available: false }) })));
  renderAssistant();
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Online AI' })).toBeDisabled());
  expect(screen.getAllByText('Offline').length).toBeGreaterThan(0);
});

test('online mode sends the question and recent turns only after configured status', async () => {
  vi.stubGlobal('fetch', vi.fn(async (path, options) => ({
    ok: true,
    json: async () => path === '/api/chat/status'
      ? { online_available: true }
      : { answer: 'Online answer.' },
  })));
  renderAssistant();
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Online AI' }));
  fireEvent.change(screen.getByLabelText('Your question'), { target: { value: 'Explain arecanut care.' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send question' }));
  expect(await screen.findByText('Online answer.')).toBeInTheDocument();
  const call = fetch.mock.calls.find(([path]) => path === '/api/chat');
  expect(JSON.parse(call[1].body)).toMatchObject({
    message: 'Explain arecanut care.',
    mode: 'online',
    language: 'en',
    history: [],
  });
  expect(screen.getByText(/Your question, recent chat turns, and relevant guide text/)).toBeInTheDocument();
});
