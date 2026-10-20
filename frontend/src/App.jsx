import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight, ArrowUpRight, Check, Clock3, Leaf, ShieldCheck, ScanLine, WifiOff, CircleAlert, Trash2, RefreshCw, Sun, Maximize, Camera, Sparkles } from 'lucide-react';
import Navbar from './components/Navbar';
import ImageUpload from './components/ImageUpload';
import PredictionResult from './components/PredictionResult';
import DiseaseInfo from './components/DiseaseInfo';
import ChatAssistant from './components/ChatAssistant';
import { Welcome, LanguagePicker } from './components/Welcome';
import { LanguageProvider } from './locales/LanguageContext';
import { LANGUAGES, translator } from './locales/messages';
import { localizeResult } from './locales/localizeResult';
import { analyseImage, getJson } from './services/api';
import { readHistory, saveHistory, clearHistory } from './services/history';

function initialLanguage() {
  try { const value=localStorage.getItem('arecalens-language'); return LANGUAGES.some(item => item.code===value) ? value : 'en'; }
  catch { return 'en'; }
}

export default function App() {
  const [language,setLanguage]=useState(initialLanguage), [stage,setStage]=useState('welcome');
  const [view,setView]=useState('scan'), [file,setFile]=useState(null), [preview,setPreview]=useState('');
  const [result,setResult]=useState(null), [info,setInfo]=useState(null), [guideClass,setGuideClass]=useState('Mahali_Koleroga');
  const [busy,setBusy]=useState(false), [health,setHealth]=useState(null), [error,setError]=useState('');
  const [history,setHistory]=useState(readHistory), [notice,setNotice]=useState(''), [confirmClear,setConfirmClear]=useState(false);
  const controller=useRef(null), resultRef=useRef(null), uploadRef=useRef(null);
  const t=useMemo(() => translator(language),[language]);
  const locale=LANGUAGES.find(item => item.code===language)?.locale || 'en-IN';
  const shownResult=useMemo(() => localizeResult(result,info,t),[result,info,t]);

  async function checkServer() {
    const [service,guide]=await Promise.allSettled([getJson('/api/health'),getJson('/api/diseases?language='+language)]);
    setHealth(service.status==='fulfilled' ? service.value : {model_loaded:false});
    if (guide.status==='fulfilled') setInfo(guide.value);
  }

  useEffect(() => {
    let active=true;
    const abort=new AbortController();
    async function load() {
      const [service,guide]=await Promise.allSettled([getJson('/api/health',{signal:abort.signal}),getJson('/api/diseases?language='+language,{signal:abort.signal})]);
      if(!active)return;
      setHealth(service.status==='fulfilled' ? service.value : {model_loaded:false});
      if(guide.status==='fulfilled')setInfo(guide.value);
    }
    setInfo(null); load();
    const timer=setInterval(load,30000);
    return () => {active=false;abort.abort();clearInterval(timer);};
  },[language]);
  useEffect(() => {document.documentElement.lang=language;},[language]);
  useEffect(() => () => controller.current?.abort(),[]);
  useEffect(() => {
    if(!file){setPreview('');return;}
    const url=URL.createObjectURL(file);setPreview(url);
    return () => URL.revokeObjectURL(url);
  },[file]);

  function chooseFile(next){setFile(next);setResult(null);setError('');setNotice('');}
  function continueInLanguage(){
    try{localStorage.setItem('arecalens-language',language);}catch{/* Preference storage is optional. */}
    setStage('app');
  }
  async function analyse(){
    if(!file)return;
    setBusy(true);setError('');setNotice('');
    controller.current=new AbortController();
    const timeout=setTimeout(() => controller.current.abort(),120000);
    try{
      const data=await analyseImage(file,controller.current.signal,language);
      setResult(data);setGuideClass(data.class_id);
      const saved=saveHistory(data,file.name);setHistory(saved.items);
      if(!saved.saved)setNotice(t('storageFull'));
      setTimeout(() => resultRef.current?.scrollIntoView({behavior:'smooth',block:'start'}),100);
    }catch(err){
      console.error('Screening request failed:',err);
      setError(err.name==='AbortError' ? t('timeoutError') : err.message.includes('image') ? t('unsupportedFile') : t('connectionError'));
    }finally{clearTimeout(timeout);setBusy(false);}
  }
  function removeSavedScans(){
    try{clearHistory();setHistory([]);setConfirmClear(false);}
    catch{setNotice(t('connectionError'));}
  }
  function openHistory(entry){
    setResult(entry.result);setGuideClass(entry.result.class_id);setView('scan');setError('');setNotice(t('savedResultNotice'));
    setTimeout(() => resultRef.current?.scrollIntoView({behavior:'smooth',block:'start'}),100);
  }
  function changeView(next){if(next==='guide'&&result)setGuideClass(result.class_id);setView(next);}
  const steps=[t('stepPhoto'),t('stepScreen'),t('stepUnderstand')];
  const activeStep=result ? 2 : file ? 1 : 0;

  return <LanguageProvider language={language}>
    {stage==='welcome' ? <Welcome onStart={() => setStage('language')}/> :
      stage==='language' ? <LanguagePicker language={language} onSelect={setLanguage} onContinue={continueInLanguage} onBack={() => setStage('welcome')}/> :
      <><Navbar view={view} onChange={changeView} onLanguage={() => setStage('language')}/>
        <main className="page-shell">
          <div className="page-context"><span><span className="context-dot"/>{t('context')}</span><span className={'server-state '+(health?.model_loaded?'ready':'')}>{health===null?t('connecting'):health.model_loaded?<><Check size={14}/>{t('ready')}</>:<><WifiOff size={14}/>{t('unavailable')}</>}</span></div>
          {health&&!health.model_loaded&&<div className="server-alert" role="status"><CircleAlert size={20}/><span>{t('serverHelp')}</span><button onClick={checkServer} aria-label={t('retry')}><RefreshCw size={18}/></button></div>}
          {view==='scan'&&<>
            <section className="farmer-hero"><div><span className="eyebrow"><Leaf size={14}/>{t('heroKicker')}</span><h1>{t('heroTitle')}</h1><p>{t('heroDescription')}</p><div className="hero-cta"><button onClick={() => uploadRef.current?.scrollIntoView({behavior:'smooth',block:'start'})}>{t('startScan')}<ArrowRight size={19}/></button><button onClick={() => setView('guide')}>{t('exploreGuide')}<ArrowUpRight size={17}/></button></div></div><div className="hero-leaf-mark" aria-hidden="true"><Leaf size={105} strokeWidth={.7}/><span>ARECA<br/>CATECHU</span><div className="hero-orbit one"/><div className="hero-orbit two"/></div></section>
            <ol className="scan-progress" aria-label="Analysis progress">{steps.map((label,index)=><li key={index} className={index===activeStep?'current':index<activeStep?'complete':''} aria-current={index===activeStep?'step':undefined}><span>{index<activeStep?<Check size={17}/>:index+1}</span><div><strong>{label}</strong><small>{index<activeStep?t('stepDone'):index===activeStep?t('stepReady'):t('stepWaiting')}</small></div>{index<2&&<ArrowRight size={16}/>}</li>)}</ol>
            <div className="workspace" ref={uploadRef}><div><ImageUpload file={file} preview={preview} busy={busy} ready={health?.model_loaded} onFile={chooseFile} onAnalyse={analyse} onClear={() => chooseFile(null)} onError={setError}/>{error&&<div className="error-message" role="alert"><CircleAlert size={19}/>{error}</div>}</div>
              <aside className="farmer-tips card"><span className="eyebrow">{t('tipsTitle')}</span><h2>{t('dropTitle')}</h2><p>{t('tipsDescription')}</p><div className="tip-list">{[[Sun,'tipLight'],[Maximize,'tipFill'],[Camera,'tipSteady']].map(([Icon,key],index)=><div key={key}><span><Icon size={22}/></span><div><small>0{index+1}</small><h3>{t(key)}</h3></div></div>)}</div><div className="expert-callout"><ShieldCheck size={21}/><span>{t('expertReminder')}</span></div></aside>
            </div>
            {notice&&<p className="notice" role="status">{notice}</p>}
            {shownResult&&<div ref={resultRef} className="result-section"><PredictionResult result={shownResult}/>{shownResult.status!=='unsure'&&<DiseaseInfo info={info} classId={result.class_id}/>}<p className="scope-note">{t('scope')}</p></div>}
            <section className="supported"><div className="supported-heading"><div><span className="eyebrow">{t('supportedTitle')}</span><h2>{t('guideTitle')}</h2></div><span><Sparkles size={16}/>{t('visualExplanation')}</span></div><div className="class-cards">{info&&Object.entries(info.classes).map(([id,item],index)=><button key={id} onClick={() => {setGuideClass(id);setView('guide');}}><span className={'class-symbol type-'+index}>{index<2?<Leaf size={27}/>:<ScanLine size={27}/>}</span><h3>{item.short_name}</h3><span>{t('openGuide')}<ArrowUpRight size={16}/></span></button>)}</div></section>
          </>}
          {view==='guide'&&<><section className="view-intro"><span className="eyebrow">{t('guideNav')}</span><h1>{t('guideIntro')}</h1><p>{t('guideDescription')}</p></section><DiseaseInfo info={info} classId={guideClass} onSelect={setGuideClass} referenceOnly currentResultName={result && info?.classes[result.class_id]?.short_name}/></>}
          {view==='history'&&<><section className="view-intro"><span className="eyebrow">{t('historyKicker')}</span><h1>{t('historyTitle')}</h1><p>{t('historyDescription')}</p></section>{history.length?<><div className="history-toolbar"><span>{t('savedScans',{count:history.length})}</span><button className="text-button" onClick={() => setConfirmClear(!confirmClear)}><Trash2 size={16}/>{t('clearHistory')}</button></div>{confirmClear&&<div className="notice">{t('deleteQuestion')}<button className="text-button" onClick={removeSavedScans}>{t('deleteScans')}</button><button className="text-button" onClick={() => setConfirmClear(false)}>{t('cancel')}</button></div>}<div className="history-grid">{history.map(entry=><button className="history-card card" key={entry.id} onClick={() => openHistory(entry)}><img src={entry.result.original_image} alt={t('uploadTitle')}/><div><span className={'history-status '+entry.result.status}>{t(entry.result.status==='unsure'?'unsureLabel':entry.result.status==='healthy'?'healthyLabel':'suspectedLabel')}</span><h3>{info?.classes[entry.result.class_id]?.short_name||entry.result.display_name}</h3><p>{entry.name}</p><small><Clock3 size={13}/>{new Date(entry.createdAt).toLocaleString(locale)}</small><span className="history-open">{t('viewResult')}<ArrowRight size={16}/></span></div></button>)}</div></>:<div className="empty-history card"><Clock3 size={40}/><h2>{t('emptyTitle')}</h2><p>{t('emptyDescription')}</p><button className="primary-button" onClick={() => setView('scan')}>{t('startScan')}<ArrowRight size={18}/></button></div>}</>}
          <footer><div className="footer-brand"><Leaf size={20}/><strong>ArecaLens</strong><span>{t('footer')}</span></div><p>{t('footerResearch')}</p><p className="footer-note">{t('scope')}</p>{language!=='en'&&<p className="footer-note">{t('translationDraft')}</p>}</footer>
        </main><ChatAssistant/>
      </>}
  </LanguageProvider>;
}
