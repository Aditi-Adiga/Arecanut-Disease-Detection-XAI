import { useEffect, useRef, useState } from 'react';
import { ArrowRight, ArrowUpRight, Check, Clock3, Leaf, Microscope, ShieldCheck, ScanLine, WifiOff, CircleAlert, Trash2, RefreshCw } from 'lucide-react';
import Navbar from './components/Navbar';
import ImageUpload from './components/ImageUpload';
import PredictionResult from './components/PredictionResult';
import DiseaseInfo from './components/DiseaseInfo';
import { analyseImage, getJson } from './services/api';
import { readHistory, saveHistory, clearHistory } from './services/history';

function PlantArt() {
  return <svg className="plant-art" viewBox="0 0 450 300" fill="none" aria-hidden="true"><circle cx="235" cy="160" r="123" fill="#e0e9d8"/><circle cx="235" cy="160" r="95" stroke="#bccab3" strokeDasharray="3 7"/><path d="M241 287c-9-47-10-108-2-165" stroke="#647746" strokeWidth="9"/>{[[238,127,155,30],[239,128,330,43],[238,132,115,102],[241,137,361,117],[239,139,158,188],[242,139,326,210]].map(([x,y,tx,ty],i)=><g key={i}><path d={`M${x} ${y} Q${(x+tx)/2} ${ty-45} ${tx} ${ty} Q${(x+tx)/2-10} ${ty+25} ${x} ${y}`} fill={i%2?'#3e6347':'#668350'}/><path d={`M${x} ${y} Q${(x+tx)/2} ${ty-10} ${tx} ${ty}`} stroke="#a7bc87" strokeWidth="1.5"/></g>)}<ellipse cx="228" cy="173" rx="12" ry="18" fill="#b68748"/><ellipse cx="251" cy="168" rx="12" ry="18" fill="#d3a45d"/><ellipse cx="244" cy="194" rx="12" ry="18" fill="#b78947"/><path d="M93 100V75h25M345 75h25v25M93 213v25h25M370 213v25h-25" stroke="#8ba378" strokeWidth="2"/><rect x="279" y="220" width="141" height="42" rx="10" fill="#fff"/><circle cx="300" cy="241" r="9" fill="#e8f1df"/><path d="m296 241 3 3 5-6" stroke="#477746" strokeWidth="1.5"/><text x="315" y="245" fill="#31543c" fontSize="11" fontFamily="sans-serif">A closer look, with AI</text></svg>;
}

export default function App() {
  const [view, setView] = useState('scan'), [file, setFile] = useState(null), [preview, setPreview] = useState('');
  const [result, setResult] = useState(null), [info, setInfo] = useState(null), [guideClass, setGuideClass] = useState('Mahali_Koleroga');
  const [busy, setBusy] = useState(false), [health, setHealth] = useState(null), [error, setError] = useState('');
  const [history, setHistory] = useState(readHistory), [notice, setNotice] = useState(''), [confirmClear, setConfirmClear] = useState(false);
  const controller = useRef(null), resultRef = useRef(null);
  async function checkServer() {
    try { setHealth(await getJson('/api/health')); } catch { setHealth({ model_loaded: false }); }
    try { setInfo(await getJson('/api/diseases')); } catch { /* Health message gives the recovery action. */ }
  }
  useEffect(() => { checkServer(); const timer = setInterval(checkServer, 30000); return () => { clearInterval(timer); controller.current?.abort(); }; }, []);
  useEffect(() => {
    if (!file) { setPreview(''); return; }
    const url = URL.createObjectURL(file); setPreview(url); return () => URL.revokeObjectURL(url);
  }, [file]);
  function chooseFile(next) { setFile(next); setResult(null); setError(''); setNotice(''); }
  async function analyse() {
    if (!file) return;
    setBusy(true); setError(''); setNotice('');
    controller.current = new AbortController();
    const timeout = setTimeout(() => controller.current.abort(), 120000);
    try {
      const data = await analyseImage(file, controller.current.signal);
      setResult(data); setGuideClass(data.class_id);
      const saved = saveHistory(data, file.name); setHistory(saved.items);
      if (!saved.saved) setNotice('Your result is ready, but browser storage is full. Download the report to keep it.');
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (err) { setError(err.name === 'AbortError' ? 'Analysis timed out. Check the backend and try again.' : err.message.includes('fetch') ? 'Cannot reach the API. Start the local backend, then retry.' : err.message); }
    finally { clearTimeout(timeout); setBusy(false); }
  }
  function openHistory(entry) { setResult(entry.result); setGuideClass(entry.result.class_id); setView('scan'); setError(''); setNotice('Viewing a saved result. Choose a new photo to run another analysis.'); }
  return <><Navbar view={view} onChange={setView}/><main className="page-shell">
    <div className="page-context"><span><span className="context-dot"/> ARECANUT HEALTH STUDIO</span><span className={`server-state ${health?.model_loaded ? 'ready' : ''}`}>{health === null ? 'Connecting to model…' : health.model_loaded ? <><Check size={13}/> Local model ready</> : <><WifiOff size={13}/> Model unavailable</>}</span></div>
    {health && !health.model_loaded && <div className="server-alert" role="status"><CircleAlert size={19}/><span>Start the FastAPI server and check that the model loaded. Internet is not required when the server runs on this laptop.</span><button onClick={checkServer} aria-label="Retry server connection"><RefreshCw size={17}/></button></div>}
    {view === 'scan' && <>
      <section className="hero"><div className="hero-copy"><span className="eyebrow"><span/> INTELLIGENCE ROOTED IN CARE</span><h1>Understand your plant.<br/><em>See beyond the symptoms.</em></h1><p>Screen arecanut leaves and nuts for disease patterns.<br className="desktop-break"/> Get an AI prediction, and see what informed it.</p><div className="hero-pills"><span><ShieldCheck size={15}/> Explainable results</span><span><Leaf size={15}/> Four trained classes</span></div></div><PlantArt/></section>
      <div className="workspace"><div><ImageUpload file={file} preview={preview} busy={busy} ready={health?.model_loaded} onFile={chooseFile} onAnalyse={analyse} onClear={() => chooseFile(null)} onError={setError}/>
        {error && <div className="error-message" role="alert"><CircleAlert size={18}/>{error}</div>}
        <div className="photo-tips"><span className="eyebrow">A GOOD PHOTO MAKES A DIFFERENCE</span><div><span><i>1</i>Use natural daylight</span><span><i>2</i>Fill the frame</span><span><i>3</i>Keep the camera steady</span></div></div>
      </div><aside className="insight-panel"><div className="insight-label"><Microscope size={18}/> MORE THAN A PREDICTION</div><h2>A result you can<br/><em>look into.</em></h2><p>Our model screens your photo, then highlights the regions that contributed to its prediction.</p><div className="insight-step"><span>01</span><div><h3>Identify a pattern</h3><p>MobileNetV3Small compares your photo with four learned classes.</p></div></div><div className="insight-step"><span>02</span><div><h3>See the attention</h3><p>A class activation map makes the model’s focus visible.</p></div></div><div className="insight-step"><span>03</span><div><h3>Know what to check</h3><p>Plain-language explanations and a field guide help you take the next step.</p></div></div><button onClick={() => setView('guide')} className="insight-link">Explore the disease guide <ArrowUpRight size={17}/></button><div className="insight-foot"><ShieldCheck size={17}/><span>Designed to assist observation.<br/>Expert confirmation still matters.</span></div></aside></div>
      {notice && <p className="notice" role="status">{notice}</p>}
      {result && <div ref={resultRef} className="result-section"><PredictionResult result={result}/>{result.status !== 'unsure' && <DiseaseInfo info={info} classId={guideClass} onSelect={setGuideClass}/>}<p className="scope-note">{result.scope_note}</p></div>}
      <section className="supported"><span className="eyebrow">WHAT THIS MODEL RECOGNISES</span><div><span><Leaf size={17}/> Healthy leaf</span><span><Leaf size={17}/> Healthy nut</span><span><ScanLine size={17}/> Mahali / Koleroga</span><span><ScanLine size={17}/> Yellow leaf / leaf spot</span></div></section>
    </>}
    {view === 'guide' && <><section className="view-intro"><span className="eyebrow">OBSERVE. UNDERSTAND. ASK AN EXPERT.</span><h1>The disease field guide.</h1><p>Symptoms, possible causes and care information from your project’s reference material.</p></section><DiseaseInfo info={info} classId={guideClass} onSelect={setGuideClass}/></>}
    {view === 'history' && <><section className="view-intro"><span className="eyebrow">SAVED ON THIS BROWSER</span><h1>Your recent observations.</h1><p>The latest eight scans are stored on this device. Clearing browser data removes them.</p></section>{history.length ? <><div className="history-toolbar"><span>{history.length} saved {history.length === 1 ? 'scan' : 'scans'}</span><button className="text-button" onClick={() => setConfirmClear(!confirmClear)}><Trash2 size={15}/> Clear history</button></div>{confirmClear && <div className="notice">Delete all saved scans from this browser? <button className="text-button" onClick={() => { try { clearHistory(); setHistory([]); setConfirmClear(false); } catch { setNotice('Browser storage could not be cleared.'); } }}>Delete scans</button><button className="text-button" onClick={() => setConfirmClear(false)}>Cancel</button></div>}<div className="history-grid">{history.map(entry => <button className="history-card card" key={entry.id} onClick={() => openHistory(entry)}><img src={entry.result.original_image} alt="Saved plant scan"/><div><span className={`history-status ${entry.result.status}`}>{entry.result.status === 'unsure' ? 'Not sure' : entry.result.status === 'healthy' ? 'Healthy pattern' : 'Suspected pattern'}</span><h3>{entry.result.display_name}</h3><p>{entry.name}</p><small><Clock3 size={12}/> {new Date(entry.createdAt).toLocaleString()}</small><span className="history-open">View result <ArrowRight size={15}/></span></div></button>)}</div></> : <div className="empty-history card"><Clock3 size={38}/><h2>A fresh start.</h2><p>Your observations will appear here after your first scan.</p><button className="primary-button" onClick={() => setView('scan')}>Analyse a photo <ArrowRight size={17}/></button></div>}</>}
    <footer><div className="footer-brand"><Leaf size={18}/><strong>ArecaLens</strong><span>Explainable AI-driven disease detection in arecanut plants.</span></div><p>Research prototype · English edition · Guidance awaiting expert review</p><p className="footer-note">A photo can miss early disease. This four-class model does not verify that the image contains an arecanut plant. Kannada, Hindi and Malayalam translations are pending review.</p></footer>
  </main></>;
}
