import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, afterEach, describe, expect, test, vi } from 'vitest';
import AskTab from '../AskTab';
import { LanguageProvider } from '../../locales/LanguageContext';

const mockChips = [
  { id: 'what_is_koleroga', question: 'What is Mahali?' },
  { id: 'koleroga_prevent', question: 'How do I prevent Koleroga?' },
  { id: 'what_is_yld', question: 'What is Yellow Leaf Disease?' },
];

function renderAskTab(props = {}) {
  return render(
    <LanguageProvider language="en">
      <AskTab {...props} />
    </LanguageProvider>
  );
}

describe('AskTab Component', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    Element.prototype.scrollIntoView = vi.fn();
    vi.stubGlobal('fetch', vi.fn(async (path) => {
      if (typeof path === 'string' && path.includes('/api/chat/chips')) {
        return {
          ok: true,
          json: async () => ({ chips: mockChips }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          answer: 'Mahali is fruit rot of areca nut.',
          intent: 'faq',
          entry_id: 'what_is_koleroga',
          sources: [
            { id: 'S1', title: 'Extension Folder No. 17', publisher: 'CPCRI', year: '1989', url: 'https://example.com/s1' },
          ],
          refused: false,
          needs_expert_review: false,
          language_fallback: false,
          suggestions: [{ id: 's2', question: 'How does it spread?' }],
          ai_generated: false,
          answer_source: 'guide',
        }),
      };
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test('renders chips from API', async () => {
    renderAskTab();
    expect(await screen.findByRole('button', { name: 'What is Mahali?' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'How do I prevent Koleroga?' })).toBeInTheDocument();
  });

  test('send button is disabled when empty or whitespace', async () => {
    renderAskTab();
    const sendBtn = screen.getByRole('button', { name: /send/i });
    const input = screen.getByLabelText(/your question/i);

    expect(sendBtn).toBeDisabled();
    fireEvent.change(input, { target: { value: '   ' } });
    expect(sendBtn).toBeDisabled();
    fireEvent.change(input, { target: { value: 'Hello' } });
    expect(sendBtn).not.toBeDisabled();
  });

  test('enforces 300 character limit and shows live counter', () => {
    renderAskTab();
    const input = screen.getByLabelText(/your question/i);
    expect(input).toHaveAttribute('maxLength', '300');

    fireEvent.change(input, { target: { value: 'a'.repeat(25) } });
    expect(screen.getByText('25/300')).toBeInTheDocument();
  });

  test('shows answer and sources toggle', async () => {
    renderAskTab();
    const chip = await screen.findByRole('button', { name: 'What is Mahali?' });
    fireEvent.click(chip);

    expect(await screen.findByText('Mahali is fruit rot of areca nut.')).toBeInTheDocument();
    expect(screen.getAllByText('From the verified guide').length).toBeGreaterThanOrEqual(1);

    const toggle = screen.getByRole('button', { name: /sources/i });
    expect(toggle).toBeInTheDocument();
    expect(screen.queryByText('Extension Folder No. 17')).not.toBeInTheDocument();

    fireEvent.click(toggle);
    const link = screen.getByRole('link', { name: /Extension Folder No. 17/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', 'https://example.com/s1');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  test('shows expert-review badge when needs_expert_review is true', async () => {
    vi.stubGlobal('fetch', vi.fn(async (path) => {
      if (typeof path === 'string' && path.includes('/api/chat/chips')) {
        return { ok: true, json: async () => ({ chips: mockChips }) };
      }
      return {
        ok: true,
        json: async () => ({
          answer: 'Prevent Koleroga with Bordeaux spray.',
          intent: 'faq',
          entry_id: 'koleroga_prevent',
          sources: [],
          refused: false,
          needs_expert_review: true,
          language_fallback: false,
          suggestions: [],
          ai_generated: false,
          answer_source: 'guide',
        }),
      };
    }));

    renderAskTab();
    const chip = await screen.findByRole('button', { name: 'How do I prevent Koleroga?' });
    fireEvent.click(chip);

    expect(await screen.findByText(/Please confirm with your agricultural officer/i)).toBeInTheDocument();
  });

  test('shows language-fallback notice when language_fallback is true', async () => {
    vi.stubGlobal('fetch', vi.fn(async (path) => {
      if (typeof path === 'string' && path.includes('/api/chat/chips')) {
        return { ok: true, json: async () => ({ chips: mockChips }) };
      }
      return {
        ok: true,
        json: async () => ({
          answer: 'Mahali details in English.',
          intent: 'faq',
          entry_id: 'what_is_koleroga',
          sources: [],
          refused: false,
          needs_expert_review: false,
          language_fallback: true,
          suggestions: [],
          ai_generated: false,
          answer_source: 'guide',
        }),
      };
    }));

    renderAskTab();
    const input = screen.getByLabelText(/your question/i);
    fireEvent.change(input, { target: { value: 'ಕೊಳರೋಗ ಎಂದರೇನು?' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(await screen.findByText('Shown in English because the translation is not ready yet')).toBeInTheDocument();
    expect(screen.getByText('Mahali details in English.')).toBeInTheDocument();
  });

  test('shows error state on failed fetch and allows retry', async () => {
    let callCount = 0;
    vi.stubGlobal('fetch', vi.fn(async (path) => {
      if (typeof path === 'string' && path.includes('/api/chat/chips')) {
        return { ok: true, json: async () => ({ chips: mockChips }) };
      }
      callCount++;
      if (callCount === 1) {
        throw new Error('Network failure');
      }
      return {
        ok: true,
        json: async () => ({
          answer: 'Recovered answer.',
          intent: 'faq',
          entry_id: 'what_is_koleroga',
          sources: [],
          refused: false,
          needs_expert_review: false,
          language_fallback: false,
          suggestions: [],
        }),
      };
    }));

    renderAskTab();
    const input = screen.getByLabelText(/your question/i);
    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(await screen.findByText('Could not reach the app server. Try again.')).toBeInTheDocument();
    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);

    expect(await screen.findByText('Recovered answer.')).toBeInTheDocument();
  });

  test('clear chat empties messages and clears storage', async () => {
    renderAskTab();
    const chip = await screen.findByRole('button', { name: 'What is Mahali?' });
    fireEvent.click(chip);

    expect(await screen.findByText('Mahali is fruit rot of areca nut.')).toBeInTheDocument();
    const clearBtn = screen.getByRole('button', { name: /clear chat/i });
    fireEvent.click(clearBtn);

    expect(screen.queryByText('Mahali is fruit rot of areca nut.')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /clear chat/i })).not.toBeInTheDocument();
  });

  test('caps history at 30 messages', async () => {
    // Seed 30 messages
    const prefilled = Array.from({ length: 30 }, (_, i) => ({
      id: `m_${i}`,
      role: i % 2 === 0 ? 'user' : 'assistant',
      content: i % 2 === 0 ? `Message ${i}` : undefined,
      answer: i % 2 !== 0 ? `Answer ${i}` : undefined,
    }));
    sessionStorage.setItem('arecalens_chat_history_v1', JSON.stringify(prefilled));

    renderAskTab();
    expect(screen.getByText('Message 0')).toBeInTheDocument();

    const input = screen.getByLabelText(/your question/i);
    fireEvent.change(input, { target: { value: 'Brand new 31st message' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText('Brand new 31st message')).toBeInTheDocument();
    });
    // Oldest message (Message 0) dropped
    expect(screen.queryByText('Message 0')).not.toBeInTheDocument();
  });

  test('result chip appears only when a result exists and sends context advice', async () => {
    const { rerender } = renderAskTab({ result: null });
    expect(screen.queryByText(/About your last result/i)).not.toBeInTheDocument();

    const fakeResult = {
      class_id: 'Mahali_Koleroga',
      display_name: 'Mahali / Koleroga',
      status: 'suspected',
      confidence: 0.96,
    };
    const fakeInfo = {
      classes: {
        Mahali_Koleroga: { short_name: 'Mahali / Koleroga' },
      },
    };

    rerender(
      <LanguageProvider language="en">
        <AskTab result={fakeResult} info={fakeInfo} />
      </LanguageProvider>
    );

    const resultChip = await screen.findByRole('button', {
      name: /About your last result: Mahali \/ Koleroga/i,
    });
    expect(resultChip).toBeInTheDocument();

    fireEvent.click(resultChip);

    await waitFor(() => {
      const chatCall = fetch.mock.calls.find(([path]) => path === '/api/chat');
      expect(chatCall).toBeDefined();
      const body = JSON.parse(chatCall[1].body);
      expect(body.message).toBe('What should I do now?');
      expect(body.context).toEqual({
        class: 'Mahali_Koleroga',
        status: 'suspected',
        confidence: 0.96,
      });
      // CRITICAL: Ensure no photo is sent!
      expect(body.file).toBeUndefined();
      expect(body.image).toBeUndefined();
    });
  });
});
