import { CircleCheck, CircleHelp, TriangleAlert, Download, Sparkles } from 'lucide-react';
import HeatmapViewer from './HeatmapViewer';
import { formatScore } from '../services/format';
import { useLanguage } from '../locales/LanguageContext';

export default function PredictionResult({ result }) {
  const { t } = useLanguage();
  const unsure = result.status === 'unsure';
  const healthyGuess = unsure && result.healthy_guess_below_threshold;
  const Icon = unsure ? CircleHelp : result.status === 'healthy' ? CircleCheck : TriangleAlert;
  const label = t(unsure ? 'unsureLabel' : result.status === 'healthy' ? 'healthyLabel' : 'suspectedLabel');
  function download() {
    const blob = new Blob([JSON.stringify({ generated_at: new Date().toISOString(), ...result }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob), anchor = document.createElement('a');
    anchor.href = url; anchor.download = 'arecalens-result-' + Date.now() + '.json'; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <div className="results" aria-live="polite"><section className={'card result-card ' + result.status}>
    <div className="section-heading"><span className="step">02</span><h2>{t('resultTitle')}</h2><button className="icon-button" aria-label={t('downloadReport')} onClick={download}><Download size={19}/></button></div>
    <div className="result-badge"><Icon size={18}/>{label}</div>
    <h3 className="result-title">{healthyGuess ? t('unsureHealthyTitle', {name: result.display_name}) : unsure ? t('unsureTitle') : result.display_name}</h3>
    <p className="muted">{healthyGuess ? t('closestHealthyGuess', {score: formatScore(result.confidence), cutoff: formatScore(result.healthy_cutoff)}) : unsure ? t('closestGuess', {name: result.display_name}) : t('resultDescription')}</p>
    <div className="score-panel"><div className="score-orbit" style={{'--score': Math.max(0,Math.min(100,result.confidence*100)) + '%'}}><strong>{formatScore(result.confidence)}</strong></div><div><h4>{t('scoreLabel')}</h4><p>{t('scoreDisclaimer')}</p></div></div>
    <details className="scores-details"><summary>{t('allScores')}</summary><div className="probabilities">{[...result.probabilities].sort((a,b) => b.probability-a.probability).map(item => <div className="probability" key={item.class_id}><div><span>{item.label}</span><span>{formatScore(item.probability)}</span></div><div className="track"><i style={{width: item.probability*100 + '%'}}/></div></div>)}</div></details>
    <div className="explanation"><h4><Sparkles size={18}/>{t('explanationTitle')}</h4>{result.explanation.lines.slice(1).map((line,i) => <p key={i}>{line}</p>)}</div>
    {result.photo_tips.map(tip => <p className="notice" key={tip}>{tip}</p>)}
  </section><HeatmapViewer result={result}/></div>;
}
