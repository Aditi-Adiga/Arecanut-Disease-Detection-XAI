import { useState } from 'react';
import { Focus } from 'lucide-react';

export default function HeatmapViewer({ result }) {
  const [mode, setMode] = useState('heatmap');
  return <section className="card heatmap-card"><div className="section-heading"><Focus size={19}/><h2>Where the model looked</h2></div>
    <div className="segmented" aria-label="Image view"><button onClick={() => setMode('original')} aria-pressed={mode === 'original'} className={mode === 'original' ? 'selected' : ''}>Model input</button><button onClick={() => setMode('heatmap')} aria-pressed={mode === 'heatmap'} className={mode === 'heatmap' ? 'selected' : ''}>CAM overlay</button></div>
    <img className="heatmap-image" src={mode === 'heatmap' ? result.heatmap_image : result.original_image} alt={mode === 'heatmap' ? 'Class activation map overlay showing model attention' : 'Image after the model’s 224 by 224 resize'} />
    <div className="heat-legend"><span>Lower attention</span><i/><span>Higher attention</span></div>
    <p className="muted small">Attention to the top predicted class. Warm colours show stronger contribution; they do not identify a confirmed lesion or cause.</p>
  </section>;
}
