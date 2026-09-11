import React from 'react';

/* ============================================
   TeacherAssist – OCR Review UI (Stufe 9)
   ============================================
   Neue Datei statt Ergänzung der 149-KB components.jsx (siehe Auftrag).
   Wird von src/main.jsx VOR components.jsx importiert, damit
   window.CameraModal etc. existieren, bevor components.jsx (ChatInput)
   danach sucht. Genau wie components.jsx/tweaks-panel.jsx ist dies ein
   window-global Skript, kein ES-Modul mit echten Exporten -- Querverweise
   (Icons, React) laufen über den globalen Scope, siehe Object.assign(window,
   ...) am Dateiende.
*/

/* ---------- Bildqualität: Fehlercodes -> deutsche Erklärung ---------- */
const OCR_QUALITY_ISSUE_MESSAGES = {
  too_blurry: () => 'Das Foto ist unscharf. Halte das Handy ruhiger oder tippe zum Fokussieren.',
  low_contrast: () => 'Zu wenig Kontrast. Fotografiere auf hellem Untergrund ohne Schatten.',
  skewed: (q) => `Das Blatt ist um ${Math.round(q?.skewDegrees ?? 0)}° verdreht. Halte die Kamera parallel zum Blatt.`,
  glare: () => 'Reflexion erkannt. Ändere den Winkel oder schalte das Blitzlicht aus.',
  too_small: () => 'Auflösung zu gering für Handschrift.',
  too_dark: () => 'Das Foto ist zu dunkel. Sorge für mehr Licht.',
  too_bright: () => 'Das Foto ist überbelichtet. Vermeide direktes Blitzlicht oder starkes Gegenlicht.',
};

function describeQualityIssue(issue, quality) {
  const fn = OCR_QUALITY_ISSUE_MESSAGES[issue];
  return fn ? fn(quality) : `Qualitätsproblem: ${issue}`;
}

/* ---------- Konsens-Markierungen: per Zeichen-Offset, nicht per Regex ----------
   Frueher wurde jede "[...?]"-Klammer per Regex im consensusText gesucht und
   der i-te Treffer mit disagreements[i] gepaart. Das ist unreparierbar: (1)
   eine Mehrwort-Spanne rendert eine einzige Klammer, die client-seitig per
   Whitespace in mehrere Tokens zerfaellt, sodass Tokenzaehlen nicht
   funktioniert, und (2) eine synthetisierte Klammer ist byte-identisch zu
   gedrucktem Text im Originaldokument (z.B. ein Mehrfachauswahlfeld
   "[ja|nein?]" auf einem Pruefungsbogen) -- nichts unterscheidet sie im Text
   selbst. Der Server liefert deshalb je Disagreement charStart/charEnd: den
   exakten Zeichenbereich seiner Klammer INNERHALB von consensusText (siehe
   Disagreement.char_start in teacherassist_core/ocr/types.py). Wir slicen
   also direkt anhand dieser Offsets, statt den Text erneut zu durchsuchen. */
function renderConsensusMarkers(consensusText, disagreements, focusedIdx) {
  const text = consensusText || '';
  const list = Array.isArray(disagreements) ? disagreements : [];

  // Degradationspfad: fehlen charStart/charEnd (z.B. ein aelterer
  // gecachter Payload vor dieser Aenderung) oder sind sie unplausibel
  // (nicht-ganzzahlig, ausserhalb des Texts, ueberlappend, nicht
  // aufsteigend), wird der Text unmarkiert gerendert. Ein unmarkierter
  // Text ist ein kleineres Problem als ein Absturz oder eine leere
  // Region.
  let lastValidEnd = 0;
  const offsetsValid = list.every((d) => {
    if (!d) return false;
    const { charStart, charEnd } = d;
    if (!Number.isInteger(charStart) || !Number.isInteger(charEnd)) return false;
    if (charStart < lastValidEnd || charEnd > text.length || charStart >= charEnd) return false;
    lastValidEnd = charEnd;
    return true;
  });

  if (!offsetsValid) {
    return [<span key="t0">{text}</span>];
  }

  const parts = [];
  let lastIndex = 0;
  list.forEach((d, i) => {
    const { charStart, charEnd } = d;
    if (charStart > lastIndex) {
      parts.push(<span key={`t${i}`}>{text.slice(lastIndex, charStart)}</span>);
    }
    const critical = !!d.critical;
    const focused = i === focusedIdx;
    parts.push(
      <mark key={`m${i}`} title={d.reason || ''} style={{
        background: critical ? 'rgba(217,54,54,0.18)' : 'rgba(245,158,11,0.20)',
        color: critical ? 'var(--danger)' : '#b45309',
        borderRadius: 4, padding: '0 3px', fontWeight: 700,
        boxShadow: focused ? `0 0 0 2px ${critical ? 'var(--danger)' : '#f59e0b'}` : 'none',
      }}>
        {text.slice(charStart, charEnd)}
      </mark>
    );
    lastIndex = charEnd;
  });
  if (lastIndex < text.length) parts.push(<span key="tail">{text.slice(lastIndex)}</span>);
  return parts;
}

/* ---------- useOcrJob: pollt einen OCR-Job, kapselt die Aktionen ---------- */
function useOcrJob(jobId, { pollMs = 1500 } = {}) {
  const [doc, setDoc] = React.useState(null);
  const [error, setError] = React.useState(null);
  const docRef = React.useRef(null);
  const timerRef = React.useRef(null);
  const abortRef = React.useRef(null);

  const applyDoc = React.useCallback((next) => {
    docRef.current = next;
    setDoc(next);
  }, []);

  const fetchOnce = React.useCallback(async () => {
    if (!jobId) return null;
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const res = await window.taFetch(`/api/v1/ocr/jobs/${jobId}`, { signal: controller.signal });
      const payload = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(payload ? window.taApi.errorMessage(payload) : `Server-Fehler ${res.status}`);
      }
      applyDoc(payload);
      setError(null);
      return payload;
    } catch (e) {
      if (e.name === 'AbortError') return null;
      setError(e.message || String(e));
      return null;
    }
  }, [jobId, applyDoc]);

  React.useEffect(() => {
    docRef.current = null;
    setDoc(null);
    setError(null);
    if (!jobId) return undefined;
    let cancelled = false;

    async function poll() {
      const data = await fetchOnce();
      if (cancelled) return;
      if (data && data.status === 'processing') {
        timerRef.current = setTimeout(poll, pollMs);
      }
    }
    poll();

    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      if (abortRef.current) abortRef.current.abort();
    };
  }, [jobId, pollMs, fetchOnce]);

  const patchRegion = React.useCallback(async (regionId, patch) => {
    if (!jobId) throw new Error('Kein OCR-Job aktiv.');
    const res = await window.taFetch(`/api/v1/ocr/jobs/${jobId}/regions/${regionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    });
    const payload = await res.json().catch(() => null);
    if (!res.ok) {
      throw new Error(payload ? window.taApi.errorMessage(payload) : `Server-Fehler ${res.status}`);
    }
    applyDoc(mergeRegionIntoDoc(docRef.current, payload));
    return payload;
  }, [jobId, applyDoc]);

  const approve = React.useCallback(async () => {
    if (!jobId) return { ok: false, message: 'Kein OCR-Job aktiv.' };
    const res = await window.taFetch(`/api/v1/ocr/jobs/${jobId}/approve`, { method: 'POST' });
    const payload = await res.json().catch(() => null);
    if (!res.ok) {
      return {
        ok: false,
        status: res.status,
        code: payload && payload.error ? payload.error.code : null,
        message: payload ? window.taApi.errorMessage(payload) : `Server-Fehler ${res.status}`,
      };
    }
    applyDoc(payload);
    return { ok: true, doc: payload };
  }, [jobId, applyDoc]);

  const refresh = React.useCallback(() => fetchOnce(), [fetchOnce]);

  return { doc, error, patchRegion, approve, refresh };
}

function mergeRegionIntoDoc(doc, patchedRegion) {
  if (!doc || !patchedRegion) return doc;
  return {
    ...doc,
    pages: doc.pages.map(page => ({
      ...page,
      regions: page.regions.map(r => (r.id === patchedRegion.id ? { ...r, ...patchedRegion } : r)),
    })),
  };
}

/* ---------- useRegionImage: Crop per taFetch+blob (nie <img src="/api/...">) ---------- */
function useRegionImage(jobId, pageIndex, regionId) {
  const [url, setUrl] = React.useState(null);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    setUrl(null);
    setError(null);
    if (!jobId || pageIndex === null || pageIndex === undefined || !regionId) return undefined;
    const controller = new AbortController();
    let objectUrl = null;
    let cancelled = false;

    (async () => {
      try {
        const res = await window.taFetch(
          `/api/v1/ocr/jobs/${jobId}/pages/${pageIndex}?region=${encodeURIComponent(regionId)}`,
          { signal: controller.signal },
        );
        if (!res.ok) throw new Error(`Server-Fehler ${res.status}`);
        const blob = await res.blob();
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      } catch (e) {
        if (e.name !== 'AbortError' && !cancelled) setError(e.message || String(e));
      }
    })();

    return () => {
      cancelled = true;
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [jobId, pageIndex, regionId]);

  return { url, error };
}

/* ---------- Kleiner Modal-Rahmen, gemeinsam für CameraModal & OcrReviewModal ---------- */
function OcrModalShell({ children, maxWidth = 480, onBackdropClick }) {
  return (
    <div
      onClick={onBackdropClick}
      style={{
        position: 'fixed', inset: 0, zIndex: 3000,
        background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: 'var(--surface)', borderRadius: 20, padding: 24,
          maxWidth, width: '100%', maxHeight: '90vh', overflowY: 'auto',
          animation: 'fadeInUp 0.25s ease', display: 'flex', flexDirection: 'column',
        }}
      >
        {children}
      </div>
    </div>
  );
}

function OcrModalHeader({ title, onClose }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
      <h3 style={{ fontWeight: 700, fontSize: 17, color: 'var(--text-primary)', margin: 0 }}>{title}</h3>
      {onClose && (
        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex' }}>
          {Icons.close}
        </button>
      )}
    </div>
  );
}

function OcrSpinner({ label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-tertiary)', fontSize: 13, padding: '20px 0' }}>
      <div style={{ width: 16, height: 16, border: '2px solid var(--accent)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.7s linear infinite', flexShrink: 0 }}></div>
      {label}
    </div>
  );
}

/* ---------- CameraModal: Aufnahme → Qualität, dann Übergabe an OcrReviewModal ---------- */
function CameraModal({ onClose, onCapture }) {
  const videoRef = React.useRef(null);
  const streamRef = React.useRef(null);
  const [stage, setStage] = React.useState('capture'); // capture | uploading | gating | blocked | create-error
  const [errMsg, setErrMsg] = React.useState('');
  const [previewUrl, setPreviewUrl] = React.useState(null);
  const [jobId, setJobId] = React.useState(null);
  const previewUrlRef = React.useRef(null);

  const { doc } = useOcrJob(stage === 'gating' ? jobId : null);

  React.useEffect(() => {
    if (stage === 'capture') startCamera();
    return () => stopCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  React.useEffect(() => () => {
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
  }, []);

  React.useEffect(() => {
    if (stage !== 'gating' || !doc || doc.status === 'processing') return;
    const firstPage = (doc.pages || [])[0];
    if (doc.status !== 'failed' && firstPage && firstPage.quality && firstPage.quality.blocking) {
      setStage('blocked');
      return;
    }
    setStage('review');
  }, [stage, doc]);

  async function startCamera() {
    setErrMsg('');
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 3840 },
          height: { ideal: 2160 },
          advanced: [{ focusMode: 'continuous' }],
        },
      });
      streamRef.current = s;
      if (videoRef.current) videoRef.current.srcObject = s;
    } catch (e) {
      setErrMsg('Kamera nicht zugänglich: ' + (e.message || e.name));
    }
  }

  function stopCamera() {
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
  }

  function setPreviewFromBlob(blob) {
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    const url = URL.createObjectURL(blob);
    previewUrlRef.current = url;
    setPreviewUrl(url);
    return url;
  }

  async function uploadAndCreateJob(blob) {
    setStage('uploading');
    try {
      const fd = new FormData();
      fd.append('classification', 'student_submission');
      fd.append('scan', blob, 'capture.jpg');
      const res = await window.taFetch('/api/v1/ocr/jobs', { method: 'POST', body: fd });
      const payload = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(payload ? window.taApi.errorMessage(payload) : `Server-Fehler ${res.status}`);
      }
      setJobId(payload.jobId);
      setStage('gating');
    } catch (e) {
      setErrMsg(e.message || String(e));
      setStage('create-error');
    }
  }

  async function capture() {
    const video = videoRef.current;
    const track = streamRef.current?.getVideoTracks?.()[0];

    // ImageCapture.takePhoto() nutzt die volle Sensorauflösung (z.B. 4032x3024
    // auf einem Handy), nicht nur den Preview-Stream (oft nur 1920x1080).
    if (window.ImageCapture && track) {
      try {
        const capture = new window.ImageCapture(track);
        const blob = await capture.takePhoto();
        stopCamera();
        setPreviewFromBlob(blob);
        uploadAndCreateJob(blob);
        return;
      } catch (e) {
        // Fällt unten auf den Canvas-Pfad zurück.
      }
    }

    if (!video || !video.videoWidth) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    stopCamera();
    // EIN Encode (0.95 statt 0.92 -- OCR reagiert empfindlicher auf
    // JPEG-Ringing an dünnen Stiftstrichen als eine reine Vorschau):
    // dieselbe Blob-Instanz liefert sowohl die Vorschau (createObjectURL)
    // als auch den Upload -- kein zweiter toDataURL()-Durchlauf mehr.
    canvas.toBlob((blob) => {
      if (!blob) return;
      setPreviewFromBlob(blob);
      uploadAndCreateJob(blob);
    }, 'image/jpeg', 0.95);
  }

  function resetToCapture() {
    if (previewUrlRef.current) { URL.revokeObjectURL(previewUrlRef.current); previewUrlRef.current = null; }
    setPreviewUrl(null);
    setJobId(null);
    setErrMsg('');
    setStage('capture');
  }

  if (stage === 'review' && jobId) {
    return (
      <OcrReviewModal
        jobId={jobId}
        onClose={onClose}
        onRetake={resetToCapture}
        onApprove={(text, approvedJobId) => { onCapture(text, approvedJobId); onClose(); }}
      />
    );
  }

  if (stage === 'blocked') {
    const firstPage = (doc?.pages || [])[0];
    const quality = firstPage?.quality;
    const issues = quality?.issues || [];
    return (
      <OcrModalShell>
        <OcrModalHeader title="📸 Arbeit fotografieren" onClose={onClose} />
        {previewUrl && <img src={previewUrl} alt="Aufnahme" style={{ width: '100%', borderRadius: 12, marginBottom: 12, display: 'block' }} />}
        <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(220,38,38,0.08)', color: 'var(--danger)', fontSize: 13, marginBottom: 12, lineHeight: 1.5 }}>
          {issues.length > 0
            ? issues.map(issue => <div key={issue}>⚠️ {describeQualityIssue(issue, quality)}</div>)
            : <div>⚠️ Das Foto konnte nicht ausreichend geprüft werden.</div>}
        </div>
        <button onClick={resetToCapture} style={{
          width: '100%', padding: '12px', borderRadius: 12,
          background: 'var(--accent)', color: '#fff', border: 'none',
          cursor: 'pointer', fontSize: 15, fontWeight: 700,
        }}>
          ↩ Neu aufnehmen
        </button>
      </OcrModalShell>
    );
  }

  return (
    <OcrModalShell>
      <OcrModalHeader title="📸 Arbeit fotografieren" onClose={onClose} />

      {stage === 'capture' && (
        <>
          {errMsg ? (
            <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(220,38,38,0.08)', color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>
              ⚠️ {errMsg}
            </div>
          ) : (
            <video ref={videoRef} autoPlay playsInline muted style={{
              width: '100%', borderRadius: 12, background: '#000',
              maxHeight: 360, objectFit: 'cover', display: 'block', marginBottom: 12,
            }} />
          )}
          <button onClick={capture} disabled={!!errMsg} style={{
            width: '100%', padding: '12px', borderRadius: 12,
            background: errMsg ? 'var(--border)' : 'var(--accent)', color: '#fff',
            border: 'none', cursor: errMsg ? 'default' : 'pointer', fontSize: 15, fontWeight: 600,
          }}>
            📸 Foto aufnehmen
          </button>
        </>
      )}

      {(stage === 'uploading' || stage === 'gating') && (
        <>
          {previewUrl && <img src={previewUrl} alt="Aufnahme" style={{ width: '100%', borderRadius: 12, marginBottom: 12, display: 'block' }} />}
          <OcrSpinner label={stage === 'uploading' ? 'Foto wird hochgeladen…' : 'Qualität wird geprüft und Text erkannt…'} />
        </>
      )}

      {stage === 'create-error' && (
        <>
          {previewUrl && <img src={previewUrl} alt="Aufnahme" style={{ width: '100%', borderRadius: 12, marginBottom: 12, display: 'block' }} />}
          <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(220,38,38,0.08)', color: 'var(--danger)', fontSize: 12, marginBottom: 12 }}>
            ⚠️ {errMsg}
          </div>
          <button onClick={resetToCapture} style={{
            width: '100%', padding: '10px', borderRadius: 10, cursor: 'pointer',
            border: '1.5px solid var(--border)', background: 'var(--surface-elevated)',
            color: 'var(--text-secondary)', fontSize: 13,
          }}>
            ↩ Neu aufnehmen
          </button>
        </>
      )}

      <div style={{ marginTop: 14, fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.6 }}>
        💡 Tipp: Auf hellem Untergrund fotografieren, Blatt gerade und parallel zur Kamera halten.
      </div>
    </OcrModalShell>
  );
}

/* ---------- OcrReviewModal: der eigentliche Review-/Freigabe-Workflow ---------- */
function OcrReviewModal({ jobId, onClose, onApprove, onRetake }) {
  const { doc, error, patchRegion, approve } = useOcrJob(jobId);
  const [focusIdx, setFocusIdx] = React.useState(0);
  const [draftText, setDraftText] = React.useState('');
  const [savingRegion, setSavingRegion] = React.useState(false);
  const [saveError, setSaveError] = React.useState(null);
  const [approving, setApproving] = React.useState(false);
  const [approveError, setApproveError] = React.useState(null);

  const flatDisagreements = React.useMemo(() => {
    const list = [];
    (doc?.pages || []).forEach(page => {
      (page.regions || []).forEach(region => {
        (region.disagreements || []).forEach((d, idxInRegion) => {
          list.push({ pageIndex: page.index, region, disagreement: d, idxInRegion });
        });
      });
    });
    return list;
  }, [doc]);

  const current = flatDisagreements[focusIdx] || null;
  const currentRegion = current?.region || null;

  const { url: cropUrl } = useRegionImage(jobId, current?.pageIndex ?? null, currentRegion?.id ?? null);

  React.useEffect(() => {
    if (!currentRegion) { setDraftText(''); return; }
    const referenceCandidate = currentRegion.candidates.find(c => c.engine === currentRegion.referenceEngine);
    setDraftText(
      currentRegion.selectedText
      ?? referenceCandidate?.text
      ?? currentRegion.candidates[0]?.text
      ?? ''
    );
    setSaveError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentRegion?.id]);

  React.useEffect(() => {
    if (focusIdx >= flatDisagreements.length) setFocusIdx(Math.max(0, flatDisagreements.length - 1));
  }, [flatDisagreements.length, focusIdx]);

  const engineFailures = React.useMemo(() => {
    const map = new Map();
    (doc?.pages || []).forEach(p => (p.engineFailures || []).forEach(f => {
      if (!map.has(f.engine)) map.set(f.engine, f.reason);
    }));
    return Array.from(map, ([engine, reason]) => ({ engine, reason }));
  }, [doc]);

  const successfulEngineCount = React.useMemo(() => {
    const set = new Set();
    (doc?.pages || []).forEach(p => (p.regions || []).forEach(r => (r.candidates || []).forEach(c => set.add(c.engine))));
    return set.size;
  }, [doc]);

  const criticalRegions = React.useMemo(() => {
    const list = [];
    (doc?.pages || []).forEach(p => (p.regions || []).forEach(r => {
      if ((r.disagreements || []).some(d => d.critical)) list.push(r);
    }));
    return list;
  }, [doc]);
  const unresolvedCriticalCount = criticalRegions.filter(r => !r.editedByTeacher).length;

  async function commitCandidate(regionId, candidateEngine) {
    setSavingRegion(true); setSaveError(null);
    try {
      await patchRegion(regionId, { candidateEngine });
    } catch (e) {
      setSaveError(e.message || String(e));
    }
    setSavingRegion(false);
  }

  async function commitText() {
    if (!currentRegion) return;
    setSavingRegion(true); setSaveError(null);
    try {
      await patchRegion(currentRegion.id, { text: draftText });
    } catch (e) {
      setSaveError(e.message || String(e));
    }
    setSavingRegion(false);
  }

  React.useEffect(() => {
    function onKeyDown(e) {
      const tag = (e.target && e.target.tagName || '').toLowerCase();
      if (tag === 'textarea' || tag === 'input') return;
      if (flatDisagreements.length === 0) return;
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        setFocusIdx(i => Math.max(0, i - 1));
      } else if (e.key === 'ArrowRight' || e.key === 'Enter') {
        e.preventDefault();
        setFocusIdx(i => Math.min(flatDisagreements.length - 1, i + 1));
      } else if (/^[1-9]$/.test(e.key) && currentRegion) {
        const idx = parseInt(e.key, 10) - 1;
        const candidate = currentRegion.candidates[idx];
        if (candidate) commitCandidate(currentRegion.id, candidate.engine);
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flatDisagreements.length, currentRegion]);

  async function handleApprove() {
    setApproving(true); setApproveError(null);
    const result = await approve();
    setApproving(false);
    if (!result.ok) { setApproveError(result.message); return; }
    const fullText = (result.doc.pages || []).map(p => p.text || '').join('\n\n').trim();
    // Lose gekoppelter Kanal statt Prop-Drilling: OcrReviewModal wird sowohl
    // aus CameraModal heraus als auch (nach einem 409 OCR_APPROVAL_REQUIRED)
    // direkt von app.jsx aus gestartet -- app.jsx kann diese Datei nicht per
    // Prop erreichen, wenn die Modal-Instanz aus CameraModal/components.jsx
    // stammt. Ein window-CustomEvent deckt beide Aufrufer mit einer einzigen
    // Stelle ab (gleiches Muster wie api-client.js' 'teacherassist:bootstrap').
    window.dispatchEvent(new CustomEvent('teacherassist:ocr-approved', { detail: { jobId, text: fullText } }));
    onApprove && onApprove(fullText, jobId);
  }

  const engineFailureBanner = engineFailures.length > 0 && (
    <div style={{
      padding: '10px 14px', borderRadius: 10, marginBottom: 12,
      background: 'rgba(245,158,11,0.12)', border: '1px solid #f59e0b',
      color: '#92400e', fontSize: 12.5, lineHeight: 1.5,
    }}>
      {engineFailures.map(f => (
        <div key={f.engine}>
          ⚠ Engine „{f.engine}" nicht verfügbar{f.reason ? ` (${f.reason})` : ''} – Ergebnis beruht auf {successfulEngineCount || 1} Erkennungssystem{(successfulEngineCount || 1) === 1 ? '' : 'en'}.
        </div>
      ))}
    </div>
  );

  if (error && !doc) {
    return (
      <OcrModalShell maxWidth={480}>
        <OcrModalHeader title="OCR-Review" onClose={onClose} />
        <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(220,38,38,0.08)', color: 'var(--danger)', fontSize: 13 }}>
          ⚠️ {error}
        </div>
      </OcrModalShell>
    );
  }

  if (!doc || doc.status === 'processing') {
    return (
      <OcrModalShell maxWidth={480}>
        <OcrModalHeader title="OCR-Review" onClose={onClose} />
        <OcrSpinner label="Erkenne Text…" />
      </OcrModalShell>
    );
  }

  if (doc.status === 'failed') {
    const isCloudBlocked = doc.errorCode === 'cloud_blocked';
    return (
      <OcrModalShell maxWidth={480}>
        <OcrModalHeader title="OCR-Review" onClose={onClose} />
        <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(220,38,38,0.08)', color: 'var(--danger)', fontSize: 13, lineHeight: 1.5, marginBottom: 12 }}>
          {isCloudBlocked
            ? 'Die Verarbeitung wurde gestoppt, weil eine Erkennungs-Engine Daten an einen externen Dienst senden wollte. Schülerarbeiten werden ausschließlich lokal verarbeitet.'
            : `⚠️ Die Erkennung ist fehlgeschlagen${doc.error ? ': ' + doc.error : '.'}`}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {onRetake && (
            <button onClick={onRetake} style={{
              flex: 1, padding: '10px', borderRadius: 10, cursor: 'pointer',
              border: '1.5px solid var(--border)', background: 'var(--surface-elevated)',
              color: 'var(--text-secondary)', fontSize: 13,
            }}>
              ↩ Neu aufnehmen
            </button>
          )}
          <button onClick={onClose} style={{
            flex: 1, padding: '10px', borderRadius: 10, cursor: 'pointer',
            border: 'none', background: 'var(--accent)', color: '#fff', fontSize: 13, fontWeight: 600,
          }}>
            Schließen
          </button>
        </div>
      </OcrModalShell>
    );
  }

  // Keine Diskrepanzen: Freigabe ist unmittelbar möglich, kein Vergleich nötig.
  if (flatDisagreements.length === 0) {
    return (
      <OcrModalShell maxWidth={560}>
        <OcrModalHeader title="OCR-Review" onClose={onClose} />
        {engineFailureBanner}
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.6 }}>
          ✅ Keine unklaren Stellen gefunden. Der erkannte Text kann direkt freigegeben werden.
        </div>
        {approveError && (
          <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(220,38,38,0.08)', color: 'var(--danger)', fontSize: 12, marginBottom: 12 }}>
            ⚠️ {approveError}
          </div>
        )}
        <button onClick={handleApprove} disabled={approving || doc.status !== 'needs_review'} style={{
          width: '100%', padding: '12px', borderRadius: 12,
          background: (approving || doc.status !== 'needs_review') ? 'var(--border)' : 'var(--accent)', color: '#fff',
          border: 'none', cursor: (approving || doc.status !== 'needs_review') ? 'default' : 'pointer', fontSize: 15, fontWeight: 700,
        }}>
          {doc.status !== 'needs_review' ? 'Bereits freigegeben' : (approving ? 'Wird freigegeben…' : '✅ OCR freigeben')}
        </button>
      </OcrModalShell>
    );
  }

  // doc.status !== 'needs_review' spiegelt OCRJobStore.approve()'s eigene
  // Vorbedingung (store.py: "der Job muss Status NEEDS_REVIEW haben"), damit
  // der Button niemals ein 409 OCR_NOT_READY zulaesst, das die Lehrkraft
  // nicht kommen sehen konnte (z.B. bereits in einem anderen Tab freigegeben).
  const approveDisabled = approving || unresolvedCriticalCount > 0 || doc.status !== 'needs_review';
  const approveLabel = doc.status !== 'needs_review'
    ? 'Bereits freigegeben'
    : unresolvedCriticalCount > 0
    ? `Noch ${unresolvedCriticalCount} kritische Stelle${unresolvedCriticalCount === 1 ? '' : 'n'}`
    : (approving ? 'Wird freigegeben…' : '✅ OCR freigeben');

  return (
    <OcrModalShell maxWidth={880}>
      <OcrModalHeader title="OCR-Review" onClose={onClose} />
      {engineFailureBanner}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, marginBottom: 12, fontSize: 13, color: 'var(--text-secondary)' }}>
        <button
          onClick={() => setFocusIdx(i => Math.max(0, i - 1))}
          disabled={focusIdx === 0}
          style={{ background: 'none', border: 'none', cursor: focusIdx === 0 ? 'default' : 'pointer', color: focusIdx === 0 ? 'var(--text-tertiary)' : 'var(--accent)', fontSize: 15, fontWeight: 700 }}
        >‹ zurück</button>
        <span>{focusIdx + 1} / {flatDisagreements.length}</span>
        <button
          onClick={() => setFocusIdx(i => Math.min(flatDisagreements.length - 1, i + 1))}
          disabled={focusIdx === flatDisagreements.length - 1}
          style={{ background: 'none', border: 'none', cursor: focusIdx === flatDisagreements.length - 1 ? 'default' : 'pointer', color: focusIdx === flatDisagreements.length - 1 ? 'var(--text-tertiary)' : 'var(--accent)', fontSize: 15, fontWeight: 700 }}
        >weiter ›</button>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {/* Links: Bildausschnitt der Region */}
        <div style={{ flex: '1 1 300px', minWidth: 260 }}>
          <div style={{
            borderRadius: 12, overflow: 'hidden', background: 'var(--surface-elevated)',
            border: '1px solid var(--border)', minHeight: 160, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
          }}>
            {cropUrl
              ? <img src={cropUrl} alt="Ausschnitt" style={{ width: '100%', display: 'block' }} />
              : <div style={{ padding: 20, color: 'var(--text-tertiary)', fontSize: 12 }}>Bildausschnitt wird geladen…</div>}
          </div>
          {currentRegion?.editedByTeacher && (
            <div style={{ marginTop: 8, fontSize: 12, color: '#2a9d5c', fontWeight: 600 }}>✓ Region bearbeitet</div>
          )}
        </div>

        {/* Rechts: Transkript + Kandidaten */}
        <div style={{ flex: '1 1 340px', minWidth: 280 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 5 }}>
            Konsenstext (fragliche Stellen markiert):
          </div>
          <div style={{
            padding: '10px 12px', borderRadius: 10, background: 'var(--surface-elevated)',
            border: '1px solid var(--border)', fontSize: 13.5, lineHeight: 1.7,
            color: 'var(--text-primary)', marginBottom: 14, whiteSpace: 'pre-wrap',
          }}>
            {renderConsensusMarkers(currentRegion?.consensusText, currentRegion?.disagreements, current?.idxInRegion)}
          </div>

          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
            Vorschläge der Erkennungssysteme:
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
            {(currentRegion?.candidates || []).map((c, idx) => (
              <label key={c.engine} style={{
                display: 'flex', alignItems: 'flex-start', gap: 8, padding: '8px 10px',
                borderRadius: 8, border: '1.5px solid var(--border)', cursor: 'pointer', fontSize: 13,
                background: draftText === c.text ? 'var(--accent-soft)' : 'transparent',
              }}>
                <input
                  type="radio"
                  name={`ocr-candidate-${currentRegion.id}`}
                  checked={draftText === c.text}
                  onChange={() => { setDraftText(c.text); commitCandidate(currentRegion.id, c.engine); }}
                  style={{ marginTop: 3 }}
                />
                <span>
                  <strong>{idx + 1}. {c.engine}</strong>{' '}
                  <span style={{ color: 'var(--text-secondary)' }}>({Math.round(c.confidence * 100)}%)</span>
                  <br />
                  <span>{c.text || <em style={{ color: 'var(--text-tertiary)' }}>(leer)</em>}</span>
                </span>
              </label>
            ))}
            {engineFailures
              .filter(f => !(currentRegion?.candidates || []).some(c => c.engine === f.engine))
              .map(f => (
                <div key={f.engine} style={{
                  display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px',
                  borderRadius: 8, border: '1.5px dashed var(--border)', fontSize: 12,
                  color: 'var(--text-tertiary)',
                }}>
                  {f.engine} nicht verfügbar{f.reason ? ` – ${f.reason}` : ''}
                </div>
              ))}
          </div>

          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 5 }}>
            Oder Text frei bearbeiten:
          </div>
          <textarea
            value={draftText}
            onChange={e => setDraftText(e.target.value)}
            onBlur={commitText}
            style={{
              width: '100%', padding: '9px 13px', borderRadius: 10, boxSizing: 'border-box',
              border: '1.5px solid var(--border)', background: 'var(--surface-input)',
              color: 'var(--text-primary)', fontSize: 13, fontFamily: 'inherit',
              resize: 'vertical', minHeight: 70,
            }}
          />
          {savingRegion && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>Wird gespeichert…</div>}
          {saveError && <div style={{ fontSize: 11, color: 'var(--danger)', marginTop: 4 }}>⚠️ {saveError}</div>}
        </div>
      </div>

      {approveError && (
        <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(220,38,38,0.08)', color: 'var(--danger)', fontSize: 12, marginTop: 14 }}>
          ⚠️ {approveError}
        </div>
      )}

      <button onClick={handleApprove} disabled={approveDisabled} style={{
        width: '100%', padding: '12px', borderRadius: 12, marginTop: 16,
        background: approveDisabled ? 'var(--border)' : 'var(--accent)',
        color: approveDisabled ? 'var(--text-tertiary)' : '#fff',
        border: 'none', cursor: approveDisabled ? 'default' : 'pointer', fontSize: 15, fontWeight: 700,
      }}>
        {approveLabel}
      </button>
      <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-tertiary)', textAlign: 'center' }}>
        Pfeiltasten: navigieren · 1–9: Vorschlag wählen · Enter: bestätigen
      </div>
    </OcrModalShell>
  );
}

/* ---------- OcrSettingsSection: Engines, Qualität, Aufbewahrung ---------- */
// Bewusst KEIN hardcodiertes Katalog-Array von Engine-IDs/Labels mehr: das ist
// bereits einmal live gealtert (ein vier Zeilen langer Katalog markierte
// "ollama_vlm" -- unter der falschen ID "vlm" -- als "noch nicht
// implementiert", obwohl die Engine zu dem Zeitpunkt längst registriert war,
// siehe engines/__init__.py:ENGINE_FACTORIES). Diese Sektion rendert daher
// AUSSCHLIESSLICH aus dem, was /api/v1/bootstrap unter "ocrEngines" (Liste
// von EngineStatus.to_dict(): name/kind/available/reason/modelId/
// resolvedModelId/capabilities)
// tatsächlich zurückgibt -- egal welche Engine-Namen ENGINE_FACTORIES gerade
// kennt. Eine Engine, die noch in keiner Einstellung referenziert ist,
// erscheint hier folgerichtig nicht von selbst; das "Engine hinzufügen"-Feld
// unten deckt genau diesen Fall ab, ohne dass wir die Namen der Engines
// selbst kennen müssten.
function describeEngineReason(reason) {
  if (!reason) return { label: '', detail: '', offerDownload: false };
  const colonIdx = reason.indexOf(':');
  const prefix = colonIdx === -1 ? reason : reason.slice(0, colonIdx);
  const rest = colonIdx === -1 ? '' : reason.slice(colonIdx + 1);
  switch (prefix) {
    case 'not_installed':
      return { label: 'Komponenten fehlen', detail: rest, offerDownload: false };
    case 'binary_not_found':
      return {
        label: rest === 'tesseract' ? 'Tesseract ist nicht installiert' : `Programm nicht gefunden${rest ? ': ' + rest : ''}`,
        detail: '', offerDownload: false,
      };
    case 'model_not_downloaded':
    case 'model_not_pulled':
      return { label: 'Modell nicht geladen', detail: rest, offerDownload: true };
    case 'ollama_offline':
      return { label: 'Ollama läuft nicht', detail: '', offerDownload: false };
    case 'transformers_too_old':
      // Ein Download würde hier nichts beheben (das Problem ist eine zu alte
      // bereits installierte Paketversion, kein fehlendes Modell) -- daher
      // bewusst KEIN offerDownload:true, anders als bei model_not_downloaded.
      return { label: 'Nicht verfügbar: Paket-Konflikt', detail: rest, offerDownload: false };
    case 'remote_model_forbidden': {
      // rest ist der betroffene Modell-Tag, z.B. "qwen3-vl:235b-cloud" -- bei
      // recognize() (nicht bei status()) kann zusätzlich ":region=<id>"
      // angehängt sein (siehe ollama_vlm.py:_region_suffix). Für die Anzeige
      // abschneiden, den Basisnamen (vor dem ersten ":") liefert der
      // Pull-Hinweis unten in beiden Fällen richtig.
      const tag = rest.replace(/:region=.*$/, '');
      const baseName = tag.split(':')[0] || tag;
      // Kein Download-Button: das Modell IST vorhanden, es liegt nur in
      // Ollamas Cloud-Infrastruktur -- ein Download kann daran nichts
      // ändern, wie bei transformers_too_old. Das ist eine bewusste
      // Schutzmaßnahme (Schülertext soll die Maschine nicht verlassen),
      // keine Fehlfunktion -- der Ton entsprechend zurückhaltend statt alarmierend.
      return {
        label: 'Nur ein Cloud-Modell verfügbar – für Schülerarbeiten nicht zulässig',
        detail: tag
          ? `Modell „${tag}“ wird aus Datenschutzgründen nicht verwendet – Schülertext würde sonst an Ollamas Cloud-Infrastruktur gesendet. Lokale Variante laden: ollama pull ${baseName}`
          : 'Wird aus Datenschutzgründen nicht verwendet – Schülertext würde sonst an Ollamas Cloud-Infrastruktur gesendet.',
        offerDownload: false,
      };
    }
    default:
      // Unbekanntes Präfix (neue Engine, neuer Grund): roh anzeigen statt
      // verschlucken -- lieber ein technischer String als Stille.
      return { label: reason, detail: '', offerDownload: false };
  }
}

function OcrSettingsSection({ toolStatus }) {
  const bootData = window.taApi.getBootstrap() || {};
  const [settings, setSettings] = React.useState(() => bootData.settings || {});
  const [ocrEngineStatuses, setOcrEngineStatuses] = React.useState(() => bootData.ocrEngines || []);
  const [capabilities, setCapabilities] = React.useState(() => bootData.capabilities || {});
  const [saveError, setSaveError] = React.useState(null);
  const [downloads, setDownloads] = React.useState({});
  const [newEngineName, setNewEngineName] = React.useState('');
  const pendingPatchRef = React.useRef({});
  const patchTimerRef = React.useRef(null);

  React.useEffect(() => () => {
    if (patchTimerRef.current) clearTimeout(patchTimerRef.current);
  }, []);

  async function commitPatch() {
    const patch = pendingPatchRef.current;
    pendingPatchRef.current = {};
    if (Object.keys(patch).length === 0) return;
    try {
      const res = await window.taFetch('/api/v1/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      });
      const payload = await res.json().catch(() => null);
      if (!res.ok) throw new Error(payload ? window.taApi.errorMessage(payload) : `Server-Fehler ${res.status}`);
      setSettings(prev => ({ ...prev, ...(payload.settings || payload) }));
      setSaveError(null);
      const boot = await window.taApi.bootstrap(true);
      setOcrEngineStatuses(boot.ocrEngines || []);
      setCapabilities(boot.capabilities || {});
    } catch (e) {
      setSaveError(e.message || String(e));
    }
  }

  function patchSettings(partial, { immediate = false } = {}) {
    setSettings(prev => ({ ...prev, ...partial }));
    pendingPatchRef.current = { ...pendingPatchRef.current, ...partial };
    if (patchTimerRef.current) clearTimeout(patchTimerRef.current);
    if (immediate) { commitPatch(); return; }
    patchTimerRef.current = setTimeout(commitPatch, 400);
  }

  function removeEngine(id) {
    const current = settings.ocrEngines || [];
    patchSettings({ ocrEngines: current.filter(x => x !== id) }, { immediate: true });
  }

  function addEngineByName() {
    const name = newEngineName.trim();
    if (!name) return;
    const current = settings.ocrEngines || [];
    if (!current.includes(name)) patchSettings({ ocrEngines: [...current, name] }, { immediate: true });
    setNewEngineName('');
  }

  function toggleVerifyEngine(id) {
    const current = settings.ocrVerifyEngines || [];
    const next = current.includes(id) ? current.filter(x => x !== id) : [...current, id];
    patchSettings({ ocrVerifyEngines: next }, { immediate: true });
  }

  async function startModelDownload(engineId) {
    setDownloads(prev => ({ ...prev, [engineId]: { active: true, percent: 0, message: 'Download wird gestartet…', error: null } }));
    try {
      const res = await window.taFetch('/api/v1/ocr/models/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ engine: engineId }),
      });
      if (!res.ok || !res.body) {
        const payload = await res.json().catch(() => null);
        throw new Error((payload && payload.error) || `Server-Fehler ${res.status}`);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          let evt;
          try { evt = JSON.parse(line.slice(6)); } catch { continue; }
          if (evt.type === 'progress') {
            setDownloads(prev => ({ ...prev, [engineId]: { ...prev[engineId], percent: evt.percent, message: evt.status || '' } }));
          } else if (evt.type === 'status') {
            setDownloads(prev => ({ ...prev, [engineId]: { ...prev[engineId], message: evt.message } }));
          } else if (evt.type === 'done') {
            setDownloads(prev => ({ ...prev, [engineId]: { active: false, percent: 100, message: 'Fertig installiert.', error: null } }));
            window.taApi.bootstrap(true).then(boot => {
              setOcrEngineStatuses(boot.ocrEngines || []);
              setCapabilities(boot.capabilities || {});
            });
          } else if (evt.type === 'error') {
            setDownloads(prev => ({ ...prev, [engineId]: { active: false, percent: 0, message: '', error: evt.message } }));
          }
        }
      }
    } catch (e) {
      setDownloads(prev => ({ ...prev, [engineId]: { active: false, percent: 0, message: '', error: e.message || String(e) } }));
    }
  }

  const disabled = toolStatus !== 'online';
  const verifyEngines = settings.ocrVerifyEngines || [];

  return (
    <div>
      {disabled && (
        <div style={{ padding: '8px 12px', borderRadius: 8, background: 'rgba(107,103,96,0.12)', color: 'var(--text-secondary)', fontSize: 12, marginBottom: 12 }}>
          Tool-Server offline – Einstellungen können erst gespeichert werden, wenn die Verbindung wiederhergestellt ist.
        </div>
      )}
      {saveError && (
        <div style={{ padding: '8px 12px', borderRadius: 8, background: 'rgba(220,38,38,0.08)', color: 'var(--danger)', fontSize: 12, marginBottom: 12 }}>
          ⚠️ {saveError}
        </div>
      )}

      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10, lineHeight: 1.6 }}>
        {capabilities.ocrConsensus
          ? 'Mindestens zwei Erkennungssysteme sind aktiv – Ergebnisse werden gegeneinander geprüft (Konsens).'
          : 'Weniger als zwei Erkennungssysteme sind aktiv – die Konsensprüfung ist aktuell inaktiv, Ergebnisse eines einzelnen Systems werden nicht gegengeprüft.'}
      </div>

      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>Erkennungssysteme</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 10 }}>
        {ocrEngineStatuses.length === 0 && (
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Keine Erkennungssysteme aktiviert.</div>
        )}
        {ocrEngineStatuses.map(status => {
          const info = describeEngineReason(status.reason);
          const download = downloads[status.name];
          const badgeColor = status.available ? '#2a9d5c' : (info.offerDownload ? '#f59e0b' : 'var(--danger)');
          const badgeIcon = status.available ? '✅' : (info.offerDownload ? '⬇' : '❌');
          const badgeLabel = status.available ? 'verfügbar' : (info.label || 'nicht verfügbar');
          return (
            <div key={status.name} style={{
              padding: '10px 12px', borderRadius: 10, border: '1px solid var(--border)',
              background: 'var(--surface-input)',
            }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: disabled ? 'default' : 'pointer' }}>
                <input
                  type="checkbox"
                  checked
                  disabled={disabled}
                  onChange={() => removeEngine(status.name)}
                />
                <span style={{ flex: 1, fontSize: 13, color: 'var(--text-primary)' }}>
                  {status.name} <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>({status.kind})</span>
                </span>
                <span style={{ fontSize: 12, color: badgeColor, fontWeight: 600 }}>{badgeIcon} {badgeLabel}</span>
              </label>
              {!status.available && info.detail && (
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4, marginLeft: 26 }}>
                  {info.detail}
                </div>
              )}
              {status.resolvedModelId && status.resolvedModelId !== status.modelId && (
                // Bug 2: _resolve_vision_model() (ollama_vlm.py) darf per
                // Praefix-Match ein ANDERES, tatsaechlich vorhandenes Modell
                // waehlen als das konfigurierte -- das ist keine Fehlfunktion
                // (der Job laeuft), aber die Lehrkraft muss sehen koennen,
                // welches Modell tatsaechlich die Erkennung liefert, statt
                // stillschweigend von den konfigurierten Ergebnissen
                // abzuweichen.
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4, marginLeft: 26 }}>
                  Konfiguriertes Modell „{status.modelId}“ nicht gefunden – verwendet wird stattdessen „{status.resolvedModelId}“.
                </div>
              )}
              {info.offerDownload && !download?.active && (
                <button onClick={() => startModelDownload(status.name)} disabled={disabled} style={{
                  marginTop: 8, marginLeft: 26, padding: '6px 12px', borderRadius: 8, fontSize: 12,
                  border: '1.5px solid var(--accent)', background: 'transparent', color: 'var(--accent)', cursor: 'pointer',
                }}>
                  ⬇ Modell herunterladen
                </button>
              )}
              {download?.active && (
                <div style={{ marginTop: 8, marginLeft: 26, fontSize: 11, color: 'var(--text-secondary)' }}>
                  {download.message} {download.percent ? `(${download.percent}%)` : ''}
                </div>
              )}
              {download?.error && (
                <div style={{ marginTop: 8, marginLeft: 26, fontSize: 11, color: 'var(--danger)' }}>⚠️ {download.error}</div>
              )}
            </div>
          );
        })}
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          type="text"
          value={newEngineName}
          onChange={e => setNewEngineName(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') addEngineByName(); }}
          disabled={disabled}
          placeholder="Engine-Kennung (z.B. von der Administration)"
          style={{
            flex: 1, padding: '7px 10px', borderRadius: 8, boxSizing: 'border-box',
            border: '1.5px solid var(--border)', background: 'var(--surface-input)', color: 'var(--text-primary)', fontSize: 12,
          }}
        />
        <button onClick={addEngineByName} disabled={disabled || !newEngineName.trim()} style={{
          padding: '7px 14px', borderRadius: 8, fontSize: 12, fontWeight: 600,
          border: '1.5px solid var(--accent)', background: 'transparent', color: 'var(--accent)',
          cursor: (disabled || !newEngineName.trim()) ? 'default' : 'pointer', opacity: (disabled || !newEngineName.trim()) ? 0.5 : 1,
        }}>
          + Aktivieren
        </button>
      </div>

      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>Scan-Qualität (Ziel-DPI)</div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {[200, 350, 600].map(dpi => (
          <button key={dpi} disabled={disabled} onClick={() => patchSettings({ ocrTargetDpi: dpi }, { immediate: true })} style={{
            flex: 1, padding: '8px', borderRadius: 8, cursor: disabled ? 'default' : 'pointer',
            border: '1.5px solid', borderColor: settings.ocrTargetDpi === dpi ? 'var(--accent)' : 'var(--border)',
            background: settings.ocrTargetDpi === dpi ? 'var(--accent)' : 'var(--surface-input)',
            color: settings.ocrTargetDpi === dpi ? '#fff' : 'var(--text-secondary)', fontSize: 13, fontWeight: 600,
          }}>{dpi} DPI</button>
        ))}
      </div>

      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>Fach (optional)</div>
      <input
        type="text"
        disabled={disabled}
        value={settings.ocrSubject || ''}
        onChange={e => patchSettings({ ocrSubject: e.target.value })}
        placeholder="z.B. Physik, Mathematik…"
        style={{
          width: '100%', padding: '8px 12px', borderRadius: 8, boxSizing: 'border-box', marginBottom: 16,
          border: '1.5px solid var(--border)', background: 'var(--surface-input)', color: 'var(--text-primary)', fontSize: 13,
        }}
      />

      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
        Mindest-Übereinstimmung ({Math.round((settings.ocrMinAgreement ?? 0.98) * 100)}%)
      </div>
      <input
        type="range" min="0.5" max="1" step="0.01" disabled={disabled}
        value={settings.ocrMinAgreement ?? 0.98}
        onChange={e => patchSettings({ ocrMinAgreement: parseFloat(e.target.value) })}
        style={{ width: '100%', marginBottom: 16 }}
      />

      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>Gerät (für HTR-Modell)</div>
      <select
        disabled={disabled}
        value={settings.ocrDevice || 'auto'}
        onChange={e => patchSettings({ ocrDevice: e.target.value }, { immediate: true })}
        style={{
          width: '100%', padding: '8px 12px', borderRadius: 8, marginBottom: 16,
          border: '1.5px solid var(--border)', background: 'var(--surface-input)', color: 'var(--text-primary)', fontSize: 13,
        }}
      >
        <option value="auto">Automatisch</option>
        <option value="cpu">CPU</option>
        <option value="cuda">GPU (CUDA)</option>
      </select>

      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>Verifizierung (zweiter Leser)</div>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8, lineHeight: 1.6 }}>
        Die Verifizierungs-Engine liest nicht jede Zeile erneut, sondern nur strittige oder schwach
        gestützte Regionen – auf diesem Rechner braucht z.B. ein Vision-Sprachmodell rund 90 Sekunden
        pro Zeile, das flächendeckend einzusetzen wäre nicht praktikabel.
      </div>
      {ocrEngineStatuses.length === 0 ? (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 12 }}>
          Erst ein Erkennungssystem oben aktivieren, um es hier als Verifizierer auszuwählen.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
          {ocrEngineStatuses.map(status => (
            <label key={status.name} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: disabled ? 'default' : 'pointer' }}>
              <input
                type="checkbox" disabled={disabled}
                checked={verifyEngines.includes(status.name)}
                onChange={() => toggleVerifyEngine(status.name)}
              />
              <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>{status.name} als Verifizierer nutzen</span>
            </label>
          ))}
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Max. verifizierte Regionen pro Dokument</span>
        <input
          type="number" min="0" max="200" disabled={disabled}
          value={settings.ocrMaxVerifyRegions ?? 12}
          onChange={e => patchSettings({ ocrMaxVerifyRegions: parseInt(e.target.value, 10) || 0 })}
          style={{ width: 70, padding: '6px 8px', borderRadius: 8, border: '1.5px solid var(--border)', background: 'var(--surface-input)', color: 'var(--text-primary)', fontSize: 13 }}
        />
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Zeitlimit pro Vision-Sprachmodell-Aufruf</span>
        <input
          type="number" min="1" max="600" disabled={disabled}
          value={settings.ocrVlmTimeoutS ?? 240}
          onChange={e => patchSettings({ ocrVlmTimeoutS: parseInt(e.target.value, 10) || 1 })}
          style={{ width: 70, padding: '6px 8px', borderRadius: 8, border: '1.5px solid var(--border)', background: 'var(--surface-input)', color: 'var(--text-primary)', fontSize: 13 }}
        />
        <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Sekunden</span>
      </div>

      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>Aufbewahrung</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Scans löschen nach</span>
        <input
          type="number" min="1" max="365" disabled={disabled}
          value={settings.ocrRetentionDays ?? 7}
          onChange={e => patchSettings({ ocrRetentionDays: parseInt(e.target.value, 10) || 1 })}
          style={{ width: 70, padding: '6px 8px', borderRadius: 8, border: '1.5px solid var(--border)', background: 'var(--surface-input)', color: 'var(--text-primary)', fontSize: 13 }}
        />
        <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Tagen</span>
      </div>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: disabled ? 'default' : 'pointer' }}>
        <input
          type="checkbox" disabled={disabled}
          checked={!!settings.ocrDeleteAfterApproval}
          onChange={e => patchSettings({ ocrDeleteAfterApproval: e.target.checked }, { immediate: true })}
        />
        <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>Scan direkt nach Freigabe löschen</span>
      </label>
    </div>
  );
}

Object.assign(window, { CameraModal, OcrReviewModal, OcrSettingsSection, useOcrJob });
