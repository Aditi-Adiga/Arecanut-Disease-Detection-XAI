import { Leaf, ScanLine, BookOpen, MessageSquare, History, Languages } from 'lucide-react';
import { useLanguage } from '../locales/LanguageContext';
import { LANGUAGES } from '../locales/messages';

export default function Navbar({ view, onChange, onLanguage }) {
  const { t, language } = useLanguage();
  return <header className="header"><div className="nav-shell">
    <button className="brand" onClick={() => onChange('scan')} aria-label="ArecaLens home"><span className="brand-icon"><Leaf size={24}/></span><span>Areca<span className="brand-light">Lens</span><small>{t('tagline')}</small></span></button>
    <nav aria-label="Main navigation">{[['scan', t('analyseNav'), ScanLine], ['guide', t('guideNav'), BookOpen], ['ask', t('askNav'), MessageSquare], ['history', t('historyNav'), History]].map(([key, label, Icon]) => <button key={key} className={view === key ? 'nav-item active' : 'nav-item'} aria-current={view === key ? 'page' : undefined} onClick={() => onChange(key)}><Icon size={18}/><span>{label}</span></button>)}</nav>
    <button className="language-switch" onClick={onLanguage} aria-label={t('language')}><Languages size={17}/>{LANGUAGES.find(item => item.code === language)?.name}</button>
  </div></header>;
}
