import { Component, useEffect, useRef, useState } from 'react';
import { MessageCircle, Send, Sparkles, X } from 'lucide-react';
import { useLanguage } from '../locales/LanguageContext';
import { offlineChatAnswer } from '../locales/chatOfflineAnswers';

const intents = [
  ['result', 'chatPromptResult'],
  ['signs', 'chatPromptCheck'],
  ['photo', 'chatPromptPhoto'],
];

function percent(value) {
  const rounded = (Number(value || 0) * 100).toFixed(1);
  return `${rounded.endsWith('.0') ? rounded.slice(0, -2) : rounded}%`;
}

function mentionedClass(question, info) {
  if (!info?.classes) return undefined;
  const normalized = question.toLocaleLowerCase();
  return Object.entries(info.classes).find(([, item]) =>
    [item.display_name, item.short_name].some(name => name && normalized.includes(name.toLocaleLowerCase()))
  )?.[0];
}

function localIntent(question) {
  const q = question.toLocaleLowerCase();
  const words = {
    photo: ['photo', 'picture', 'camera', 'retake', 'फोटो', 'तस्वीर', 'ಚಿತ್ರ', 'ಫೋಟೋ', 'ചിത്രം', 'ഫോട്ടോ'],
    heat: ['heatmap', 'cam', 'heat map', 'red area', 'gradient', 'गरम नक्शा', 'हीटमैप', 'ಬಣ್ಣದ ನಕ್ಷೆ', 'ഹീറ്റ്', 'നിറമുള്ള ഭൂപടം'],
    score: ['score', 'confidence', 'threshold', 'unsure', 'not sure', 'अंक', 'स्कोर', 'सीमा', 'स्पष्ट नहीं', 'ಖಚಿತವಿಲ್ಲ', 'ಅಂಕ', 'ಮಿತಿ', 'വ്യക്തമല്ല', 'സ്കോർ', 'പരിധി'],
    signs: ['check', 'sign', 'symptom', 'look for', 'लक्षण', 'जाँच', 'लक्षण', 'देखें', 'ಲಕ್ಷಣ', 'ಪರಿಶೀಲಿಸ', 'लक्षण', 'तपास', 'ലക്ഷണം', 'പരിശോധ'],
    care: ['care', 'treat', 'treatment', 'spray', 'medicine', 'fertilizer', 'what can i do', 'next step'],
    cause: ['cause', 'reason', 'why', 'because'],
    result: ['result', 'prediction', 'my photo', 'my scan', 'मेरी जाँच', 'परिणाम', 'नतीजा', 'ಫಲಿತಾಂಶ', 'ಪರಿಶೀಲನೆ', 'ಫೋಟೋ', 'ഫലം', 'പരിശോധന'],
  };
  if (words.photo.some(word => q.includes(word))) return 'photo';
  if (words.heat.some(word => q.includes(word))) return 'heat';
  if (words.score.some(word => q.includes(word))) return 'score';
  if (words.signs.some(word => q.includes(word))) return 'signs';
  if (words.care.some(word => q.includes(word))) return 'care';
  if (words.cause.some(word => q.includes(word))) return 'cause';
  if (words.result.some(word => q.includes(word))) return 'result';
  return 'fallback';
}

function offlineAnswerForIntent(intent, { question = '', language, result, t }) {
  const resolvedIntent = intent || localIntent(question);
  if (resolvedIntent === 'photo') return t('chatPhotoTips');
  if (resolvedIntent === 'heat') return t('chatHeatmap');
  if (resolvedIntent === 'score') return offlineChatAnswer(language, 'score');
  if (resolvedIntent === 'result') {
    return result
      ? offlineChatAnswer(language, 'result', { name: result.display_name || result.class_id || 'the model result', score: percent(result.confidence) })
      : t('chatNoResult');
  }
  if (resolvedIntent === 'signs') return `${offlineChatAnswer(language, 'signs')}\n\n${t('chatNeedExpert')}`;
  if (resolvedIntent === 'care') return offlineChatAnswer(language, 'care');
  if (resolvedIntent === 'cause') return offlineChatAnswer(language, 'cause');
  return t('chatFallback');
}

export function answerFromGuide({ question = '', intent, info, result, guideClass, t, language = info?.language || 'en' }) {
  const questionIntent = intent || localIntent(question);
  if (questionIntent === 'photo') return t('chatPhotoTips');
  if (questionIntent === 'heat') return t('chatHeatmap');

  const hasGuide = Boolean(info?.classes && Object.keys(info.classes).length);
  const detectedClass = hasGuide ? mentionedClass(question, info) : undefined;
  const currentClass = result?.class_id && info?.classes?.[result.class_id] ? result.class_id : guideClass;
  const classId = (questionIntent === 'result' || questionIntent === 'score') && result?.class_id
    ? result.class_id
    : detectedClass || currentClass;
  const item = info?.classes?.[classId];

  if (questionIntent === 'result' || questionIntent === 'score') {
    if (!result) return questionIntent === 'score'
      ? offlineChatAnswer(language, 'score')
      : t('chatNoResult');
    if (!hasGuide || !item) return offlineChatAnswer(language, 'result', {
      name: result.display_name || result.class_id || 'the model result',
      score: percent(result.confidence),
    });
    if (result.status === 'unsure') {
      const healthyGuess = item.status === 'no_disease_found';
      const cutoff = info.explanation?.thresholds?.[healthyGuess ? 'healthy_below' : 'unsure_below'];
      if (cutoff == null || !Number.isFinite(Number(cutoff))) {
        return offlineChatAnswer(language, 'result', { name: item.short_name || item.display_name, score: percent(result.confidence) });
      }
      return healthyGuess
        ? t('chatUncertainHealthy', { name: item.short_name, score: percent(result.confidence), cutoff: percent(cutoff) })
        : t('chatUncertainOther', { name: item.short_name, score: percent(result.confidence), cutoff: percent(cutoff) });
    }
    return `${t('chatResult', { name: item.short_name, score: percent(result.confidence) })}\n\n${item.summary?.text || t('chatNeedExpert')}\n\n${t('chatNeedExpert')}`;
  }

  if (!hasGuide) {
    return offlineAnswerForIntent(questionIntent, { question, language, result, t });
  }

  if (questionIntent === 'cause') {
    const causes = (item?.possible_causes || []).map(value => value.text || value.name).filter(Boolean).slice(0, 3);
    return causes.length ? `${causes.join(' \u00b7 ')}\n\n${t('chatNeedExpert')}` : offlineChatAnswer(language, 'cause');
  }
  if (questionIntent === 'care') {
    const actions = (item?.what_to_do || []).filter(value => !value.verify).map(value => value.text).filter(Boolean).slice(0, 3);
    return actions.length ? `${actions.join(' \u00b7 ')}\n\n${t('chatNeedExpert')}` : offlineChatAnswer(language, 'care');
  }
  if (questionIntent === 'fallback' && !detectedClass) return t('chatFallback');
  if (questionIntent === 'signs' || detectedClass) {
    if (!item) return offlineAnswerForIntent('signs', { question, language, result, t });
    const signs = (item.check_signs || []).map(value => value.text).slice(0, 3).join(' \u00b7 ');
    const care = (item.what_to_do || []).filter(value => !value.verify).map(value => value.text).slice(0, 2).join(' \u00b7 ');
    return `${t('chatGuideAnswer', { name: item.short_name })}\n\n${t('chatSigns')}: ${signs || t('chatFallback')}\n\n${t('chatCare')}: ${care || t('chatNeedExpert')}\n\n${t('chatNeedExpert')}`;
  }
  return t('chatFallback');
}

function HelpChatPanel({ info, result, guideClass }) {
  const { language, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [conversation, setConversation] = useState([{ role: 'assistant', text: t('chatWelcome') }]);
  const endRef = useRef(null);
  useEffect(() => setConversation([{ role: 'assistant', text: t('chatWelcome') }]), [language]);
  useEffect(() => endRef.current?.scrollIntoView?.({ block: 'nearest' }), [conversation, open]);

  function ask(question, intent) {
    const clean = question.trim();
    if (!clean && !intent) return;
    let answer;
    try {
      answer = answerFromGuide({ question: clean, intent, info, result, guideClass, t, language });
      if (typeof answer !== 'string' || !answer.trim()) answer = t('chatFallback');
    } catch (error) {
      // The guide is draft data and may be incomplete. Keep a bad entry from
      // breaking the rest of the screening page.
      console.error('Plant-care help could not answer:', error);
      answer = offlineAnswerForIntent(intent, { question: clean, language, result, t });
    }
    setConversation(previous => [
      ...previous,
      ...(clean ? [{ role: 'user', text: clean }] : []),
      { role: 'assistant', text: answer },
    ]);
    setDraft('');
  }

  return <div className="help-chat">
    {open && <section className="help-chat-panel" aria-label={t('chatTitle')}>
      <header className="help-chat-header"><span className="help-chat-mark"><Sparkles size={17}/></span><div><strong>{t('chatTitle')}</strong><small>{t('chatSubtitle')}</small></div><button type="button" onClick={() => setOpen(false)} aria-label={t('chatClose')}><X size={19}/></button></header>
      <div className="help-chat-messages" aria-live="polite">{conversation.map((message, index) => <div key={`${index}-${message.role}`} className={`help-chat-message ${message.role}`}>{message.text}</div>)}<div ref={endRef}/></div>
      {conversation.length === 1 && <div className="help-chat-prompts">{intents.map(([intent, key]) => <button type="button" key={intent} onClick={() => ask('', intent)}>{t(key)}</button>)}</div>}
      <form className="help-chat-form" onSubmit={event => { event.preventDefault(); ask(draft); }}><input value={draft} onChange={event => setDraft(event.target.value)} placeholder={t('chatPlaceholder')} aria-label={t('chatPlaceholder')} /><button type="submit" disabled={!draft.trim()} aria-label={t('chatSend')}><Send size={17}/></button></form>
    </section>}
    <button type="button" className="help-chat-launcher" onClick={() => setOpen(value => !value)} aria-expanded={open} aria-label={open ? t('chatClose') : t('chatOpen')}><MessageCircle size={19}/><span>{open ? t('chatClose') : t('chatOpen')}</span></button>
  </div>;
}

export class HelpChatBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error) {
    console.error('Plant-care help failed to render:', error);
  }

  render() {
    if (this.state.failed) {
      return <HelpChatFallback result={this.props.result}/>;
    }
    return this.props.children;
  }
}

function HelpChatFallback({ result }) {
  const { language, t } = useLanguage();
  const [open, setOpen] = useState(true);
  const [draft, setDraft] = useState('');
  const [conversation, setConversation] = useState([{ role: 'assistant', text: t('chatWelcome') }]);
  const endRef = useRef(null);
  useEffect(() => endRef.current?.scrollIntoView?.({ block: 'nearest' }), [conversation]);

  function ask(question, intent) {
    const clean = question.trim();
    if (!clean && !intent) return;
    const answer = offlineAnswerForIntent(intent, { question: clean, language, result, t });
    setConversation(previous => [...previous, ...(clean ? [{ role: 'user', text: clean }] : []), { role: 'assistant', text: answer }]);
    setDraft('');
  }

  return <div className="help-chat">
    {open && <section className="help-chat-panel" aria-label={t('chatTitle')}>
      <header className="help-chat-header"><span className="help-chat-mark"><Sparkles size={17}/></span><div><strong>{t('chatTitle')}</strong><small>{t('chatSubtitle')}</small></div><button type="button" onClick={() => setOpen(false)} aria-label={t('chatClose')}><X size={19}/></button></header>
      <div className="help-chat-messages" aria-live="polite">{conversation.map((message, index) => <div key={`${index}-${message.role}`} className={`help-chat-message ${message.role}`}>{message.text}</div>)}<div ref={endRef}/></div>
      {conversation.length === 1 && <div className="help-chat-prompts">{intents.map(([intent, key]) => <button type="button" key={intent} onClick={() => ask('', intent)}>{t(key)}</button>)}</div>}
      <form className="help-chat-form" onSubmit={event => { event.preventDefault(); ask(draft); }}><input value={draft} onChange={event => setDraft(event.target.value)} placeholder={t('chatPlaceholder')} aria-label={t('chatPlaceholder')}/><button type="submit" disabled={!draft.trim()} aria-label={t('chatSend')}><Send size={17}/></button></form>
    </section>}
    <button type="button" className="help-chat-launcher" onClick={() => setOpen(value => !value)} aria-expanded={open} aria-label={open ? t('chatClose') : t('chatOpen')}><MessageCircle size={19}/><span>{open ? t('chatClose') : t('chatOpen')}</span></button>
  </div>;
}

export default function HelpChat(props) {
  return <HelpChatBoundary key="chat" result={props.result}>
    <HelpChatPanel {...props}/>
  </HelpChatBoundary>;
}
