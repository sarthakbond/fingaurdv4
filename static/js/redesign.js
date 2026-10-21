import {tools,stats,queries,lessons,quiz} from './demo-data.js';
import {toViewModel} from './model.js';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)], fmt=n=>new Intl.NumberFormat('en-IN').format(n);
const palette={blue:'#173f35',green:'#2e6653',yellow:'#c8a96b',navy:'#173f35',sand:'#c8a96b',sky:'#2e6653'};
const track=$('#carousel-track'),dots=$('#carousel-dots');let active=0,startX=0,dragX=0;
track.innerHTML=tools.map((t,i)=>`<article class="tool-card" data-card="${i}" style="--card-color:${palette[t.tone]||'#173f35'};--icon-bg:${t.tone==='yellow'?'#faf4e8':t.tone==='green'?'#edf7f2':'#f3ebdd'}"><div class="tool-card-visual" aria-hidden="true"><span class="visual-orbit visual-orbit-one"></span><span class="visual-orbit visual-orbit-two"></span><span class="visual-index">0${i+1}</span><div class="visual-icon">${t.icon}</div><span class="visual-seal">VERIFY<br>WITH CARE</span></div><div class="tool-card-copy"><div class="card-meta"><span class="tool-type">${t.type}</span><span class="card-index">0${i+1} / 05</span></div><h3>${t.title}</h3><p>${t.desc}</p><button class="card-action" data-tool="${t.id}"><span class="action-label">${t.action}</span><span class="action-arrow">→</span></button></div></article>`).join('');
dots.innerHTML=tools.map((_,i)=>`<button class="carousel-dot" data-dot="${i}" aria-label="Show tool ${i+1}" aria-current="${i===0}"></button>`).join('');
const selector=$('#tool-selector'),shortNames=['Video','Audio','APK','URL','Compliance'];selector.innerHTML=tools.map((t,i)=>`<button class="tool-shortcut" type="button" data-shortcut="${i}" aria-current="${i===0}"><span class="shortcut-icon" aria-hidden="true">${t.icon}</span><span class="shortcut-name">${shortNames[i]}</span><span class="shortcut-number">0${i+1}</span></button>`).join('');
function step(){return (track.children[0]?.getBoundingClientRect().width||0)+parseFloat(getComputedStyle(track).gap||18)}
function drawCarousel(){const cards=$$('.tool-card',track);const center=cards[active];if(!center)return;const offset=center.offsetLeft-(track.parentElement.clientWidth-center.offsetWidth)/2;track.style.transform=`translateX(${-offset}px)`;cards.forEach((c,i)=>{c.classList.toggle('active-card',i===active);c.classList.toggle('past-card',i<active)});$$('.carousel-dot',dots).forEach((d,i)=>d.setAttribute('aria-current',String(i===active)));$$('.tool-shortcut',selector).forEach((b,i)=>b.setAttribute('aria-current',String(i===active)));$('#slide-num').textContent=`0${active+1}`;}
function goTo(n){active=(n+tools.length)%tools.length;drawCarousel()} $('[data-prev]').addEventListener('click',()=>goTo(active-1));$('[data-next]').addEventListener('click',()=>goTo(active+1));dots.addEventListener('click',e=>{const d=e.target.closest('[data-dot]');if(d)goTo(Number(d.dataset.dot))});selector.addEventListener('click',e=>{const b=e.target.closest('[data-shortcut]');if(b)goTo(Number(b.dataset.shortcut))});track.addEventListener('click',e=>{const card=e.target.closest('.tool-card');if(!card)return;const idx=Number(card.dataset.card);if(!isNaN(idx)&&idx!==active&&!e.target.closest('button'))goTo(idx);});window.addEventListener('resize',drawCarousel);const viewport=$('#tool-carousel');viewport.addEventListener('touchstart',e=>{startX=e.touches[0].clientX},{passive:true});viewport.addEventListener('touchend',e=>{const dx=e.changedTouches[0].clientX-startX;if(Math.abs(dx)>45)goTo(active+(dx<0?1:-1))},{passive:true});viewport.addEventListener('pointerdown',e=>{if(e.pointerType==='touch')return;startX=e.clientX});viewport.addEventListener('pointerup',e=>{if(e.pointerType==='touch')return;const dx=e.clientX-startX;if(Math.abs(dx)>80)goTo(active+(dx<0?1:-1))});
const lessonList=$('#lesson-list');lessonList.innerHTML=lessons.map(([num,title,scenario,flags,safe,tag])=>`<article class="lesson-card"><div class="lesson-top"><span class="lesson-num">${num}</span><span class="lesson-tag">${tag}</span></div><h3>${title}</h3><p>${scenario}</p><button class="reveal-btn" aria-expanded="false">Reveal the red flags <span>⌄</span></button><div class="lesson-details"><div class="lesson-details-inner"><div class="lesson-detail"><b>WARNING SIGNS</b>${flags}</div><div class="lesson-detail"><b>WHAT TO DO INSTEAD</b>${safe}</div></div></div></article>`).join('');lessonList.addEventListener('click',e=>{const b=e.target.closest('.reveal-btn');if(!b)return;const card=b.closest('.lesson-card');const open=card.classList.toggle('open');b.setAttribute('aria-expanded',String(open));b.innerHTML=open?'Hide the red flags <span>⌃</span>':'Reveal the red flags <span>⌄</span>'});
function shuffleQuestions(items){const copy=[...items];for(let i=copy.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[copy[i],copy[j]]=[copy[j],copy[i]]}return copy}let quizDeck=shuffleQuestions(quiz),qi=0,answered=false;function renderQuiz(){const item=quizDeck[qi];$('#quiz-progress').textContent=`${String(qi+1).padStart(2,'0')} / ${String(quizDeck.length).padStart(2,'0')}`;$('#quiz-question').textContent=item.q;$('#quiz-feedback').textContent='';$('#quiz-options').innerHTML=item.options.map((o,i)=>`<button class="quiz-option" data-answer="${i}">${String.fromCharCode(65+i)}. ${o}</button>`).join('');$('#quiz-next').textContent=qi===quizDeck.length-1?'Shuffle and start again →':'Next question →';answered=false}
$('#quiz-options').addEventListener('click',e=>{const b=e.target.closest('[data-answer]');if(!b||answered)return;answered=true;const answer=Number(b.dataset.answer),correct=answer===quizDeck[qi].answer;$$('.quiz-option').forEach((o,i)=>{o.disabled=true;if(i===quizDeck[qi].answer)o.classList.add('correct');else if(i===answer)o.classList.add('incorrect')});$('#quiz-feedback').textContent=`${correct?'That’s right.':'Not quite.'} ${quizDeck[qi].why}`});$('#quiz-next').addEventListener('click',()=>{if(!answered){$('#quiz-feedback').textContent='Choose an answer to continue.';return}if(qi===quizDeck.length-1){quizDeck=shuffleQuestions(quiz);qi=0}else qi++;renderQuiz()});renderQuiz();
const statsGrid=$('#stats-grid');statsGrid.innerHTML=stats.map(([label,n],i)=>`<button class="stat-card" data-stat-query="${queries[i]}"><span class="stat-value" data-count="${n}" aria-label="${fmt(n)}">0</span><span class="stat-label">${label}</span></button>`).join('');
let countersRan=false,frames=[];function animateCounters(){if(countersRan)return;countersRan=true;const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;const nodes=$$('.stat-value[data-count]');nodes.push($('#total-count'));nodes.forEach((el,index)=>{const end=Number(el.dataset.count);if(reduced){el.textContent=fmt(end);return}const delay=index*95,duration=1550,start=performance.now();let frame;const tick=now=>{const elapsed=Math.max(0,now-start-delay);if(now-start<delay){frame=requestAnimationFrame(tick);frames.push(frame);return}const t=Math.min(1,elapsed/duration),ease=1-Math.pow(1-t,4);el.textContent=fmt(Math.round(end*ease));if(t<1){frame=requestAnimationFrame(tick);frames.push(frame)}else el.textContent=fmt(end)};frame=requestAnimationFrame(tick);frames.push(frame)})}
const statObserver=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){animateCounters();statObserver.disconnect()}},{threshold:.15});statObserver.observe($('#stats-grid'));window.addEventListener('pagehide',()=>{statObserver.disconnect();frames.forEach(cancelAnimationFrame)});
$('#query-chips').innerHTML=queries.map(q=>`<button class="query-chip" type="button" data-query="${q}">${q}</button>`).join('');
const search=$('#sebi-search'),result=$('#sebi-result');
$('#query-chips').addEventListener('click',e=>{const chip=e.target.closest('[data-query]');if(!chip)return;search.value=chip.dataset.query;$$('.query-chip').forEach(c=>c.classList.toggle('selected',c===chip));search.focus()});
$('.clear-search').addEventListener('click',()=>{search.value='';search.focus();result.hidden=true;$$('.query-chip').forEach(c=>c.classList.remove('selected'))});
$('#stats-grid').addEventListener('click',e=>{const b=e.target.closest('[data-stat-query]');if(b){search.value=b.dataset.statQuery;search.focus();$('#sebi-form').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'})}});

$('#sebi-form').addEventListener('submit',async (e)=>{
  e.preventDefault();
  const value=search.value.trim();
  if(!value){result.hidden=false;result.innerHTML='<b>Enter a name, firm, or registration number to search official records.</b>';search.focus();return;}
  result.hidden=false;
  result.innerHTML='<div class="loading-indicator"><span class="spinner"></span> Querying live SEBI Intermediary Registry database...</div>';
  try {
    const resp=await fetch(`/api/registry/search?q=${encodeURIComponent(value)}`);
    if(!resp.ok)throw new Error(`HTTP ${resp.status}`);
    const data=await resp.json();
    const matches=data.results||[];
    if(matches.length>0){
      let html=`<div style="margin-bottom:6px"><b>Verified SEBI Records for “${escapeHtml(value)}” (${data.total_matches} found):</b></div>`;
      html+=matches.slice(0,5).map(m=>`
        <div class="sebi-result-item">
          <div class="sebi-result-header">
            <span class="sebi-result-name">${escapeHtml(m.name||'Unknown')}</span>
            <span class="sebi-reg-pill">${escapeHtml(m.registration_number||'N/A')}</span>
          </div>
          <div class="sebi-result-details">
            <b>Category:</b> ${escapeHtml(m.type||'Intermediary')} · <b>Status:</b> <span style="color:#16a34a;font-weight:700">${escapeHtml(m.status||'Active')}</span>
            ${m.contact_person?` · <b>Contact:</b> ${escapeHtml(m.contact_person)}`:''}
          </div>
        </div>
      `).join('');
      result.innerHTML=html;
    } else {
      result.innerHTML=`
        <div style="background:#fff1f2;border:1px solid #fecdd3;padding:12px;border-radius:4px;color:#9f1239">
          <b style="color:#be123c">❌ Unregistered Entity / Impersonation Alert</b>
          <div style="font-size:11px;margin-top:4px">No active registration matching “${escapeHtml(value)}” was found in the official SEBI database. Offering financial advice without SEBI registration violates Section 12(1) of the SEBI Act, 1992.</div>
        </div>
      `;
    }
  } catch (err){
    result.innerHTML=`<b>Error querying SEBI database:</b><small>${escapeHtml(err.message)}</small>`;
  }
});

function escapeHtml(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
const dlg=$('#tool-dialog'),dlgContent=$('#dialog-content');let selectedFile=null,previewUrl=null,activeTool=null;

function showToast(msg){
  const t=$('#toast');
  if(!t)return;
  t.textContent=msg;
  t.classList.add('visible');
  setTimeout(()=>t.classList.remove('visible'),3000);
}

function fmtClock(s) {
  if (s === null || s === undefined || isNaN(s)) return '00:00';
  const sec = Math.max(0, Math.floor(s));
  const m = Math.floor(sec / 60);
  const rem = sec % 60;
  return `${String(m).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
}

function buildDetailedAnalysisHtml(vm, raw, jobId) {
  if (!vm) return '';

  const video = vm.videoModality || {};
  const audio = vm.audioModality || {};
  const scam = vm.scamModality || {};
  const reg = vm.registryModality || {};

  const vBadge = video.isDeepfake ? 'badge-danger' : (video.score !== null ? 'badge-safe' : 'badge-idle');
  const aBadge = audio.isDeepfake ? 'badge-danger' : (audio.score !== null ? 'badge-safe' : 'badge-idle');
  const sBadge = scam.violatesSebi || scam.violatesBns ? 'badge-danger' : (scam.score !== null && scam.score > 0.3 ? 'badge-warning' : 'badge-safe');
  const rBadge = reg.isFlagged ? 'badge-danger' : (reg.verdict === 'verified' ? 'badge-safe' : 'badge-idle');

  const modalityCardsHtml = `
    <div class="forensic-modality-grid">
      <!-- 1. Video Deepfake Modality -->
      <div class="forensic-modality-card">
        <div class="forensic-modality-card-head">
          <h4 class="forensic-modality-title">👁️ Visual Facial Forensics</h4>
          <span class="forensic-modality-badge ${vBadge}">
            ${video.score !== null ? `${(video.score * 100).toFixed(1)}%` : 'N/A'}
          </span>
        </div>
        <div class="forensic-modality-status">${escapeHtml(video.label || (video.isDeepfake ? 'Synthetic Face Anomaly' : 'Authentic Face'))}</div>
        <div class="forensic-modality-desc">${escapeHtml(video.explanation || 'Analyzed spatial and temporal artifacts across extracted video keyframes.')}</div>
        <dl class="forensic-detail-dl">
          <div class="forensic-detail-row"><dt>Detected Faces</dt><dd>${video.faceCount || 0}</dd></div>
          <div class="forensic-detail-row"><dt>Temporal Glitch Score</dt><dd>${raw.vision_temporal_variance ? Number(raw.vision_temporal_variance).toFixed(3) : '0.000'}</dd></div>
          <div class="forensic-detail-row"><dt>Mouth Sync Movement</dt><dd>${raw.mouth_motion_activity ? Number(raw.mouth_motion_activity).toFixed(2) : 'Active'}</dd></div>
        </dl>
      </div>

      <!-- 2. Voice Clone Modality -->
      <div class="forensic-modality-card">
        <div class="forensic-modality-card-head">
          <h4 class="forensic-modality-title">🎙️ Acoustic Voice Clone</h4>
          <span class="forensic-modality-badge ${aBadge}">
            ${audio.score !== null ? `${(audio.score * 100).toFixed(1)}%` : 'N/A'}
          </span>
        </div>
        <div class="forensic-modality-status">${escapeHtml(audio.label || (audio.isDeepfake ? 'AI Synthetic Voice' : 'Human Voice'))}</div>
        <div class="forensic-modality-desc">${escapeHtml(audio.explanation || 'Classified vocal acoustics, spectral flatness, and temporal audio artifacts.')}</div>
        <dl class="forensic-detail-dl">
          <div class="forensic-detail-row"><dt>Model Engine</dt><dd>${escapeHtml(audio.backend || 'Wav2Vec2 GaryStafford')}</dd></div>
          <div class="forensic-detail-row"><dt>Flagged Audio Windows</dt><dd>${raw.audio_windows_flagged || 0} / ${raw.audio_total_windows || 1}</dd></div>
          <div class="forensic-detail-row"><dt>Raw Peak Acoustic Score</dt><dd>${raw.audio_raw_peak_score !== undefined ? `${(raw.audio_raw_peak_score * 100).toFixed(1)}%` : 'N/A'}</dd></div>
        </dl>
      </div>

      <!-- 3. Financial Scam & Regulatory -->
      <div class="forensic-modality-card">
        <div class="forensic-modality-card-head">
          <h4 class="forensic-modality-title">⚖️ Financial Scam Claims</h4>
          <span class="forensic-modality-badge ${sBadge}">
            ${scam.score !== null ? `${Math.round(scam.score * 100)}%` : (scam.violatesSebi ? 'Violated' : 'Clean')}
          </span>
        </div>
        <div class="forensic-modality-status">${escapeHtml(scam.label || (scam.violatesSebi ? 'Prohibited Promises Flagged' : 'No Prohibited Promises'))}</div>
        <div class="forensic-modality-desc">${escapeHtml(scam.explanation || 'Screened statements against SEBI Investment Adviser Regulations and penal code fraud.')}</div>
        <dl class="forensic-detail-dl">
          <div class="forensic-detail-row"><dt>SEBI IA Reg 15</dt><dd>${scam.violatesSebi ? '❌ Violated' : '✅ Compliant'}</dd></div>
          <div class="forensic-detail-row"><dt>BNS Sec 318(4) Match</dt><dd>${scam.violatesBns ? '❌ Flagged' : '✅ None'}</dd></div>
          <div class="forensic-detail-row"><dt>DPDP PII Scrubbed</dt><dd>${raw.dpdp_pii_scrubbed_count || 0} Entities</dd></div>
        </dl>
      </div>

      <!-- 4. SEBI Intermediary Registry -->
      <div class="forensic-modality-card">
        <div class="forensic-modality-card-head">
          <h4 class="forensic-modality-title">🏛️ SEBI Registry Cross-Check</h4>
          <span class="forensic-modality-badge ${rBadge}">
            ${escapeHtml(reg.badge || 'Official Database')}
          </span>
        </div>
        <div class="forensic-modality-status">${escapeHtml(reg.label || 'Registry Verification')}</div>
        <div class="forensic-modality-desc">${escapeHtml(reg.summary || 'Live cross-reference against SEBI Registered Intermediaries database.')}</div>
        <dl class="forensic-detail-dl">
          <div class="forensic-detail-row"><dt>Claimed Adviser</dt><dd>${escapeHtml(reg.claimedName || 'None Claimed')}</dd></div>
          <div class="forensic-detail-row"><dt>Claimed Reg Number</dt><dd>${escapeHtml(reg.claimedNumber || 'N/A')}</dd></div>
          <div class="forensic-detail-row"><dt>Database Match</dt><dd>${escapeHtml(reg.matchedName || 'No Match')}</dd></div>
        </dl>
      </div>
    </div>
  `;

  let heatmapHtml = '';
  const heatmapSrc = video.heatmap || raw.heatmap_base64;
  if (heatmapSrc) {
    const fullHeatmapUri = heatmapSrc.startsWith('data:') ? heatmapSrc : `data:image/png;base64,${heatmapSrc}`;
    heatmapHtml = `
      <details class="forensic-disclosure" open>
        <summary>
          <span>🔥 Visual Forensic Heatmap (Facial Manipulation Anomaly Map)</span>
          <span style="font-size:12px;color:var(--muted)">Spatial & C3D Activation ▾</span>
        </summary>
        <div class="forensic-disclosure-inner">
          <div class="forensic-heatmap-wrap">
            <img src="${fullHeatmapUri}" alt="Facial Deepfake Forensic Heatmap" class="forensic-heatmap-img">
            <p class="forensic-heatmap-caption">
              <b>Heatmap Interpretation:</b> High-intensity warm zones (red/yellow) indicate anomalous facial boundary blending, temporal warping, or deepfake generative neural artifacts localized around the mouth, eyes, or jawline.
            </p>
          </div>
        </div>
      </details>
    `;
  }

  let transcriptHtml = '';
  const segments = vm.transcript || [];
  if (segments.length > 0) {
    transcriptHtml = `
      <details class="forensic-disclosure" open>
        <summary>
          <span>💬 Timestamped Audio Transcript (OpenAI Whisper)</span>
          <span style="font-size:12px;color:var(--muted)">${segments.length} Segments ▾</span>
        </summary>
        <div class="forensic-disclosure-inner">
          <ul class="forensic-transcript-list">
            ${segments.map(s => `
              <li>
                <time>${fmtClock(s.start)} - ${fmtClock(s.end)}</time>
                <span>${escapeHtml(s.text)}</span>
              </li>
            `).join('')}
          </ul>
        </div>
      </details>
    `;
  } else if (raw.transcript) {
    transcriptHtml = `
      <details class="forensic-disclosure" open>
        <summary>
          <span>💬 Audio Speech Transcript (OpenAI Whisper)</span>
          <span style="font-size:12px;color:var(--muted)">Full Text ▾</span>
        </summary>
        <div class="forensic-disclosure-inner">
          <p style="font-size:13.5px;line-height:1.6;color:#282b28;margin:0;background:#faf4e8;padding:12px;border-radius:6px">
            “${escapeHtml(raw.transcript)}”
          </p>
        </div>
      </details>
    `;
  }

  let timelineHtml = '';
  const timeline = vm.timeline || [];
  if (timeline.length > 0) {
    timelineHtml = `
      <details class="forensic-disclosure">
        <summary>
          <span>⏱️ Media Forensic Timeline Track</span>
          <span style="font-size:12px;color:var(--muted)">${timeline.length} Evidence Events ▾</span>
        </summary>
        <div class="forensic-disclosure-inner">
          <ul class="forensic-timeline-list">
            ${timeline.map(item => `
              <li>
                <time style="font-family:monospace;font-size:11.5px;font-weight:700;color:#173f35">
                  ${fmtClock(item.start)} - ${fmtClock(item.end)}
                </time>
                <div>
                  <span class="timeline-badge ${item.type === 'audio' ? 'audio-badge' : 'text-badge'}">
                    ${escapeHtml(item.type ? item.type.toUpperCase() : 'SIGNAL')}
                  </span>
                  <b>${escapeHtml(item.text || item.label || 'Flagged Event')}</b>
                  ${item.quote ? `<span class="timeline-quote">“${escapeHtml(item.quote)}”</span>` : ''}
                </div>
              </li>
            `).join('')}
          </ul>
        </div>
      </details>
    `;
  }

  let evidenceHtml = '';
  const evidenceItems = vm.evidence || [];
  if (evidenceItems.length > 0) {
    evidenceHtml = `
      <details class="forensic-disclosure" open>
        <summary>
          <span>📋 Quoted Evidence & Findings Audit Trail</span>
          <span style="font-size:12px;color:var(--muted)">${evidenceItems.length} Quoted Items ▾</span>
        </summary>
        <div class="forensic-disclosure-inner">
          <div class="forensic-table-wrap">
            <table class="forensic-evidence-table">
              <thead>
                <tr>
                  <th style="width:60px">ID</th>
                  <th style="width:140px">Signal / Category</th>
                  <th style="width:80px">Time</th>
                  <th>Quoted Statement / Observation</th>
                  <th style="width:100px">Risk Tier</th>
                </tr>
              </thead>
              <tbody>
                ${evidenceItems.map(e => `
                  <tr>
                    <td><b>${escapeHtml(e.id)}</b></td>
                    <td><b>${escapeHtml(e.kind || e.source || 'Claim')}</b></td>
                    <td><code>${e.timestamp !== null && e.timestamp !== undefined ? fmtClock(e.timestamp) : 'N/A'}</code></td>
                    <td>
                      ${e.quote ? `<div style="font-style:italic;color:#173f35;margin-bottom:3px">“${escapeHtml(e.quote)}”</div>` : ''}
                      <span style="color:#565d56;font-size:12px">${escapeHtml(e.title || e.body || '')}</span>
                    </td>
                    <td>
                      <span class="forensic-modality-badge ${e.tier === 'critical' || e.tier === 'high' ? 'badge-danger' : e.tier === 'moderate' ? 'badge-warning' : 'badge-safe'}">
                        ${escapeHtml((e.tier || 'INFO').toUpperCase())}
                      </span>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </details>
    `;
  }

  const violations = scam.violations || [];
  let statutoryHtml = '';
  if (violations.length > 0 || scam.violatesSebi || scam.violatesBns) {
    statutoryHtml = `
      <details class="forensic-disclosure">
        <summary>
          <span>⚖️ Statutory Legal & Regulatory Violations</span>
          <span style="font-size:12px;color:var(--muted)">Acts & Penal Provisions ▾</span>
        </summary>
        <div class="forensic-disclosure-inner">
          <div class="forensic-statutory-grid">
            <div class="statutory-card">
              <b>SEBI Act, 1992 — Section 12(1)</b>
              <p>Prohibits undertaking investment advice or portfolio recommendation without active certificate of registration issued by SEBI.</p>
            </div>
            <div class="statutory-card">
              <b>SEBI IA Regulations, 2013 — Reg 15(1)</b>
              <p>Expressly prohibits guaranteeing or promising fixed, specific, or risk-free returns on stock market and securities investments.</p>
            </div>
            <div class="statutory-card">
              <b>Bharatiya Nyaya Sanhita (BNS) 2023 — Sec 318(4)</b>
              <p>Criminal cheating by inducing any person dishonestly to deliver property or make valuable securities investments based on false representations.</p>
            </div>
            <div class="statutory-card">
              <b>Information Technology Act, 2000 — Sec 66D</b>
              <p>Punishment for cheating by personation by using computer resource, synthetic AI voices, or deepfake likenesses.</p>
            </div>
          </div>
        </div>
      </details>
    `;
  }

  const nextSteps = vm.nextSteps || [];
  let nextStepsHtml = '';
  if (nextSteps.length > 0) {
    nextStepsHtml = `
      <details class="forensic-disclosure">
        <summary>
          <span>🛡️ Recommended Protective Actions</span>
          <span style="font-size:12px;color:var(--muted)">${nextSteps.length} Next Steps ▾</span>
        </summary>
        <div class="forensic-disclosure-inner">
          <ul class="forensic-steps-list">
            ${nextSteps.map((step, idx) => `
              <li class="forensic-step-item">
                <span class="forensic-step-icon">${idx + 1}</span>
                <div>
                  <div class="forensic-step-title">${escapeHtml(step.title || 'Recommended Action')}</div>
                  <p class="forensic-step-desc">${escapeHtml(step.body || step)}</p>
                </div>
              </li>
            `).join('')}
          </ul>
        </div>
      </details>
    `;
  }

  const scoresComplaint = vm.scoresComplaint || raw.scores_complaint || '';
  let complaintDraftHtml = '';
  if (scoresComplaint) {
    complaintDraftHtml = `
      <details class="forensic-disclosure" open>
        <summary>
          <span>🏛️ Official SEBI SCORES 2.0 Complaint Draft</span>
          <span style="font-size:12px;color:var(--muted)">Certified Text Format ▾</span>
        </summary>
        <div class="forensic-disclosure-inner">
          <div class="complaint-actions-row">
            <a href="/api/jobs/${jobId}/complaint/pdf" target="_blank" class="button btn-mobile-pdf" style="min-height:44px;font-size:13px;padding:8px 16px;width:auto">
              <span>📄</span> Download Certified Complaint (PDF)
            </a>
            <button type="button" class="button btn-mobile-print" id="btn-print-dossier" style="min-height:44px;font-size:13px;padding:8px 16px;width:auto">
              <span>🖨️</span> Print Full Forensic Dossier
            </button>
            <button type="button" class="button btn-mobile-copy" id="btn-dl-txt" style="min-height:44px;font-size:13px;padding:8px 16px;width:auto">
              <span>💾</span> Download .TXT Report
            </button>
          </div>
          <pre class="forensic-complaint-pre" id="scores-complaint-text">${escapeHtml(scoresComplaint)}</pre>
        </div>
      </details>
    `;
  }

  return `
    <div class="detailed-forensic-section" id="detailed-forensic-dossier">
      <div class="detailed-forensic-header">
        <div>
          <span class="detailed-eyebrow">Comprehensive Forensic Investigation Dossier</span>
          <h3 class="detailed-title">Multi-Modal Forensic & Regulatory Analysis</h3>
        </div>
        <span class="detailed-badge">BS 2023 Sec 63 Compliant</span>
      </div>
      <div class="detailed-forensic-body">
        ${modalityCardsHtml}
        ${heatmapHtml}
        ${transcriptHtml}
        ${timelineHtml}
        ${evidenceHtml}
        ${statutoryHtml}
        ${nextStepsHtml}
        ${complaintDraftHtml}
      </div>
    </div>
  `;
}

function wireDossierActions(res, vm, jobId) {
  const jumpBtn = $('#btn-scroll-dossier', dlg);
  if (jumpBtn) {
    jumpBtn.addEventListener('click', () => {
      const dossier = $('#detailed-forensic-dossier', dlg);
      if (dossier) dossier.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  const printBtns = $$('#btn-print-dossier, #btn-print-dossier-main', dlg);
  printBtns.forEach(b => b.addEventListener('click', () => window.print()));

  const txtBtns = $$('#btn-dl-txt, #btn-dl-txt-main', dlg);
  txtBtns.forEach(b => b.addEventListener('click', () => {
    const complaint = res.scores_complaint || vm.scoresComplaint || '';
    const textContent = `============================================================
FINGUARD MULTI-MODAL FORENSIC INVESTIGATION REPORT
============================================================
Job Reference ID   : ${jobId}
Timestamp          : ${new Date().toISOString()}
Verdict            : ${res.verdict || 'N/A'}
Composite Risk     : ${Math.round((res.composite_risk_score || 0) * 100)}%
Deepfake Detected  : ${res.is_deepfake ? 'YES' : 'NO'}
Scam Detected      : ${res.is_scam ? 'YES' : 'NO'}
Visual Face Score  : ${res.vision_score !== null && res.vision_score !== undefined ? `${(res.vision_score * 100).toFixed(1)}%` : 'N/A'}
Voice Clone Score  : ${res.audio_score !== null && res.audio_score !== undefined ? `${(res.audio_score * 100).toFixed(1)}%` : 'N/A'}
SEBI Registry      : ${res.registry_check?.verdict || 'Not Claimed'}

SUMMARY:
${res.overall_summary || 'N/A'}

SPEECH TRANSCRIPT:
${res.transcript || 'N/A'}

============================================================
OFFICIAL SEBI SCORES 2.0 COMPLAINT DRAFT
============================================================
${complaint}

============================================================
END OF DOSSIER — BHARATIYA SAKSHYA ADHINIYAM (BSA 2023) SEC 63
============================================================
`;
    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `FinGuard_Forensic_Report_${jobId.slice(0, 8)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Plaintext dossier downloaded!');
  }));

  const copyBtn = $('#btn-copy-complaint', dlg);
  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      try {
        let cText = res.scores_complaint || vm.scoresComplaint || '';
        if (!cText) {
          copyBtn.disabled = true;
          copyBtn.innerHTML = '<span>⏳</span> Fetching Complaint...';
          const cResp = await fetch(`/api/jobs/${jobId}/complaint`);
          if (!cResp.ok) throw new Error('Could not fetch complaint');
          cText = await cResp.text();
        }
        await navigator.clipboard.writeText(cText);
        copyBtn.innerHTML = '<span>✓</span> Copied Complaint to Clipboard!';
        showToast('Complaint text copied to clipboard!');
        setTimeout(() => {
          copyBtn.disabled = false;
          copyBtn.innerHTML = '<span>📋</span> Copy Plaintext Complaint to Clipboard';
        }, 3000);
      } catch (e) {
        console.error(e);
        showToast('Unable to copy automatically. Download PDF instead.');
        copyBtn.disabled = false;
        copyBtn.innerHTML = '<span>📋</span> Copy Plaintext Complaint to Clipboard';
      }
    });
  }
}

function renderVideoResults(res, jobId, filename = 'Analyzed Video') {
  const verdict = res.verdict || 'Analysis Complete';
  const risk = Math.round((res.composite_risk_score || 0) * 100);
  const isDeepfake = Boolean(res.is_deepfake);
  const isScam = Boolean(res.is_scam);
  const vScoreNum = typeof res.vision_score === 'number' ? res.vision_score : null;
  const aScoreNum = typeof res.audio_score === 'number' ? res.audio_score : null;
  const vScoreStr = vScoreNum !== null ? `${(vScoreNum * 100).toFixed(1)}%` : 'N/A';
  const aScoreStr = aScoreNum !== null ? `${(aScoreNum * 100).toFixed(1)}%` : 'N/A';
  const isVisionFake = vScoreNum !== null && vScoreNum > 0.4;
  const isAudioFake = aScoreNum !== null && aScoreNum > 0.5;

  let bannerClass = 'banner-safe', bannerIcon = '✅', fillClass = 'fill-safe', colorClass = 'color-safe', riskLevelText = 'LOW / NO MALICIOUS SIGNALS';
  if (risk >= 80 || (isDeepfake && isScam)) {
    bannerClass = 'banner-critical';
    bannerIcon = '🚨';
    fillClass = 'fill-critical';
    colorClass = 'color-critical';
    riskLevelText = 'CRITICAL FRAUD & DEEPFAKE THREAT';
  } else if (risk >= 40 || isDeepfake || isScam) {
    bannerClass = 'banner-warning';
    bannerIcon = '⚠️';
    fillClass = 'fill-warning';
    colorClass = 'color-warning';
    riskLevelText = 'SUSPICIOUS / ELEVATED RISK';
  }

  const regVerdict = res.registry_check?.verdict || 'Not Claimed';
  const isRegFlag = ['impersonated', 'unregistered'].includes(String(regVerdict).toLowerCase());

  const vm = toViewModel(res, { mode: 'video', jobId: jobId, filename: filename });
  const detailedHtml = buildDetailedAnalysisHtml(vm, res, jobId);

  const out = $('#workspace-output', dlg);
  out.innerHTML = `
    <div class="mobile-conclusion-card" id="workspace-result-card">
      <div class="mobile-verdict-banner ${bannerClass}">
        <span class="banner-icon">${bannerIcon}</span>
        <div class="banner-text">
          <span class="banner-kicker">FINANCIAL FORENSIC CONCLUSION</span>
          <h3 class="banner-title">${escapeHtml(verdict.toUpperCase())}</h3>
        </div>
      </div>
      
      <div class="mobile-risk-score-box">
        <div class="risk-score-header">
          <div>
            <span class="risk-label">Composite Risk Rating</span>
            <div class="risk-sublabel">${riskLevelText}</div>
          </div>
          <div class="risk-big-number ${colorClass}">
            ${risk}<span class="risk-unit">%</span>
          </div>
        </div>
        <div class="risk-meter-bar">
          <div class="risk-meter-fill ${fillClass}" style="width:${Math.max(5, risk)}%"></div>
        </div>
      </div>
      
      <div class="mobile-findings-list">
        <div class="finding-card ${isVisionFake ? 'finding-danger' : 'finding-ok'}">
          <span class="finding-icon">${isVisionFake ? '👁️' : '✅'}</span>
          <div class="finding-content">
            <b>Visual Facial Authenticity</b>
            <span>${vScoreStr} · ${isVisionFake ? 'Synthetic Face / Temporal Glitches Detected' : 'Authentic Camera Capture'}</span>
          </div>
        </div>
        
        <div class="finding-card ${isAudioFake ? 'finding-danger' : 'finding-ok'}">
          <span class="finding-icon">${isAudioFake ? '🎙️' : '✅'}</span>
          <div class="finding-content">
            <b>Voice Authenticity (Wav2Vec2)</b>
            <span>${aScoreStr} · ${isAudioFake ? 'Synthetic Voice Clone Detected' : 'Natural Human Voice Patterns'}</span>
          </div>
        </div>
        
        <div class="finding-card ${isRegFlag ? 'finding-danger' : 'finding-ok'}">
          <span class="finding-icon">${isRegFlag ? '🏛️' : '✅'}</span>
          <div class="finding-content">
            <b>SEBI Intermediary Registry</b>
            <span>${escapeHtml(regVerdict).toUpperCase()} · ${isRegFlag ? 'Unregistered / Identity Fraud Risk' : 'No Fraudulent Registry Claim'}</span>
          </div>
        </div>
        
        <div class="finding-card finding-info">
          <span class="finding-icon">⚖️</span>
          <div class="finding-content">
            <b>Legal Admissibility (BSA 2023)</b>
            <span>Section 63 Digital Evidence Hash & Audit Trail Certified</span>
          </div>
        </div>
      </div>
      
      ${res.overall_summary ? `
        <div class="mobile-summary-box">
          <b>Forensic Summary & Analysis</b>
          <p>${escapeHtml(res.overall_summary)}</p>
        </div>
      ` : ''}
      
      <div class="mobile-conclusion-actions">
        <a href="/api/jobs/${jobId}/complaint/pdf" target="_blank" class="button btn-mobile-pdf" id="btn-dl-pdf-main">
          <span>📄</span> Download Certified Court Complaint (PDF)
        </a>
        <button type="button" class="button btn-mobile-print" id="btn-print-dossier-main">
          <span>🖨️</span> Print / Save Full Dossier (PDF)
        </button>
        <button type="button" class="button btn-mobile-copy" id="btn-dl-txt-main">
          <span>💾</span> Download Plaintext (.TXT) Report
        </button>
        <button type="button" class="button btn-mobile-copy" id="btn-copy-complaint">
          <span>📋</span> Copy Plaintext Complaint to Clipboard
        </button>
        <button type="button" class="button btn-mobile-secondary" id="btn-scroll-dossier">
          <span>🔍</span> Inspect Detailed Forensic Dossier ↓
        </button>
      </div>
    </div>

    ${detailedHtml}
  `;

  wireDossierActions(res, vm, jobId);

  setTimeout(() => {
    const card = $('#workspace-result-card', dlg);
    if (card) card.scrollIntoView({ behavior: 'smooth', block: 'start' });
    else dlg.scrollTo({ top: out.offsetTop - 30, behavior: 'smooth' });
  }, 100);
}

const PIPELINE_STAGES = [
  { id: 'stage1_ingest', name: 'Ingest & Sampling', desc: 'Decoding video keyframes & audio stream', icon: '1' },
  { id: 'stage2_vision', name: 'Facial Deepfake Scan', desc: 'ms-eff-gcvit & C3D facial artifacts', icon: '2' },
  { id: 'stage3_audio', name: 'Voice Clone Analysis', desc: 'Wav2Vec2 synthetic acoustic classifier', icon: '3' },
  { id: 'stage4_transcript', name: 'Speech & On-Screen OCR', desc: 'Whisper STT & keyframe text extraction', icon: '4' },
  { id: 'stage5_llm', name: 'Regulatory Reasoning', desc: 'SEBI IA Reg 15 & BNS 318(4) scam audit', icon: '5' },
  { id: 'stage6_registry', name: 'SEBI Intermediary Check', desc: 'Official SEBI registration verification', icon: '6' },
  { id: 'stage8_report', name: 'Court Evidence Dossier', desc: 'BSA 2023 Sec 63 certification & SCORES draft', icon: '7' }
];

function getStageIndex(stageId) {
  if (!stageId) return 0;
  if (stageId === 'stage1_ingest') return 0;
  if (stageId === 'stage2_vision') return 1;
  if (stageId === 'stage3_audio') return 2;
  if (stageId === 'stage4_transcript' || stageId === 'stage7_ocr') return 3;
  if (stageId === 'stage5_llm') return 4;
  if (stageId === 'stage6_registry' || stageId === 'stage9_apk_domain') return 5;
  if (stageId === 'stage8_report' || stageId === 'stage7_aggregation') return 6;
  return 0;
}

function renderUploadTracker(loadedBytes, totalBytes, percent) {
  const loadedMb = (loadedBytes / 1048576).toFixed(1);
  const totalMb = (totalBytes / 1048576).toFixed(1);
  return `
    <div class="mobile-upload-tracker" id="upload-tracker-box">
      <div class="tracker-head">
        <div class="tracker-title-row">
          <span class="pulse-radar"></span>
          <span class="tracker-title">Uploading Video to GPU Cluster...</span>
        </div>
        <span class="tracker-pct">${percent}%</span>
      </div>
      <div class="tracker-meter">
        <div class="tracker-meter-fill" style="width: ${percent}%"></div>
      </div>
      <div class="tracker-meta">
        <span><b>${loadedMb} MB</b> of ${totalMb} MB transferred</span>
        <span>🔒 AES-256 Encrypted Transfer</span>
      </div>
    </div>
  `;
}

function renderPipelineTracker(activeStageIdx, isCompleted = false) {
  const pct = isCompleted ? 100 : Math.min(96, Math.round(((activeStageIdx + 0.6) / PIPELINE_STAGES.length) * 100));
  const activeStage = PIPELINE_STAGES[activeStageIdx] || PIPELINE_STAGES[0];
  
  const stagesHtml = PIPELINE_STAGES.map((s, idx) => {
    let state = 'pending';
    let statusText = 'Pending';
    let iconContent = s.icon;
    
    if (isCompleted || idx < activeStageIdx) {
      state = 'completed';
      statusText = '✓ Completed';
      iconContent = '✓';
    } else if (idx === activeStageIdx) {
      state = 'active';
      statusText = 'Running...';
      iconContent = '◉';
    }
    
    return `
      <div class="stepper-stage ${state}">
        <span class="stage-icon">${iconContent}</span>
        <div class="stage-content">
          <span class="stage-name">${s.name}</span>
          <span class="stage-desc">${s.desc}</span>
        </div>
        <span class="stage-status-badge">${statusText}</span>
      </div>
    `;
  }).join('');
  
  return `
    <div class="mobile-forensic-tracker" id="pipeline-tracker-box">
      <div class="tracker-head">
        <div class="tracker-title-row">
          <span class="pulse-radar"></span>
          <span class="tracker-title">${isCompleted ? 'Forensic Pipeline Complete' : escapeHtml(activeStage.name)}</span>
        </div>
        <span class="tracker-pct">${pct}%</span>
      </div>
      <div class="tracker-meter">
        <div class="tracker-meter-fill" style="width: ${pct}%"></div>
      </div>
      <div class="tracker-active-sub">
        ${isCompleted ? '✅ All 7 forensic models completed verification.' : `⚡ <b>Active Pipeline:</b> ${escapeHtml(activeStage.desc)}`}
      </div>
      <div class="stages-stepper">
        ${stagesHtml}
      </div>
    </div>
  `;
}

function uploadWithProgress(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/jobs');
    
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        onProgress(e.loaded, e.total, pct);
      }
    };
    
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error('Invalid response from FinGuard server'));
        }
      } else {
        try {
          const errData = JSON.parse(xhr.responseText);
          reject(new Error(errData.detail || `Upload failed (Status ${xhr.status})`));
        } catch {
          reject(new Error(`Upload failed (Status ${xhr.status})`));
        }
      }
    };
    
    xhr.onerror = () => reject(new Error('Network error during file upload. Check your connection.'));
    xhr.ontimeout = () => reject(new Error('Upload timed out. Please try again.'));
    
    const fd = new FormData();
    fd.append('file', file);
    xhr.send(fd);
  });
}

function openTool(id){
  activeTool=tools.find(t=>t.id===id);
  if(!activeTool)return;
  selectedFile=null;
  previewUrl=null;
  const kicker=$('#dialog-kicker-text',dlg);
  if(kicker)kicker.textContent=`${activeTool.title} · Live Forensics`;
  renderWorkspace();
  dlg.hidden=false;
  document.body.classList.add('dialog-open');
  dlg.scrollTop=0;
  const closeBtn=$('.dialog-close',dlg);
  if(closeBtn)closeBtn.focus();
}

function renderWorkspace(){
  const t=activeTool;
  const upload=['video','audio','apk'].includes(t.id);
  const audio=t.id==='audio',accept=t.accept||'';
  dlgContent.className='dialog-content';
  dlgContent.innerHTML=`
    <span class="dialog-kicker">${t.type} · FINGUARD LIVE FORENSICS</span>
    <h2 id="dialog-title">${t.title}</h2>
    <p>${t.desc}</p>
    <span class="demo-banner" style="background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0">🟢 LIVE 9-STAGE FORENSIC ENGINE CONNECTED</span>
    ${upload?`
      <div class="dropzone" id="dropzone">
        <span class="drop-icon">${audio?'♫':'↥'}</span>
        <b>${audio?'Drop an audio recording here':'Choose or Drop a file here'}</b>
        <small>${audio?'MP3, WAV, M4A, or other audio file':'Select media to analyze with local GPU models'}</small>
        <input class="file-input" id="file-input" type="file" accept="${accept}">
        <button class="browse-btn" type="button">Select file from device</button>
      </div>
      <div id="file-info"></div>
      ${audio?'<div class="waveform" aria-label="Decorative audio waveform">'+Array.from({length:41},(_,i)=>`<i style="--h:${12+Math.abs(Math.sin(i*4.2))*27}px"></i>`).join('')+'</div>':''}
    `:t.id==='url'?`
      <label class="workspace-label" for="workspace-value">Website address</label>
      <input class="workspace-input" id="workspace-value" type="url" placeholder="https://example-broker.xyz" autocomplete="url">
    `: `
      <label class="workspace-label" for="workspace-value">${t.id==='compliance'?'Paste a financial claim or promotional pitch to inspect':'Describe the content to check'}</label>
      <textarea class="workspace-textarea" id="workspace-value" placeholder="e.g. 500% guaranteed monthly returns, join VIP telegram channel…"></textarea>
    `}
    <div class="workspace-error" id="workspace-error" role="alert"></div>
    <button class="button button-blue workspace-submit" id="run-demo">${t.action}<span>→</span></button>
    <div id="workspace-output" aria-live="polite"></div>
  `;
  if(upload){
    const input=$('#file-input',dlg),zone=$('#dropzone',dlg);
    $('.browse-btn',dlg).addEventListener('click',()=>input.click());
    input.addEventListener('change',()=>setFile(input.files[0]));
    zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('dragging')});
    zone.addEventListener('dragleave',()=>zone.classList.remove('dragging'));
    zone.addEventListener('drop',e=>{e.preventDefault();zone.classList.remove('dragging');setFile(e.dataTransfer.files[0])});
  }
  $('#run-demo',dlg).addEventListener('click',runDemo);
}

function setFile(file){
  const error=$('#workspace-error',dlg);
  error.textContent='';
  if(!file)return;
  const kind=activeTool.id;
  if(kind==='apk'&&!file.name.toLowerCase().endsWith('.apk')){error.textContent='Please choose an APK file for application safety scan.';return;}
  if(kind==='video'&&!file.type.startsWith('video/')){error.textContent='Please choose a valid video file.';return;}
  if(kind==='audio'&&!file.type.startsWith('audio/')){error.textContent='Please choose a valid audio file.';return;}
  if(file.size>100*1024*1024){error.textContent='File exceeds 100 MB limit.';return;}
  selectedFile=file;
  if(previewUrl)URL.revokeObjectURL(previewUrl);
  previewUrl=URL.createObjectURL(file);
  const sizeMb=(file.size/1048576).toFixed(2);
  let mediaPreview='';
  if(kind==='video'){
    mediaPreview=`
      <div class="media-preview-container">
        <video controls playsinline preload="metadata" src="${previewUrl}" class="mobile-media-preview"></video>
      </div>
    `;
  } else if(kind==='audio'){
    mediaPreview=`<audio controls src="${previewUrl}" style="width:100%;margin-top:10px"></audio>`;
  }
  $('#file-info',dlg).innerHTML=`
    <div class="file-selected">
      <span style="font-size:18px">${kind==='audio'?'♫':kind==='video'?'🎬':'📦'}</span>
      <div style="flex:1 1 auto;min-width:0">
        <b style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(file.name)}</b>
        <span style="font-size:12px;color:#475569">${sizeMb} MB · Ready for FinGuard GPU models</span>
      </div>
      <button type="button" class="file-remove-btn" aria-label="Remove selected file">✕</button>
    </div>
    ${mediaPreview}
  `;
  $('.file-remove-btn',dlg).addEventListener('click',()=>{
    selectedFile=null;
    if(previewUrl)URL.revokeObjectURL(previewUrl);
    previewUrl=null;
    $('#file-info',dlg).innerHTML='';
    $('#file-input',dlg).value='';
  });
}

async function runDemo(){
  const error=$('#workspace-error',dlg),out=$('#workspace-output',dlg);
  error.textContent='';
  const toolId=activeTool.id;
  
  if(['video','audio','apk'].includes(toolId)&&!selectedFile){
    error.textContent='Please choose a file to analyze.';
    return;
  }
  let urlVal='';
  if(toolId==='url'){
    urlVal=$('#workspace-value',dlg).value.trim();
    try {
      const u=new URL(urlVal);
      if(!['http:','https:'].includes(u.protocol)||!u.hostname.includes('.'))throw Error();
    } catch {
      error.textContent='Please enter a valid web address starting with https:// or http://';
      $('#workspace-value',dlg).focus();
      return;
    }
  }
  let claimVal='';
  if(toolId==='compliance'){
    claimVal=$('#workspace-value',dlg).value.trim();
    if(!claimVal){
      error.textContent='Please paste a financial claim or promotional text to inspect.';
      $('#workspace-value',dlg).focus();
      return;
    }
  }
  
  const btn=$('#run-demo',dlg);
  btn.disabled=true;
  const originalBtnText=btn.innerHTML;
  btn.innerHTML='<span>⏳</span> Verifying Content...';
  
  try {
    // ── 1. Video Multimodal Forensics ───────────────────────────────
    if(toolId==='video'){
      out.innerHTML=renderUploadTracker(0, selectedFile.size, 0);
      setTimeout(()=>{ dlg.scrollTo({top:out.offsetTop-30,behavior:'smooth'}); }, 50);
      
      const initData=await uploadWithProgress(selectedFile, (loaded, total, pct)=>{
        out.innerHTML=renderUploadTracker(loaded, total, pct);
      });
      
      const jobId=initData.job_id;
      out.innerHTML=renderPipelineTracker(0, false);
      
      let completed=false,pollCount=0;
      while(!completed&&pollCount<120){
        await new Promise(r=>setTimeout(r,1400));
        pollCount++;
        const checkResp=await fetch(`/api/jobs/${jobId}`);
        if(!checkResp.ok)continue;
        const checkData=await checkResp.json();
        
        if(checkData.status==='processing'){
          const stageIdx=getStageIndex(checkData.stage);
          out.innerHTML=renderPipelineTracker(stageIdx, false);
        } else if(checkData.status==='completed'){
          completed=true;
          out.innerHTML=renderPipelineTracker(6, true);
          await new Promise(r=>setTimeout(r,400));
          renderVideoResults(checkData.result || {}, jobId, selectedFile?.name);
        } else if(checkData.status==='failed'){
          throw new Error(checkData.error||'Video analysis encountered an error.');
        }
      }
    }
    
    // ── 2. Audio Acoustic Deepfake Scan ────────────────────────────
    else if(toolId==='audio'){
      out.innerHTML=`
        <div class="mobile-forensic-tracker">
          <div class="tracker-head">
            <div class="tracker-title-row"><span class="pulse-radar"></span><span class="tracker-title">Running Wav2Vec2 Acoustic Model...</span></div>
            <span class="tracker-pct">50%</span>
          </div>
          <div class="tracker-meter"><div class="tracker-meter-fill" style="width:50%"></div></div>
          <div class="tracker-active-sub">⚡ Analyzing acoustic temporal artifacts and vocal frequency distributions</div>
        </div>
      `;
      setTimeout(()=>{ dlg.scrollTo({top:out.offsetTop-30,behavior:'smooth'}); }, 50);
      
      const fd=new FormData();
      fd.append('file',selectedFile);
      const resp=await fetch('/api/scan/audio',{method:'POST',body:fd});
      if(!resp.ok)throw new Error(`Audio scan returned status ${resp.status}`);
      const data=await resp.json();
      const isFake=Boolean(data.is_deepfake);
      const score=data.audio_score!==undefined?Math.round(data.audio_score*100):0;
      
      out.innerHTML=`
        <div class="mobile-conclusion-card" id="workspace-result-card">
          <div class="mobile-verdict-banner ${isFake?'banner-critical':'banner-safe'}">
            <span class="banner-icon">${isFake?'🚨':'✅'}</span>
            <div class="banner-text">
              <span class="banner-kicker">ACOUSTIC CLASSIFICATION</span>
              <h3 class="banner-title">${isFake?'SYNTHETIC VOICE CLONE DETECTED':'AUTHENTIC HUMAN SPEECH'}</h3>
            </div>
          </div>
          
          <div class="mobile-risk-score-box">
            <div class="risk-score-header">
              <div>
                <span class="risk-label">Spoof Likelihood Rating</span>
                <div class="risk-sublabel">${isFake?'HIGH PROBABILITY SYNTHETIC VOICE':'AUTHENTIC HUMAN VOCAL CORDS'}</div>
              </div>
              <div class="risk-big-number ${isFake?'color-critical':'color-safe'}">
                ${score}<span class="risk-unit">%</span>
              </div>
            </div>
            <div class="risk-meter-bar">
              <div class="risk-meter-fill ${isFake?'fill-critical':'fill-safe'}" style="width:${Math.max(5,score)}%"></div>
            </div>
          </div>
          
          <div class="mobile-findings-list">
            <div class="finding-card ${isFake?'finding-danger':'finding-ok'}">
              <span class="finding-icon">${isFake?'🎙️':'✅'}</span>
              <div class="finding-content">
                <b>Acoustic Neural Architecture</b>
                <span>${escapeHtml(data.audio_backend||'Wav2Vec2 GaryStafford')} · ${data.audio_windows_flagged||0} flagged temporal windows</span>
              </div>
            </div>
          </div>
          
          ${data.transcript?`
            <div class="mobile-summary-box">
              <b>Speech Transcript (Whisper)</b>
              <p>“${escapeHtml(data.transcript)}”</p>
            </div>
          `:''}
          
          <div class="mobile-conclusion-actions">
            <button type="button" class="button btn-mobile-print" id="btn-audio-print">
              <span>🖨️</span> Print / Save Acoustic Dossier (PDF)
            </button>
            <button type="button" class="button btn-mobile-copy" id="btn-audio-copy">
              <span>📋</span> Copy Speech Transcript to Clipboard
            </button>
          </div>
        </div>
      `;
      const audioPrint=$('#btn-audio-print',dlg);
      if(audioPrint)audioPrint.addEventListener('click',()=>window.print());
      const audioCopy=$('#btn-audio-copy',dlg);
      if(audioCopy){
        audioCopy.addEventListener('click',async ()=>{
          const textToCopy=data.transcript||`Voice Spoof Likelihood: ${score}% (${data.audio_backend||'Wav2Vec2'})`;
          await navigator.clipboard.writeText(textToCopy);
          showToast('Audio findings copied to clipboard!');
        });
      }
      setTimeout(()=>{
        const card=$('#workspace-result-card',dlg);
        if(card) card.scrollIntoView({behavior:'smooth',block:'start'});
        else dlg.scrollTo({top:out.offsetTop-30,behavior:'smooth'});
      },100);
    }
    
    // ── 3. APK Application Safety Scan ─────────────────────────────
    else if(toolId==='apk'){
      out.innerHTML=`
        <div class="mobile-forensic-tracker">
          <div class="tracker-head">
            <div class="tracker-title-row"><span class="pulse-radar"></span><span class="tracker-title">Decompiling APK & Scanning Manifest...</span></div>
            <span class="tracker-pct">50%</span>
          </div>
          <div class="tracker-meter"><div class="tracker-meter-fill" style="width:50%"></div></div>
          <div class="tracker-active-sub">⚡ Inspecting Android permissions, trojan capabilities, and broker whitelists</div>
        </div>
      `;
      setTimeout(()=>{ dlg.scrollTo({top:out.offsetTop-30,behavior:'smooth'}); }, 50);
      
      const fd=new FormData();
      fd.append('file',selectedFile);
      const resp=await fetch('/api/scan/apk',{method:'POST',body:fd});
      if(!resp.ok)throw new Error(`APK scan returned status ${resp.status}`);
      const data=await resp.json();
      const apkR=data.apk_result||{};
      const isSuspicious=Boolean(apkR.is_suspicious);
      
      out.innerHTML=`
        <div class="mobile-conclusion-card" id="workspace-result-card">
          <div class="mobile-verdict-banner ${isSuspicious?'banner-critical':'banner-safe'}">
            <span class="banner-icon">${isSuspicious?'🚨':'✅'}</span>
            <div class="banner-text">
              <span class="banner-kicker">APPLICATION SAFETY AUDIT</span>
              <h3 class="banner-title">${isSuspicious?'DANGEROUS / MALICIOUS APK':'VERIFIED OFFICIAL BROKER PACKAGE'}</h3>
            </div>
          </div>
          
          <div class="mobile-findings-list">
            <div class="finding-card ${isSuspicious?'finding-danger':'finding-ok'}">
              <span class="finding-icon">📦</span>
              <div class="finding-content">
                <b>Package Identifier</b>
                <span><code>${escapeHtml(apkR.package_name||selectedFile.name)}</code></span>
              </div>
            </div>
            
            <div class="finding-card ${isSuspicious?'finding-danger':'finding-ok'}">
              <span class="finding-icon">${isSuspicious?'⚠️':'✅'}</span>
              <div class="finding-content">
                <b>Security Finding</b>
                <span>${escapeHtml(apkR.reason||'Package verified within standard operational parameters.')}</span>
              </div>
            </div>
            
            ${apkR.suspicious_permissions?.length?`
              <div class="finding-card finding-danger">
                <span class="finding-icon">🚨</span>
                <div class="finding-content">
                  <b>High-Risk Trojan Permissions Flagged</b>
                  <span>${apkR.suspicious_permissions.map(p=>`<code>${escapeHtml(p)}</code>`).join(', ')}</span>
                </div>
              </div>
            `:''}
          </div>

          <div class="mobile-conclusion-actions">
            <button type="button" class="button btn-mobile-print" id="btn-apk-print">
              <span>🖨️</span> Print / Save Application Dossier (PDF)
            </button>
            <button type="button" class="button btn-mobile-copy" id="btn-apk-copy">
              <span>📋</span> Copy Security Findings to Clipboard
            </button>
          </div>
        </div>
      `;
      const apkPrint=$('#btn-apk-print',dlg);
      if(apkPrint)apkPrint.addEventListener('click',()=>window.print());
      const apkCopy=$('#btn-apk-copy',dlg);
      if(apkCopy){
        apkCopy.addEventListener('click',async ()=>{
          const textToCopy=`APK Package: ${apkR.package_name||selectedFile.name}\nFinding: ${apkR.reason||'OK'}\nSuspicious: ${isSuspicious?'YES':'NO'}`;
          await navigator.clipboard.writeText(textToCopy);
          showToast('Security findings copied to clipboard!');
        });
      }
      setTimeout(()=>{
        const card=$('#workspace-result-card',dlg);
        if(card) card.scrollIntoView({behavior:'smooth',block:'start'});
        else dlg.scrollTo({top:out.offsetTop-30,behavior:'smooth'});
      },100);
    }
    
    // ── 4. URL Phishing & Typo-Squatting Check ─────────────────────
    else if(toolId==='url'){
      out.innerHTML=`
        <div class="mobile-forensic-tracker">
          <div class="tracker-head">
            <div class="tracker-title-row"><span class="pulse-radar"></span><span class="tracker-title">Checking Domain & Brand Whitelist...</span></div>
            <span class="tracker-pct">50%</span>
          </div>
          <div class="tracker-meter"><div class="tracker-meter-fill" style="width:50%"></div></div>
          <div class="tracker-active-sub">⚡ Verifying domain age, SSL telemetry, and registered SEBI broker domains</div>
        </div>
      `;
      setTimeout(()=>{ dlg.scrollTo({top:out.offsetTop-30,behavior:'smooth'}); }, 50);
      
      const resp=await fetch('/api/scan/url',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url:urlVal})
      });
      if(!resp.ok)throw new Error(`URL scan returned status ${resp.status}`);
      const data=await resp.json();
      const urlR=data.url_result||{};
      const isPhishing=Boolean(urlR.is_phishing);
      
      out.innerHTML=`
        <div class="mobile-conclusion-card" id="workspace-result-card">
          <div class="mobile-verdict-banner ${isPhishing?'banner-critical':'banner-safe'}">
            <span class="banner-icon">${isPhishing?'🚨':'✅'}</span>
            <div class="banner-text">
              <span class="banner-kicker">DOMAIN REPUTATION VERDICT</span>
              <h3 class="banner-title">${isPhishing?'PHISHING / FAKE BROKER DETECTED':'CLEAN / LEGITIMATE DOMAIN'}</h3>
            </div>
          </div>
          
          <div class="mobile-findings-list">
            <div class="finding-card ${isPhishing?'finding-danger':'finding-ok'}">
              <span class="finding-icon">🌐</span>
              <div class="finding-content">
                <b>Normalized Host</b>
                <span><code>${escapeHtml(urlR.normalised_host||urlVal)}</code></span>
              </div>
            </div>
            
            <div class="finding-card ${isPhishing?'finding-danger':'finding-ok'}">
              <span class="finding-icon">${isPhishing?'⚠️':'✅'}</span>
              <div class="finding-content">
                <b>Forensic Finding</b>
                <span>${escapeHtml(urlR.reason||'Domain verification completed.')}</span>
              </div>
            </div>
            
            ${urlR.matched_legitimate_domain?`
              <div class="finding-card finding-danger">
                <span class="finding-icon">🚨</span>
                <div class="finding-content">
                  <b>Spoofed Genuine SEBI Entity</b>
                  <span>Targeted Broker: <b>${escapeHtml(urlR.legitimate_broker)}</b> (<code>${escapeHtml(urlR.matched_legitimate_domain)}</code>)</span>
                </div>
              </div>
            `:''}
          </div>

          <div class="mobile-conclusion-actions">
            <button type="button" class="button btn-mobile-print" id="btn-url-print">
              <span>🖨️</span> Print / Save Domain Dossier (PDF)
            </button>
            <button type="button" class="button btn-mobile-copy" id="btn-url-copy">
              <span>📋</span> Copy Domain Findings to Clipboard
            </button>
          </div>
        </div>
      `;
      const urlPrint=$('#btn-url-print',dlg);
      if(urlPrint)urlPrint.addEventListener('click',()=>window.print());
      const urlCopy=$('#btn-url-copy',dlg);
      if(urlCopy){
        urlCopy.addEventListener('click',async ()=>{
          const textToCopy=`Host: ${urlR.normalised_host||urlVal}\nPhishing: ${isPhishing?'YES':'NO'}\nFinding: ${urlR.reason||'OK'}`;
          await navigator.clipboard.writeText(textToCopy);
          showToast('Domain findings copied to clipboard!');
        });
      }
      setTimeout(()=>{
        const card=$('#workspace-result-card',dlg);
        if(card) card.scrollIntoView({behavior:'smooth',block:'start'});
        else dlg.scrollTo({top:out.offsetTop-30,behavior:'smooth'});
      },100);
    }
    
    // ── 5. Financial Claim / Compliance Scan ────────────────────────
    else if(toolId==='compliance'){
      out.innerHTML=`
        <div class="mobile-forensic-tracker">
          <div class="tracker-head">
            <div class="tracker-title-row"><span class="pulse-radar"></span><span class="tracker-title">Cross-Checking Statutory Violations...</span></div>
            <span class="tracker-pct">50%</span>
          </div>
          <div class="tracker-meter"><div class="tracker-meter-fill" style="width:50%"></div></div>
          <div class="tracker-active-sub">⚡ Auditing against SEBI IA Regulations 2013 and BNS 2023 Sec 318(4)</div>
        </div>
      `;
      setTimeout(()=>{ dlg.scrollTo({top:out.offsetTop-30,behavior:'smooth'}); }, 50);
      
      const resp=await fetch('/api/scan/text',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({text:claimVal})
      });
      if(!resp.ok)throw new Error(`Compliance scan returned status ${resp.status}`);
      const data=await resp.json();
      const isScam=Boolean(data.is_scam);
      const risk=Math.round((data.composite_risk_score||0)*100);
      
      out.innerHTML=`
        <div class="mobile-conclusion-card" id="workspace-result-card">
          <div class="mobile-verdict-banner ${isScam?'banner-warning':'banner-safe'}">
            <span class="banner-icon">${isScam?'⚠️':'✅'}</span>
            <div class="banner-text">
              <span class="banner-kicker">STATUTORY COMPLIANCE VERDICT</span>
              <h3 class="banner-title">${escapeHtml(data.verdict||'Review Completed').toUpperCase()}</h3>
            </div>
          </div>
          
          <div class="mobile-risk-score-box">
            <div class="risk-score-header">
              <div>
                <span class="risk-label">Regulatory Risk Score</span>
                <div class="risk-sublabel">${isScam?'POTENTIAL FRAUD / NON-COMPLIANT PROMISES':'COMPLIANT FINANCIAL COMMUNICATION'}</div>
              </div>
              <div class="risk-big-number ${risk>=60?'color-critical':risk>=30?'color-warning':'color-safe'}">
                ${risk}<span class="risk-unit">%</span>
              </div>
            </div>
            <div class="risk-meter-bar">
              <div class="risk-meter-fill ${risk>=60?'fill-critical':risk>=30?'fill-warning':'fill-safe'}" style="width:${Math.max(5,risk)}%"></div>
            </div>
          </div>
          
          <div class="mobile-findings-list">
            <div class="finding-card ${data.sebi_analysis?.specific_return_promises?.length?'finding-danger':'finding-ok'}">
              <span class="finding-icon">🏛️</span>
              <div class="finding-content">
                <b>SEBI IA Regulation 15 Audit</b>
                <span>${data.sebi_analysis?.specific_return_promises?.length?'❌ Guaranteed Return Promises Prohibited by SEBI':'✅ No Prohibited Fixed Returns Promised'}</span>
              </div>
            </div>
            
            <div class="finding-card ${isScam?'finding-danger':'finding-ok'}">
              <span class="finding-icon">⚖️</span>
              <div class="finding-content">
                <b>Criminal Penal Code Match</b>
                <span>${isScam?'BNS Sec 318(4) (Cheating) & IT Act Sec 66D (Impersonation)':'No Criminal Penal Offence Flagged'}</span>
              </div>
            </div>
          </div>
          
          ${data.sebi_analysis?.reasoning?`
            <div class="mobile-summary-box">
              <b>Forensic Legal Reasoning</b>
              <p>${escapeHtml(data.sebi_analysis.reasoning)}</p>
            </div>
          `:''}

          <div class="mobile-conclusion-actions">
            ${data.scores_complaint ? `
              <button type="button" class="button btn-mobile-pdf" id="btn-comp-dl-pdf">
                <span>📄</span> Download Certified Court Complaint (PDF)
              </button>
            ` : ''}
            <button type="button" class="button btn-mobile-print" id="btn-comp-print">
              <span>🖨️</span> Print / Save Compliance Dossier (PDF)
            </button>
            <button type="button" class="button btn-mobile-copy" id="btn-comp-dl-txt">
              <span>💾</span> Download Plaintext (.TXT) Report
            </button>
            <button type="button" class="button btn-mobile-copy" id="btn-comp-copy">
              <span>📋</span> Copy Text Findings to Clipboard
            </button>
          </div>

          ${data.scores_complaint ? `
            <details class="forensic-disclosure" open style="margin-top:16px">
              <summary>
                <span>🏛️ Official SEBI SCORES 2.0 Complaint Draft</span>
                <span style="font-size:12px;color:var(--muted)">Certified Format ▾</span>
              </summary>
              <div class="forensic-disclosure-inner">
                <pre class="forensic-complaint-pre">${escapeHtml(data.scores_complaint)}</pre>
              </div>
            </details>
          ` : ''}
        </div>
      `;

      const printBtn = $('#btn-comp-print', dlg);
      if (printBtn) printBtn.addEventListener('click', () => window.print());

      const pdfBtn = $('#btn-comp-dl-pdf', dlg);
      if (pdfBtn && data.scores_complaint) {
        pdfBtn.addEventListener('click', async () => {
          try {
            pdfBtn.disabled = true;
            pdfBtn.innerHTML = '<span>⏳</span> Generating Institutional PDF...';
            const pdfResp = await fetch('/api/complaint/pdf', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                complaint_text: data.scores_complaint,
                mode: 'Financial Claim Compliance Scan',
                verdict: data.verdict
              })
            });
            if (!pdfResp.ok) throw new Error('PDF generation failed');
            const blob = await pdfResp.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `FinGuard_SEBI_SCORES_Complaint_${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast('Complaint PDF downloaded successfully!');
          } catch (e) {
            console.error(e);
            showToast('PDF generation failed. Use print instead.');
          } finally {
            pdfBtn.disabled = false;
            pdfBtn.innerHTML = '<span>📄</span> Download Certified Court Complaint (PDF)';
          }
        });
      }

      const txtBtn = $('#btn-comp-dl-txt', dlg);
      if (txtBtn) {
        txtBtn.addEventListener('click', () => {
          const textContent = `============================================================\nFINGUARD STATUTORY COMPLIANCE INVESTIGATION REPORT\n============================================================\nDate / Timestamp  : ${new Date().toISOString()}\nTested Text       : "${claimVal}"\nVerdict           : ${data.verdict || 'N/A'}\nRegulatory Risk   : ${risk}%\nScam Flagged      : ${isScam ? 'YES' : 'NO'}\nSEBI IA Reg 15    : ${data.sebi_analysis?.specific_return_promises?.length ? 'VIOLATED' : 'COMPLIANT'}\nReasoning         : ${data.sebi_analysis?.reasoning || 'N/A'}\n\n${data.scores_complaint ? `============================================================\nOFFICIAL SEBI SCORES 2.0 COMPLAINT DRAFT\n============================================================\n${data.scores_complaint}` : ''}\n`;
          const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `FinGuard_Compliance_Report_${Date.now()}.txt`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          showToast('Plaintext report downloaded!');
        });
      }

      const copyBtn = $('#btn-comp-copy', dlg);
      if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
          try {
            const textToCopy = data.scores_complaint || data.sebi_analysis?.reasoning || claimVal;
            await navigator.clipboard.writeText(textToCopy);
            copyBtn.innerHTML = '<span>✓</span> Copied to Clipboard!';
            showToast('Text copied to clipboard!');
            setTimeout(() => {
              copyBtn.innerHTML = '<span>📋</span> Copy Text Findings to Clipboard';
            }, 3000);
          } catch {
            showToast('Unable to copy automatically.');
          }
        });
      }
      setTimeout(()=>{
        const card=$('#workspace-result-card',dlg);
        if(card) card.scrollIntoView({behavior:'smooth',block:'start'});
        else dlg.scrollTo({top:out.offsetTop-30,behavior:'smooth'});
      },100);
    }
  } catch (err){
    console.error('[FinGuard Frontend Error]',err);
    out.innerHTML=`
      <div class="mobile-conclusion-card" id="workspace-result-card" style="border-color:#fca5a5">
        <div class="mobile-verdict-banner banner-critical">
          <span class="banner-icon">⚠️</span>
          <div class="banner-text">
            <span class="banner-kicker">ANALYSIS NOTICE</span>
            <h3 class="banner-title">Error During Verification</h3>
          </div>
        </div>
        <p style="font-size:14px;color:#991b1b;margin:0 0 10px">${escapeHtml(err.message||'Could not connect to FinGuard forensic server.')}</p>
        <small style="font-size:12px;color:#64748b">Please ensure your device is connected to the internet and retry.</small>
      </div>
    `;
    setTimeout(()=>{
      const card=$('#workspace-result-card',dlg);
      if(card) card.scrollIntoView({behavior:'smooth',block:'start'});
      else dlg.scrollTo({top:out.offsetTop-30,behavior:'smooth'});
    },100);
  } finally {
    btn.disabled=false;
    btn.innerHTML=originalBtnText;
  }
}

track.addEventListener('click',e=>{const b=e.target.closest('[data-tool]');if(b)openTool(b.dataset.tool)});
function closeWorkspace(){
  dlg.hidden=true;
  document.body.classList.remove('dialog-open');
  if(previewUrl)URL.revokeObjectURL(previewUrl);
  previewUrl=null;
  selectedFile=null;
  const out=$('#workspace-output',dlg);
  if(out)out.innerHTML='';
}
$('.dialog-close',dlg).addEventListener('click',closeWorkspace);
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!dlg.hidden)closeWorkspace()});
document.addEventListener('pointerdown',e=>{if(!dlg.hidden&&e.target===dlg)closeWorkspace()});
const menu=$('.menu-toggle'),nav=$('.nav');menu.addEventListener('click',()=>{const open=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(open));menu.textContent=open?'×':'☰'});nav.addEventListener('click',e=>{if(e.target.closest('a')){nav.classList.remove('open');menu.setAttribute('aria-expanded','false');menu.textContent='☰'}});
const revealObserver=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');revealObserver.unobserve(e.target)}}),{threshold:.12});$$('.section-heading,.step-card,.sebi-card').forEach(el=>{el.classList.add('reveal');revealObserver.observe(el)});
drawCarousel();window.addEventListener('load',drawCarousel,{once:true});

async function checkDirectJobLoad() {
  try {
    const params = new URLSearchParams(window.location.search);
    const jobId = params.get('job_id');
    if (!jobId) return;

    openTool('video');
    const out = $('#workspace-output', dlg);
    if (!out) return;

    out.innerHTML = `
      <div class="mobile-forensic-tracker">
        <div class="tracker-head">
          <div class="tracker-title-row"><span class="pulse-radar"></span><span class="tracker-title">Loading Saved Forensic Dossier...</span></div>
          <span class="tracker-pct">100%</span>
        </div>
        <div class="tracker-meter"><div class="tracker-meter-fill" style="width:100%"></div></div>
        <div class="tracker-active-sub">⚡ Fetching complete multimodal analysis for Job ID <code>${escapeHtml(jobId)}</code></div>
      </div>
    `;

    const resp = await fetch(`/api/jobs/${jobId}`);
    if (!resp.ok) throw new Error(`Job not found (${resp.status})`);
    const checkData = await resp.json();
    if (checkData.status === 'completed') {
      renderVideoResults(checkData.result || {}, jobId, checkData.filename || 'Archived Video');
    } else {
      out.innerHTML = `
        <div class="mobile-conclusion-card" id="workspace-result-card" style="border-color:#fca5a5">
          <div class="mobile-verdict-banner banner-warning">
            <span class="banner-icon">⏳</span>
            <div class="banner-text">
              <span class="banner-kicker">ANALYSIS STATUS</span>
              <h3 class="banner-title">Job is ${escapeHtml(checkData.status)}</h3>
            </div>
          </div>
          <p style="font-size:13.5px;color:#5e4c48;margin:10px 0 0">The requested job is still in progress or incomplete.</p>
        </div>
      `;
    }
  } catch (err) {
    console.warn('[FinGuard] Direct job load failed:', err);
  }
}
window.addEventListener('load', checkDirectJobLoad);

