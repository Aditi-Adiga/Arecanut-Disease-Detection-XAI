import { useRef, useState } from 'react';
import { UploadCloud, Camera, ImagePlus, X, ArrowUpRight, LoaderCircle } from 'lucide-react';

export default function ImageUpload({ file, preview, busy, ready, onFile, onAnalyse, onClear, onError }) {
  const input = useRef(null), camera = useRef(null);
  const [dragging, setDragging] = useState(false);
  function accept(candidate) {
    if (!candidate || busy) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(candidate.type)) { onError('Choose a JPEG, PNG or WebP image.'); return; }
    if (candidate.size > 10 * 1024 * 1024) { onError('The image must be 10 MB or smaller.'); return; }
    onFile(candidate);
  }
  return <section className="upload-card card">
    <div className="section-heading"><span className="step">01</span><h2>Add a plant photo</h2><span className="tiny-label">LEAF OR NUT</span></div>
    <input ref={input} type="file" accept="image/jpeg,image/png,image/webp" aria-label="Choose plant image" disabled={busy} hidden onChange={e => { accept(e.target.files[0]); e.target.value = ''; }} />
    <input ref={camera} type="file" accept="image/*" capture="environment" aria-label="Take plant photo" disabled={busy} hidden onChange={e => { accept(e.target.files[0]); e.target.value = ''; }} />
    {preview ? <div className="selected-image"><img src={preview} alt="Selected arecanut leaf or nut" /><button className="image-remove" aria-label="Remove selected image" disabled={busy} onClick={onClear}><X size={18}/></button><div className="image-caption"><ImagePlus size={16}/><span>{file.name}</span></div></div> :
      <div className={`dropzone ${dragging ? 'dragging' : ''}`} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); accept(e.dataTransfer.files[0]); }}>
        <div className="upload-icon"><UploadCloud size={32} strokeWidth={1.4}/></div><h3>A clearer photo. A better insight.</h3><p>Drag and drop your photo here, or choose<br className="desktop-break"/> one from your device.</p>
        <button className="outline-button" disabled={busy} onClick={() => input.current.click()}>Choose an image <ArrowUpRight size={16}/></button><small>JPG, PNG or WebP · up to 10 MB</small>
      </div>}
    <div className="upload-actions"><button className="camera-button" disabled={busy} onClick={() => camera.current.click()}><Camera size={18}/> Use camera</button>{preview && <button className="text-button" disabled={busy} onClick={() => input.current.click()}>Change photo</button>}</div>
    <button className="primary-button analyse-button" disabled={!file || busy || !ready} onClick={onAnalyse}>{busy ? <><LoaderCircle className="spin" size={19}/> Analysing your photo…</> : <>Analyse plant health <ArrowUpRight size={19}/></>}</button>
    <p className="privacy-note">Your photo is processed by this server. It is not uploaded to a third-party AI service.</p>
  </section>;
}
