import { useEffect, useRef, useState } from 'react';
import { Send, ShieldCheck, AlertTriangle, RefreshCw, Trash2, ExternalLink, BookOpen, Sparkles } from 'lucide-react';
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
  const [busyMode, setBusyMode] = useState('offline'); // 'offline' | 'online'
  const [error, setError] = useState(false);
  const [lastQuery, setLastQuery] = useState(null);
  const [openSources, setOpenSources] = useState({});
  const [onlineEnabled, setOnlineEnabled] = useState(false);
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [pendingOnlineQuery, setPendingOnlineQuery] = useState(null);
  const messagesEndRef = useRef(null);

  // Monitor network online/offline state
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Fetch online mode availability status
  useEffect(() => {
    let active = true;
    getJson('/api/chat/status')
      .then(res => {
        if (active && res && typeof res.online_enabled === 'boolean') {
          setOnlineEnabled(res.online_enabled);
        }
      })
      .catch(() => {
        if (active) setOnlineEnabled(false);
      });
    return () => {
      active = false;
    };
  }, []);

  // Load starter question chips and refresh suggestions whenever language changes
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

    // Also reload suggestion chips in existing messages when language changes
    setMessages(prev => {
      const lastAssIdx = prev.map(m => m.role).lastIndexOf('assistant');
      if (lastAssIdx === -1 || !prev[lastAssIdx]?.suggestions?.length) {
        return prev;
      }
      const suggestionIds = prev[lastAssIdx].suggestions.map(s => s.id).filter(Boolean);
      if (suggestionIds.length === 0) return prev;

      getJson(`/api/chat/chips?language=${language}&ids=${suggestionIds.join(',')}`)
        .then(res => {
          if (!active || !res || !Array.isArray(res.chips)) return;
          setMessages(current => {
            const idx = current.map(m => m.role).lastIndexOf('assistant');
            if (idx === -1 || !current[idx]?.suggestions?.length) return current;
            const updated = [...current];
            updated[idx] = {
              ...updated[idx],
              suggestions: res.chips,
            };
            return updated;
          });
        })
        .catch(() => {});
      return prev;
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

  async function sendMessage(textToSend, contextOverride = null, entryId = null, isOnlineRequest = false) {
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
    setBusyMode(isOnlineRequest ? 'online' : 'offline');

    const chatContext = contextOverride || (result && result.class_id ? {
      class: result.class_id,
      status: result.status,
      confidence: result.confidence,
    } : null);

    const historyTurns = messages.slice(-6).map(m => ({
      role: m.role,
      content: m.role === 'user' ? m.content : m.answer,
    }));

    const payload = {
      message: trimmed,
      language,
      ...(chatContext ? { context: chatContext } : {}),
      ...(entryId ? { entry_id: entryId } : {}),
      ...(isOnlineRequest ? { history: historyTurns } : {}),
    };

    setLastQuery({ text: trimmed, context: chatContext, entryId, isOnlineRequest });

    const endpoint = isOnlineRequest ? '/api/chat/online' : '/api/chat';

    try {
      // 15-second client-side timeout controller
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);

      const data = await getJson(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      const botMsg = {
        id: 'b_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6),
        role: 'assistant',
        userQuery: trimmed,
        answer: data.answer,
        intent: data.intent,
        entry_id: data.entry_id,
        sources: data.sources || [],
        refused: data.refused,
        needs_expert_review: data.needs_expert_review,
        language_fallback: data.language_fallback,
        suggestions: data.suggestions || [],
        ai_generated: Boolean(data.ai_generated),
        answer_source: data.answer_source || (data.ai_generated ? 'ai' : 'guide'),
        online_error: data.online_error || null,
      };

      setMessages(prev => [...prev, botMsg].slice(-MAX_MESSAGES));
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  function handleAskMoreClick(msg, index) {
    let userText = msg.userQuery;
    if (!userText) {
      for (let i = index - 1; i >= 0; i--) {
        if (messages[i].role === 'user') {
          userText = messages[i].content;
          break;
        }
      }
    }
    if (!userText) userText = msg.answer;

    const hasAcknowledged = sessionStorage.getItem('arecalens_online_ack_v1') === 'true';
    if (!hasAcknowledged) {
      setPendingOnlineQuery(userText);
      setShowPrivacyModal(true);
      return;
    }

    sendMessage(userText, null, null, true);
  }

  function handleConfirmPrivacy() {
    try {
      sessionStorage.setItem('arecalens_online_ack_v1', 'true');
    } catch {
      /* ignore */
    }
    setShowPrivacyModal(false);
    if (pendingOnlineQuery) {
      const q = pendingOnlineQuery;
      setPendingOnlineQuery(null);
      sendMessage(q, null, null, true);
    }
  }

  function handleRetry() {
    if (lastQuery) {
      sendMessage(lastQuery.text, lastQuery.context, lastQuery.entryId, lastQuery.isOnlineRequest);
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

  const lastAssistantIndex = messages.map(m => m.role).lastIndexOf('assistant');

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
            onClick={() => sendMessage(t('lastResultQuestion'), {
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
                onClick={() => sendMessage(chip.question, null, chip.id)}
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
                  {msg.ai_generated ? (
                    <span className="ask-meta-badge ai-generated">
                      <Sparkles size={13} />
                      {t('aiGeneratedBadge')}
                    </span>
                  ) : (
                    <span className="ask-meta-badge verified">
                      <BookOpen size={13} />
                      {t('verifiedGuideBadge')}
                    </span>
                  )}
                  {msg.needs_expert_review && (
                    <span className="ask-meta-badge expert-review">
                      <AlertTriangle size={13} />
                      {t('expertReviewBadge')}
                    </span>
                  )}
                </div>

                {msg.online_error && (
                  <div className="ask-online-error-notice" role="status">
                    {msg.online_error === 'rate_limited'
                      ? t('onlineErrorRateLimit')
                      : msg.online_error === 'not_configured'
                      ? t('onlineErrorNotConfigured')
                      : t('onlineErrorGeneric')}
                  </div>
                )}

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

                {!msg.ai_generated && !msg.refused && (
                  <div className="ask-online-actions">
                    <button
                      type="button"
                      className={`ask-more-online-btn ${!onlineEnabled || !isOnline ? 'disabled' : ''}`}
                      disabled={busy || !onlineEnabled || !isOnline}
                      title={!isOnline ? t('onlineOfflineReason') : !onlineEnabled ? t('onlineErrorNotConfigured') : t('askMoreOnline')}
                      onClick={() => handleAskMoreClick(msg, index)}
                    >
                      <Sparkles size={14} />
                      <span>{t('askMoreOnline')}</span>
                      {(!onlineEnabled || !isOnline) && (
                        <small className="ask-disabled-reason">
                          ({!isOnline ? t('onlineOfflineReason') : t('onlineErrorNotConfigured')})
                        </small>
                      )}
                    </button>
                  </div>
                )}

                {index === lastAssistantIndex && msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="ask-suggestions-group" role="group" aria-label={t('starterQuestions')}>
                    {msg.suggestions.map(s => (
                      <button
                        key={s.id}
                        type="button"
                        className="ask-chip-button suggestion"
                        onClick={() => sendMessage(s.question, null, s.id)}
                        disabled={busy}
                      >
                        {s.question}
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
              <span>{busyMode === 'online' ? t('connectingOnline') : t('connecting')}</span>
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

      {showPrivacyModal && (
        <div className="ask-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="ask-privacy-title">
          <div className="ask-modal-card">
            <h3 id="ask-privacy-title">{t('onlinePrivacyTitle')}</h3>
            <div className="ask-modal-body">
              <p className="privacy-point sent">✓ {t('onlinePrivacySent')}</p>
              <p className="privacy-point not-sent">✕ {t('onlinePrivacyNotSent')}</p>
            </div>
            <div className="ask-modal-actions">
              <button
                type="button"
                className="primary-button"
                onClick={handleConfirmPrivacy}
              >
                {t('onlinePrivacyAcknowledge')}
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() => {
                  setShowPrivacyModal(false);
                  setPendingOnlineQuery(null);
                }}
              >
                {t('cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
