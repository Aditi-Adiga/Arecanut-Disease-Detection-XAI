import { BookOpen, ExternalLink, Leaf, CircleAlert } from 'lucide-react';
import { useLanguage } from '../locales/LanguageContext';

export default function DiseaseInfo({ info, classId, onSelect }) {
  const { t } = useLanguage();
  if (!info) return <div className="card guide-card"><p>{t('guideLoading')}</p></div>;
  const selected = classId || 'Mahali_Koleroga', item = info.classes[selected];
  const sections = [[t('signs'), item.check_signs], [t('causes'), item.possible_causes], [t('actions'), item.what_to_do], [t('getHelp'), item.when_to_get_help]];
  const sourceIds = new Set([...(item.summary.sources || []), ...sections.flatMap(([,values]) => (values || []).flatMap(v => v.sources || []))]);
  return <section className="card guide-card"><div className="section-heading"><BookOpen size={20}/><h2>{t('guideTitle')}</h2><span className="tiny-label">{t('reference')}</span></div>
    <div className="guide-tabs">{Object.entries(info.classes).map(([id,disease]) => <button key={id} onClick={() => onSelect(id)} aria-pressed={selected === id} className={selected === id ? 'selected' : ''}>{disease.short_name}</button>)}</div>
    <div className="guide-title"><span className="guide-leaf"><Leaf size={25}/></span><div><span className="eyebrow">{t('knowSigns')}</span><h3>{item.display_name}</h3></div></div>
    <p className="guide-summary">{item.summary.text}</p>
    <div className="draft-notice"><CircleAlert size={19}/><p><strong>{t('draftTitle')}</strong> {t('draftDescription')}</p></div>
    <div className="guide-columns">{sections.filter(([,values]) => values?.length).map(([title,values]) => <div key={title}><h4>{title}</h4><ul>{values.filter(v => !v.verify).map((value,i) => <li key={i}>{value.text}</li>)}</ul></div>)}</div>
    {item.also_consider?.length > 0 && <p className="small"><strong>{t('alternatives')}:</strong> {item.also_consider.map(v => v.name).join(', ')}.</p>}
    <p className="limits"><strong>{t('photoLimits')}:</strong> {item.limits.text}</p>
    <details className="sources"><summary>{t('sources')} ({sourceIds.size})</summary>{[...sourceIds].map(id => { const source=info.sources[id]; return source && <a key={id} href={source.url} target="_blank" rel="noreferrer">{source.publisher} · {source.title} ({source.year}) <ExternalLink size={13}/></a>; })}</details>
  </section>;
}
