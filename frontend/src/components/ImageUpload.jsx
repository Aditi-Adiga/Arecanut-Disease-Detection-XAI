import { useRef, useState } from 'react';
import { UploadCloud, Camera, ImagePlus, X, ArrowUpRight, LoaderCircle, ShieldCheck } from 'lucide-react';
import { useLanguage } from '../locales/LanguageContext';

export default function ImageUpload({ file, preview, busy, ready, onFile, onAnalyse, onClear, onError }) {
  const { t } = useLanguage();
  const input = useRef(null), camera = useRef(null);
  const [dragging, setDragging] = useState(false);
  function accept(candidate) {
    if (!candidate || busy) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(candidate.type)) { onError(t('unsupportedFile')); return; }
    if (candidate.size > 10 * 1024 * 1024) { onError(t('oversizedFile')); return; }
    onFile(candidate);
  }
  return <section className="upload-card card">
    <div className="section-heading"><span className="step">01</span><h2>{t('uploadTitle')}</h2><span className="tiny-label">{t('leafOrNut')}</span></div>
    <input ref={input} type="file" accept="image/jpeg,image/png,image/webp" aria-label="Choose plant image" disabled={busy} hidden onChange={e => { accept(e.target.files[0]); e.target.value = ''; }}/>
    <input ref={camera} type="file" accept="image/*" capture="environment" aria-label="Take plant photo" disabled={busy} hidden onChange={e => { accept(e.target.files[0]); e.target.value = ''; }}/>
    {preview ? <div className="selected-image"><img src={preview} alt={t('uploadTitle')}/><button className="image-remove" aria-label={t('removePhoto')} disabled={busy} onClick={onClear}><X size={18}/></button><div className="image-caption"><ImagePlus size={16}/><span>{file.name}</span><small>{(file.size / 1024 / 1024).toFixed(1)} MB</small></div></div> : <div className={'dropzone ' + (dragging ? 'dragging' : '')} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); accept(e.dataTransfer.files[0]); }}><div className="upload-icon"><UploadCloud size={36} strokeWidth={1.5}/></div><h3>{t('dropTitle')}</h3><p>{t('dropDescription')}</p><button className="outline-button" disabled={busy} onClick={() => input.current.click()}>{t('chooseImage')}<ArrowUpRight size={17}/></button><small>{t('fileTypes')}</small></div>}
    <div className="upload-actions"><button className="camera-button" disabled={busy} onClick={() => camera.current.click()}><Camera size={19}/>{t('takePhoto')}</button>{preview && <button className="text-button" disabled={busy} onClick={() => input.current.click()}>{t('changePhoto')}</button>}</div>
    <button className="primary-button analyse-button" disabled={!file || busy || !ready} onClick={onAnalyse}>{busy ? <><LoaderCircle className="spin" size={20}/>{t('analysing')}</> : <>{t('analyseButton')}<ArrowUpRight size={20}/></>}</button>
    <p className="privacy-note"><ShieldCheck size={14}/>{t('privacy')}</p>
  </section>;
}
