import { Leaf, ScanLine, BookOpen, History } from 'lucide-react';

export default function Navbar({ view, onChange }) {
  return <header className="header"><div className="nav-shell">
    <button className="brand" onClick={() => onChange('scan')} aria-label="ArecaLens home">
      <span className="brand-icon"><Leaf size={23} /></span><span>Areca<span className="brand-light">Lens</span><small>PLANT HEALTH, EXPLAINED</small></span>
    </button>
    <nav aria-label="Main navigation">{[
      ['scan', 'Analyse', ScanLine], ['guide', 'Disease guide', BookOpen], ['history', 'Scan history', History],
    ].map(([key, text, Icon]) => <button key={key} className={view === key ? 'nav-item active' : 'nav-item'} aria-current={view === key ? 'page' : undefined} onClick={() => onChange(key)}><Icon size={17} /><span>{text}</span></button>)}</nav>
    <span className="project-tag">RESEARCH PROJECT <span>01</span></span>
  </div></header>;
}
