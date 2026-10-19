import { useState } from 'react';
import { Focus, Download } from 'lucide-react';
import { useLanguage } from '../locales/LanguageContext';

export default function HeatmapViewer({ result }) {
  const { t } = useLanguage();
  const [mode, setMode] = useState('heatmap'), [visibility, setVisibility] = useState(100);
  return <section className="card heatmap-card"><div className="section-heading"><Focus size={20}/><h2>{t('heatTitle')}</h2><a className="icon-button" href={result.heatmap_image} download="arecalens-cam.png" aria-label={t('saveHeatmap')}><Download size={17}/></a></div>
    <div className="segmented" aria-label="Image view">{[['original', t('modelInput')], ['heatmap', t('camOverlay')], ['compare', t('compare')]].map(([key,label]) => <button key={key} onClick={() => setMode(key)} aria-pressed={mode === key} className={mode === key ? 'selected' : ''}>{label}</button>)}</div>
    {mode === 'compare' ? <div className="image-comparison"><figure><img src={result.original_image} alt={t('modelInput')}/><figcaption>{t('modelInput')}</figcaption></figure><figure><img src={result.heatmap_image} alt={t('camOverlay')}/><figcaption>{t('camOverlay')}</figcaption></figure></div> : <div className="heatmap-stage"><img className="heatmap-image" src={result.original_image} alt={t('modelInput')}/>{mode === 'heatmap' && <img className="heatmap-layer" src={result.heatmap_image} alt={t('camOverlay')} style={{opacity: visibility / 100}}/>}</div>}
    {mode === 'heatmap' && <label className="overlay-control"><span>{t('overlayVisibility')}<strong>{visibility}%</strong></span><input type="range" aria-label={t('overlayVisibility')} min="0" max="100" value={visibility} onChange={e => setVisibility(Number(e.target.value))}/></label>}
    <div className="heat-legend"><span>{t('lowAttention')}</span><i/><span>{t('highAttention')}</span></div>
    <p className="muted small">{t('heatNote')}</p>
  </section>;
}
