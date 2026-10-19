import { BookOpen, ExternalLink, Leaf, CircleAlert } from 'lucide-react';

export default function DiseaseInfo({ info, classId, onSelect }) {
  if (!info) return <div className="card guide-card"><p>Disease information will load when the local API is available.</p></div>;
  const selected = classId || 'Mahali_Koleroga';
  const item = info.classes[selected];
  const sections = [['What to check', item.check_signs], ['Possible causes', item.possible_causes], ['Care and next steps', item.what_to_do], ['When to get help', item.when_to_get_help]];
  const sourceIds = new Set([...(item.summary.sources || []), ...sections.flatMap(([, values]) => (values || []).flatMap(v => v.sources || []))]);
  return <section className="card guide-card"><div className="section-heading"><BookOpen size={19}/><h2>Disease field guide</h2><span className="tiny-label">REFERENCE</span></div>
    <div className="guide-tabs">{Object.entries(info.classes).map(([id, disease]) => <button key={id} onClick={() => onSelect(id)} aria-pressed={selected === id} className={selected === id ? 'selected' : ''}>{id === 'Yellow_Leaf' ? 'Yellow leaf / spot' : disease.short_name.replace(' (fruit rot)', '')}</button>)}</div>
    <div className="guide-title"><span className="guide-leaf"><Leaf size={23}/></span><div><span className="eyebrow">KNOW THE SIGNS</span><h3>{item.display_name}</h3></div></div>
    <p className="guide-summary">{item.summary.text}</p>
    <div className="draft-notice"><CircleAlert size={18}/><p><strong>Draft reference · expert review pending.</strong> Guidance is taken from your supplied disease information file. Confirm treatment and doses with a local agricultural officer.</p></div>
    <div className="guide-columns">{sections.filter(([, values]) => values?.length).map(([title, values]) => <div key={title}><h4>{title}</h4><ul>{values.filter(v => !v.verify).map((value, i) => <li key={i}>{value.text}</li>)}</ul></div>)}</div>
    {item.also_consider?.length > 0 && <p className="small"><strong>Other possibilities:</strong> {item.also_consider.map(v => v.name).join(', ')}.</p>}
    <p className="limits"><strong>Limits of a photo:</strong> {item.limits.text}</p>
    <details className="sources"><summary>Reference sources ({sourceIds.size})</summary>{[...sourceIds].map(id => { const source = info.sources[id]; return source && <a key={id} href={source.url} target="_blank" rel="noreferrer">{source.publisher} · {source.title} ({source.year}) <ExternalLink size={13}/></a>; })}</details>
  </section>;
}
