import { CircleCheck, CircleHelp, TriangleAlert, Download, Sparkles } from 'lucide-react';
import HeatmapViewer from './HeatmapViewer';

export default function PredictionResult({ result }) {
  const unsure = result.status === 'unsure';
  const Icon = unsure ? CircleHelp : result.status === 'healthy' ? CircleCheck : TriangleAlert;
  const label = unsure ? 'Not sure — retake the photo' : result.status === 'healthy' ? 'No visible disease pattern detected' : 'Disease pattern suspected';
  function download() {
    const blob = new Blob([JSON.stringify({ generated_at: new Date().toISOString(), ...result }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob), anchor = document.createElement('a');
    anchor.href = url; anchor.download = `arecalens-result-${Date.now()}.json`; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <div className="results" aria-live="polite"><section className={`card result-card ${result.status}`}>
    <div className="section-heading"><span className="step">02</span><h2>Your screening result</h2><button className="icon-button" aria-label="Download result report" onClick={download}><Download size={19}/></button></div>
    <div className="result-badge"><Icon size={17}/>{label}</div>
    <h3 className="result-title">{unsure ? 'This photo needs another look.' : result.display_name}</h3>
    <p className="muted">{unsure ? `Closest model guess: ${result.display_name}. Confidence did not meet the result threshold.` : 'A screening suggestion from your photo. Check the plant and consider expert advice.'}</p>
    <div className="confidence-line"><span>Top model score</span><strong>{(result.confidence * 100).toFixed(1)}%</strong></div>
    <p className="small muted">Model scores are not a calibrated probability that a plant has a disease.</p>
    <div className="probabilities">{[...result.probabilities].sort((a, b) => b.probability - a.probability).map(item => <div className="probability" key={item.class_id}><div><span>{item.label}</span><span>{(item.probability * 100).toFixed(1)}%</span></div><div className="track"><i style={{ width: `${item.probability * 100}%` }}/></div></div>)}</div>
    <div className="explanation"><h4><Sparkles size={16}/> Understanding this result</h4>{result.explanation.lines.slice(1).map((line, i) => <p key={i}>{line}</p>)}</div>
    {result.photo_tips.map(tip => <p className="notice" key={tip}>{tip}</p>)}
  </section><HeatmapViewer result={result}/></div>;
}
