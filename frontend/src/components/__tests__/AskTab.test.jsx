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
      if (typeof path === 'string' && path.includes('/api/chat/status')) {
        return {
          ok: true,
          json: async () => ({ online_enabled: false }),
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
      if (typeof path === 'string' && path.includes('/api/chat/status')) {
        return { ok: true, json: async () => ({ online_enabled: false }) };
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

  test('after fallback reply chips appear exactly once, and normal FAQ answer has <= 3 follow-ups and no second starter row', async () => {
    const full7Chips = [
      { id: 'what_is_koleroga', question: 'What is Mahali?' },
      { id: 'koleroga_prevent', question: 'How do I prevent Koleroga?' },
      { id: 'what_is_yld', question: 'What is Yellow Leaf Disease?' },
      { id: 'yld_treatment', question: 'How to treat yellow leaf disease?' },
      { id: 'photo_tips', question: 'How do I take a good photo?' },
      { id: 'why_unsure', question: 'Why does it say not sure?' },
      { id: 'when_expert', question: 'When should I call an expert?' },
    ];

    vi.stubGlobal('fetch', vi.fn(async (path, opts) => {
      if (typeof path === 'string' && path.includes('/api/chat/chips')) {
        return {
          ok: true,
          json: async () => ({ chips: full7Chips }),
        };
      }
      const body = opts && opts.body ? JSON.parse(opts.body) : {};
      if (body.message === 'fallback query') {
        return {
          ok: true,
          json: async () => ({
            answer: "I can only answer questions about arecanut leaf and nut health from this app's verified guide.",
            intent: 'fallback',
            entry_id: 'fallback',
            sources: [],
            refused: false,
            needs_expert_review: false,
            language_fallback: false,
            suggestions: full7Chips,
            ai_generated: false,
            answer_source: 'guide',
          }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          answer: 'Mahali is fruit rot caused by Phytophthora meadii.',
          intent: 'faq',
          entry_id: 'what_is_koleroga',
          sources: [{ id: 'S1', title: 'Extension Folder No. 17', publisher: 'CPCRI', year: '1989', url: 'https://example.com/s1' }],
          refused: false,
          needs_expert_review: false,
          language_fallback: false,
          suggestions: [
            { id: 'f1', question: 'How to prevent Koleroga?' },
            { id: 'f2', question: 'Can Bordeaux mixture help?' },
          ],
          ai_generated: false,
          answer_source: 'guide',
        }),
      };
    }));

    renderAskTab();
    expect(await screen.findByRole('button', { name: 'What is Mahali?' })).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/Type your question/i);
    const sendButton = screen.getByRole('button', { name: /Send/i });

    // 1. Send fallback query
    fireEvent.change(input, { target: { value: 'fallback query' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/I can only answer questions/i)).toBeInTheDocument();
    });

    // Check that "What is Mahali?" and "When should I call an expert?" each appear exactly once
    const mahaliButtons = screen.getAllByRole('button', { name: 'What is Mahali?' });
    expect(mahaliButtons).toHaveLength(1);

    const expertButtons = screen.getAllByRole('button', { name: 'When should I call an expert?' });
    expect(expertButtons).toHaveLength(1);

    // 2. Send normal FAQ query
    fireEvent.change(input, { target: { value: 'What is Mahali?' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/caused by Phytophthora meadii/i)).toBeInTheDocument();
    });

    // After normal FAQ answer:
    // Only the latest bot message has suggestion chips (at most 3 follow-ups)
    const suggestionsGroup = document.querySelectorAll('.ask-suggestions-group');
    expect(suggestionsGroup).toHaveLength(1);
    const followUpButtons = suggestionsGroup[0].querySelectorAll('.ask-chip-button.suggestion');
    expect(followUpButtons.length).toBeLessThanOrEqual(3);

    // And no second starter row appears
    expect(document.querySelector('.ask-empty-state')).toBeNull();
    expect(document.querySelector('.fallback-chips')).toBeNull();
  });

  test('starter chip and follow-up chip clicks send entry_id and display user message', async () => {
    let capturedBody = null;
    vi.stubGlobal('fetch', vi.fn(async (path, opts) => {
      if (typeof path === 'string' && path.includes('/api/chat/chips')) {
        return { ok: true, json: async () => ({ chips: mockChips }) };
      }
      if (opts && opts.body) {
        capturedBody = JSON.parse(opts.body);
      }
      return {
        ok: true,
        json: async () => ({
          answer: 'Mahali is fruit rot of areca nut.',
          intent: 'faq',
          entry_id: 'what_is_koleroga',
          sources: [],
          refused: false,
          needs_expert_review: false,
          language_fallback: false,
          suggestions: [{ id: 'leaf_spot', question: 'What is leaf spot?' }],
        }),
      };
    }));

    renderAskTab();
    const chip = await screen.findByRole('button', { name: 'What is Mahali?' });
    fireEvent.click(chip);

    await waitFor(() => {
      expect(screen.getByText('What is Mahali?')).toBeInTheDocument();
      expect(capturedBody).toEqual(expect.objectContaining({
        message: 'What is Mahali?',
        entry_id: 'what_is_koleroga',
        language: 'en',
      }));
    });

    const followUp = await screen.findByRole('button', { name: 'What is leaf spot?' });
    fireEvent.click(followUp);

    await waitFor(() => {
      expect(screen.getAllByText('What is leaf spot?').length).toBeGreaterThanOrEqual(1);
      expect(capturedBody).toEqual(expect.objectContaining({
        message: 'What is leaf spot?',
        entry_id: 'leaf_spot',
        language: 'en',
      }));
    });
  });

  test('ask more online button is disabled when online_enabled is false', async () => {
    renderAskTab();
    const chip = await screen.findByRole('button', { name: 'What is Mahali?' });
    fireEvent.click(chip);

    const askMoreBtn = await screen.findByRole('button', { name: /ask more \(online\)/i });
    expect(askMoreBtn).toBeDisabled();
    expect(askMoreBtn).toHaveClass('disabled');
  });

  test('ask more online button triggers privacy modal and remembers acknowledgment', async () => {
    let capturedOnlineBody = null;
    vi.stubGlobal('fetch', vi.fn(async (path, opts) => {
      if (typeof path === 'string' && path.includes('/api/chat/chips')) {
        return { ok: true, json: async () => ({ chips: mockChips }) };
      }
      if (typeof path === 'string' && path.includes('/api/chat/status')) {
        return { ok: true, json: async () => ({ online_enabled: true }) };
      }
      if (typeof path === 'string' && path.includes('/api/chat/online')) {
        if (opts && opts.body) capturedOnlineBody = JSON.parse(opts.body);
        return {
          ok: true,
          json: async () => ({
            answer: 'This is an AI-generated explanation grounded in CPCRI guide.',
            intent: 'online_llm',
            sources: [],
            refused: false,
            needs_expert_review: false,
            language_fallback: false,
            suggestions: [],
            ai_generated: true,
            answer_source: 'ai',
          }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          answer: 'Mahali is fruit rot of areca nut.',
          intent: 'faq',
          entry_id: 'what_is_koleroga',
          sources: [],
          refused: false,
          needs_expert_review: false,
          language_fallback: false,
          suggestions: [],
          ai_generated: false,
          answer_source: 'guide',
        }),
      };
    }));

    renderAskTab();
    const chip = await screen.findByRole('button', { name: 'What is Mahali?' });
    fireEvent.click(chip);

    const askMoreBtn = await screen.findByRole('button', { name: /ask more \(online\)/i });
    expect(askMoreBtn).not.toBeDisabled();
    fireEvent.click(askMoreBtn);

    // Privacy notice modal should pop up
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/what is sent:/i)).toBeInTheDocument();
    expect(screen.getByText(/what is not sent:/i)).toBeInTheDocument();

    // Click acknowledge button
    const ackBtn = screen.getByRole('button', { name: /i understand/i });
    fireEvent.click(ackBtn);

    // Modal closes and online answer appears
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      expect(screen.getByText(/this is an ai-generated explanation/i)).toBeInTheDocument();
      expect(screen.getByText(/ai-generated, may be wrong/i)).toBeInTheDocument();
    });

    expect(sessionStorage.getItem('arecalens_online_ack_v1')).toBe('true');
    expect(capturedOnlineBody).toEqual(expect.objectContaining({
      message: 'What is Mahali?',
      language: 'en',
    }));
    expect(Array.isArray(capturedOnlineBody.history)).toBe(true);
  });

  test('displays online error notice when online_error is returned', async () => {
    vi.stubGlobal('fetch', vi.fn(async (path) => {
      if (typeof path === 'string' && path.includes('/api/chat/chips')) {
        return { ok: true, json: async () => ({ chips: mockChips }) };
      }
      if (typeof path === 'string' && path.includes('/api/chat/status')) {
        return { ok: true, json: async () => ({ online_enabled: true }) };
      }
      if (typeof path === 'string' && path.includes('/api/chat/online')) {
        return {
          ok: true,
          json: async () => ({
            answer: 'Verified offline fallback answer.',
            intent: 'faq',
            sources: [],
            refused: false,
            needs_expert_review: false,
            language_fallback: false,
            suggestions: [],
            ai_generated: false,
            answer_source: 'guide',
            online_error: 'rate_limited',
          }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          answer: 'Mahali is fruit rot of areca nut.',
          intent: 'faq',
          sources: [],
          refused: false,
          needs_expert_review: false,
          language_fallback: false,
          suggestions: [],
          ai_generated: false,
          answer_source: 'guide',
        }),
      };
    }));

    sessionStorage.setItem('arecalens_online_ack_v1', 'true');
    renderAskTab();
    const chip = await screen.findByRole('button', { name: 'What is Mahali?' });
    fireEvent.click(chip);

    const askMoreBtn = await screen.findByRole('button', { name: /ask more \(online\)/i });
    fireEvent.click(askMoreBtn);

    await waitFor(() => {
      expect(screen.getByText(/too many requests to the ai provider/i)).toBeInTheDocument();
      expect(screen.getByText('Verified offline fallback answer.')).toBeInTheDocument();
    });
  });
});

