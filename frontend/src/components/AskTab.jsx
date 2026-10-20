import { useEffect, useRef, useState } from 'react';
import { Send, ShieldCheck, AlertTriangle, RefreshCw, Trash2, ExternalLink, BookOpen, MessageSquare } from 'lucide-react';
import { useLanguage } from '../locales/LanguageContext';
import { getJson } from '../services/api';

const STORAGE_KEY = 'arecalens_chat_history_v1';
const MAX_MESSAGES = 30;

function loadStoredMessages() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY) || localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.slice(-MAX_MESSAGES) : [];
  } catch {
    return [];
  }
}

function persistMessages(msgs) {
  try {
    const trimmed = msgs.slice(-MAX_MESSAGES);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    /* storage failure is non-fatal */
  }
}

export default function AskTab({ result, info }) {
  const { language, t } = useLanguage();
  const [messages, setMessages] = useState(loadStoredMessages);
  const [chips, setChips] = useState([]);
  const [question, setQuestion] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const [lastQuery, setLastQuery] = useState(null);
  const [openSources, setOpenSources] = useState({});
  const messagesEndRef = useRef(null);

  // Load starter question chips whenever language changes
  useEffect(() => {
    let active = true;
    getJson(`/api/chat/chips?language=${language}`)
      .then(res => {
        if (active && res && Array.isArray(res.chips)) {
          setChips(res.chips);
        }
      })
      .catch(() => {
        if (active) setChips([]);
      });
    return () => {
      active = false;
    };
  }, [language]);

  // Persist messages whenever updated
  useEffect(() => {
    persistMessages(messages);
  }, [messages]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, busy, error]);

  async function sendMessage(textToSend, contextOverride = null) {
    const trimmed = (textToSend || '').trim();
    if (!trimmed || busy) return;

    setError(false);
    setQuestion('');
    const userMsg = {
      id: 'u_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6),
      role: 'user',
      content: trimmed,
    };

    setMessages(prev => [...prev, userMsg].slice(-MAX_MESSAGES));
    setBusy(true);

    const chatContext = contextOverride || (result && result.class_id ? {
      class: result.class_id,
      status: result.status,
      confidence: result.confidence,
    } : null);

    const payload = {
      message: trimmed,
      language,
      ...(chatContext ? { context: chatContext } : {}),
    };

    setLastQuery({ text: trimmed, context: chatContext });

    try {
      const data = await getJson('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const botMsg = {
        id: 'b_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6),
        role: 'assistant',
        answer: data.answer,
        intent: data.intent,
        entry_id: data.entry_id,
        sources: data.sources || [],
        refused: data.refused,
        needs_expert_review: data.needs_expert_review,
        language_fallback: data.language_fallback,
        suggestions: data.suggestions || [],
        ai_generated: data.ai_generated,
        answer_source: data.answer_source || 'guide',
      };

      setMessages(prev => [...prev, botMsg].slice(-MAX_MESSAGES));
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  function handleRetry() {
    if (lastQuery) {
      sendMessage(lastQuery.text, lastQuery.context);
    }
  }

  function handleClearChat() {
    setMessages([]);
    try {
      sessionStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
  }

  function toggleSources(msgId) {
    setOpenSources(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  }

  const resultClassName = result && result.class_id
    ? (info?.classes?.[result.class_id]?.short_name || result.display_name || result.class_id)
    : '';

  return (
    <div className="ask-tab-container card">
      <div className="ask-tab-header">
        <div>
          <span className="eyebrow"><BookOpen size={14} />{t('verifiedGuideBadge')}</span>
          <h2>{t('askTitle')}</h2>
          <p>{t('askDescription')}</p>
        </div>
        {messages.length > 0 && (
          <button
            type="button"
            className="text-button ask-clear-btn"
            onClick={handleClearChat}
            aria-label={t('clearChat')}
          >
            <Trash2 size={16} />
            <span>{t('clearChat')}</span>
          </button>
        )}
      </div>

      {result && result.class_id && (
        <div className="ask-last-result-wrapper">
          <button
            type="button"
            className="ask-last-result-chip"
            onClick={() => sendMessage('What should I do now?', {
              class: result.class_id,
              status: result.status,
              confidence: result.confidence,
            })}
          >
            <ShieldCheck size={16} />
            <span>{t('lastResultChip', { name: resultClassName })}</span>
          </button>
        </div>
      )}

      {messages.length === 0 && chips.length > 0 && (
        <div className="ask-empty-state" role="group" aria-label={t('starterQuestions')}>
          <h3>{t('starterQuestions')}</h3>
          <div className="ask-chips-grid">
            {chips.map(chip => (
              <button
                key={chip.id}
                type="button"
                className="ask-chip-button"
                onClick={() => sendMessage(chip.question)}
                disabled={busy}
              >
                {chip.question}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="ask-message-list" aria-live="polite">
        {messages.map((msg, index) => (
          <div key={msg.id || index} className={`ask-message ${msg.role}`}>
            {msg.role === 'user' ? (
              <div className="ask-user-bubble">{msg.content}</div>
            ) : (
              <div className="ask-bot-bubble">
                <div className="ask-bot-meta">
                  <span className="ask-meta-badge verified">
                    <BookOpen size={13} />
                    {t('verifiedGuideBadge')}
                  </span>
                  {msg.needs_expert_review && (
                    <span className="ask-meta-badge expert-review">
                      <AlertTriangle size={13} />
                      {t('expertReviewBadge')}
                    </span>
                  )}
                </div>

                {msg.language_fallback && (
                  <div className="ask-language-notice" role="status">
                    {t('languageFallbackNotice')}
                  </div>
                )}

                <div className="ask-answer-text">{msg.answer}</div>

                {msg.sources && msg.sources.length > 0 && (
                  <div className="ask-sources-section">
                    <button
                      type="button"
                      className="ask-sources-toggle"
                      onClick={() => toggleSources(msg.id || index)}
                      aria-expanded={Boolean(openSources[msg.id || index])}
                    >
                      {openSources[msg.id || index]
                        ? t('sourcesHide')
                        : t('sourcesToggle', { count: msg.sources.length })}
                    </button>
                    {openSources[msg.id || index] && (
                      <ul className="ask-sources-list">
                        {msg.sources.map((s, sIdx) => (
                          <li key={s.id || sIdx}>
                            <a
                              href={s.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="ask-source-link"
                            >
                              <span>{s.title}</span>
                              <ExternalLink size={12} />
                            </a>
                            <span className="ask-source-pub"> — {s.publisher}{s.year ? `, ${s.year}` : ''}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="ask-suggestions-group" role="group" aria-label={t('starterQuestions')}>
                    {msg.suggestions.map(s => (
                      <button
                        key={s.id}
                        type="button"
                        className="ask-chip-button suggestion"
                        onClick={() => sendMessage(s.question)}
                        disabled={busy}
                      >
                        {s.question}
                      </button>
                    ))}
                  </div>
                )}

                {(msg.language_fallback || msg.intent === 'fallback') && chips.length > 0 && (
                  <div className="ask-suggestions-group fallback-chips" role="group" aria-label={t('starterQuestions')}>
                    {chips.map(chip => (
                      <button
                        key={chip.id}
                        type="button"
                        className="ask-chip-button suggestion"
                        onClick={() => sendMessage(chip.question)}
                        disabled={busy}
                      >
                        {chip.question}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {busy && (
          <div className="ask-message assistant">
            <div className="ask-bot-bubble busy-bubble" role="status">
              <span className="ask-dot-pulse" />
              <span>{t('connecting')}</span>
            </div>
          </div>
        )}

        {error && (
          <div className="ask-error-card" role="alert">
            <span>{t('serverUnreachable')}</span>
            <button type="button" className="text-button retry-btn" onClick={handleRetry}>
              <RefreshCw size={15} />
              <span>{t('retry')}</span>
            </button>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="ask-input-dock">
        <form
          className="ask-input-form"
          onSubmit={e => {
            e.preventDefault();
            sendMessage(question);
          }}
        >
          <label htmlFor="ask-question-input" className="visually-hidden">
            {t('chatInputLabel')}
          </label>
          <div className="ask-input-row">
            <input
              id="ask-question-input"
              type="text"
              value={question}
              maxLength={300}
              placeholder={t('chatInputPlaceholder')}
              onChange={e => setQuestion(e.target.value)}
              disabled={busy}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(question);
                }
              }}
            />
            <span className="ask-char-counter" aria-live="off">
              {t('charCounter', { count: question.length })}
            </span>
            <button
              type="submit"
              className="primary-button ask-send-button"
              disabled={busy || !question.trim()}
              aria-label={t('send')}
            >
              <Send size={18} />
              <span>{t('send')}</span>
            </button>
          </div>
        </form>
        <div className="ask-footer-bar">
          <p className="ask-aid-disclaimer">{t('chatFooterAid')}</p>
        </div>
      </div>
    </div>
  );
}
