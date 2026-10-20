import { useEffect, useRef, useState } from 'react';
import { Bot, ChevronDown, MessageCircle, Send, Wifi, WifiOff, X } from 'lucide-react';
import { useLanguage } from '../locales/LanguageContext';
import { getJson } from '../services/api';

const suggestions = {
  en: ['What does the heatmap show?', 'What signs should I check?', 'How do I use the app?'],
  kn: ['ಹೀಟ್‌ಮ್ಯಾಪ್ ಏನು ತೋರಿಸುತ್ತದೆ?', 'ಯಾವ ಲಕ್ಷಣಗಳನ್ನು ಪರಿಶೀಲಿಸಬೇಕು?', 'ಅಪ್ಲಿಕೇಶನ್ ಅನ್ನು ಹೇಗೆ ಬಳಸುವುದು?'],
  hi: ['हीटमैप क्या दिखाता है?', 'मुझे कौन से लक्षण देखने चाहिए?', 'ऐप का उपयोग कैसे करें?'],
  ml: ['ഹീറ്റ്മാപ്പ് എന്താണ് കാണിക്കുന്നത്?', 'ഏത് ലക്ഷണങ്ങളാണ് പരിശോധിക്കേണ്ടത്?', 'ആപ്പ് എങ്ങനെ ഉപയോഗിക്കാം?'],
};

const followupSuggestions = {
  en: ['Can you explain that more?', 'What should I check next?', 'When should I ask an expert?'],
  kn: ['ಅದನ್ನು ಇನ್ನಷ್ಟು ವಿವರಿಸಬಹುದೇ?', 'ಮುಂದೆ ಏನನ್ನು ಪರಿಶೀಲಿಸಬೇಕು?', 'ತಜ್ಞರನ್ನು ಯಾವಾಗ ಸಂಪರ್ಕಿಸಬೇಕು?'],
  hi: ['क्या आप इसे और समझा सकते हैं?', 'मुझे आगे क्या जाँचना चाहिए?', 'विशेषज्ञ से कब पूछना चाहिए?'],
  ml: ['ഇത് കുറച്ചുകൂടി വിശദീകരിക്കാമോ?', 'അടുത്തതായി എന്താണ് പരിശോധിക്കേണ്ടത്?', 'വിദഗ്ധനോട് എപ്പോൾ ചോദിക്കണം?'],
};

export default function ChatAssistant() {
  const { language, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('offline');
  const [onlineAvailable, setOnlineAvailable] = useState(false);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const tail = useRef(null);

  useEffect(() => {
    let active = true;
    getJson('/api/chat/status')
      .then(status => { if (active) setOnlineAvailable(status.online_available === true); })
      .catch(() => { if (active) setOnlineAvailable(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => { tail.current?.scrollIntoView?.({ block: 'nearest' }); }, [messages, busy, error]);
  async function send(text = question) {
    const content = text.trim();
    if (!content || busy) return;
    const context = messages.slice(-6);
    setError('');
    setQuestion('');
    setMessages(current => [...current, { role: 'user', content }]);
    setBusy(true);
    try {
      const result = await getJson('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, mode, language, history: context }),
      });
      setMessages(current => [...current, { role: 'assistant', content: result.answer }]);
    } catch (err) {
      setError(err.message || t('chatError'));
    } finally {
      setBusy(false);
    }
  }

  return <div className="chat-assistant">
    {open && <section className="chat-panel" aria-label={t('chatTitle')}>
      <header className="chat-header">
        <span className="chat-avatar"><Bot size={20}/></span>
        <span><strong>{t('chatTitle')}</strong><small>{mode === 'online' ? t('chatOnline') : t('chatOffline')}</small></span>
        <button className="chat-close" onClick={() => setOpen(false)} aria-label={t('chatClose')}><X size={18}/></button>
      </header>
      <div className="chat-mode" role="group" aria-label={t('chatMode')}>
        <button className={mode === 'offline' ? 'selected' : ''} onClick={() => setMode('offline')}><WifiOff size={15}/>{t('chatOffline')}</button>
        <button className={mode === 'online' ? 'selected' : ''} onClick={() => setMode('online')} disabled={!onlineAvailable} title={!onlineAvailable ? t('chatOnlineUnavailable') : undefined}><Wifi size={15}/>{t('chatOnline')}</button>
      </div>
      {mode === 'online' && <p className="chat-privacy">{t('chatOnlinePrivacy')}</p>}
      <div className="chat-messages" aria-live="polite">
        {!messages.length && <div className="chat-welcome"><Bot size={22}/><p>{t('chatWelcome')}</p>
          <div className="chat-suggestions">{(suggestions[language] || suggestions.en).map(item => <button key={item} onClick={() => send(item)} disabled={busy}>{item}</button>)}</div>
        </div>}
        {messages.map((item, index) => <div className={'chat-message '+item.role} key={index}>{item.content}</div>)}
        {messages.length > 0 && <div className="chat-suggestions chat-followups" role="group" aria-label={t('chatSuggestions')}>
          {(followupSuggestions[language] || followupSuggestions.en).map(item => <button key={item} onClick={() => send(item)} disabled={busy}>{item}</button>)}
        </div>}
        {busy && <p className="chat-thinking" role="status">{t('chatThinking')}</p>}
        {error && <p className="chat-error" role="alert">{error}</p>}
        <div ref={tail}/>
      </div>
      <form className="chat-form" onSubmit={event => { event.preventDefault(); send(); }}>
        <label className="visually-hidden" htmlFor="chat-question">{t('chatInputLabel')}</label>
        <input id="chat-question" value={question} maxLength={1000} onChange={event => setQuestion(event.target.value)} placeholder={t('chatPlaceholder')} disabled={busy}/>
        <button aria-label={t('chatSend')} disabled={busy || !question.trim()}><Send size={17}/></button>
      </form>
      <p className="chat-disclaimer">{t('chatDisclaimer')}</p>
    </section>}
    <button className="chat-launcher" onClick={() => setOpen(!open)} aria-label={open ? t('chatMinimize') : t('chatOpen')} aria-expanded={open}>
      {open ? <ChevronDown size={20}/> : <><MessageCircle size={20}/><span>{t('chatOpen')}</span></>}
    </button>
  </div>;
}
