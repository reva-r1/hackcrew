document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const chatViewport = document.getElementById('chatViewport');
  const chatForm = document.getElementById('chatForm');
  const queryInput = document.getElementById('queryInput');
  const submitBtn = document.getElementById('submitBtn');

  // Modal Elements
  const uploadModal = document.getElementById('uploadModal');
  const openUploadBtn = document.getElementById('openUploadBtn');
  const attachClipBtn = document.getElementById('attachClipBtn');
  const closeUploadModalBtn = document.getElementById('closeUploadModalBtn');
  const modalDismissBtn = document.getElementById('modalDismissBtn');
  const modalViewAuditBtn = document.getElementById('modalViewAuditBtn');

  // Dropzone Elements
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const dropPrompt = document.getElementById('dropPrompt');
  const uploadPreviewBox = document.getElementById('uploadPreviewBox');
  const previewFileName = document.getElementById('previewFileName');
  const previewBadge = document.getElementById('previewBadge');
  const previewMediaContainer = document.getElementById('previewMediaContainer');
  const previewTextExcerpt = document.getElementById('previewTextExcerpt');
  const uploadStatus = document.getElementById('uploadStatus');

  // Drawer Elements
  const auditLogDrawer = document.getElementById('auditLogDrawer');
  const openAuditBtn = document.getElementById('openAuditBtn');
  const closeAuditDrawerBtn = document.getElementById('closeAuditDrawerBtn');
  const tabChunksBtn = document.getElementById('tabChunksBtn');
  const tabLogsBtn = document.getElementById('tabLogsBtn');
  const tabFilesBtn = document.getElementById('tabFilesBtn');
  const tabContentChunks = document.getElementById('tabContentChunks');
  const tabContentLogs = document.getElementById('tabContentLogs');
  const tabContentFiles = document.getElementById('tabContentFiles');
  const refreshChunksBtn = document.getElementById('refreshChunksBtn');
  const refreshLogsBtn = document.getElementById('refreshLogsBtn');
  const chunksListContainer = document.getElementById('chunksListContainer');
  const logsListContainer = document.getElementById('logsListContainer');
  const filesListContainer = document.getElementById('filesListContainer');

  // Telemetry Elements
  const navChunkCount = document.getElementById('navChunkCount');
  const telemetryDocCount = document.getElementById('telemetryDocCount');
  const telemetryChunkCount = document.getElementById('telemetryChunkCount');
  const telemetryWordCount = document.getElementById('telemetryWordCount');
  const purgeDataBtn = document.getElementById('purgeDataBtn');
  const drawerPurgeBtn = document.getElementById('drawerPurgeBtn');

  // Citation Popover Tooltip
  const citationPopover = document.getElementById('citationPopover');
  const popoverDocName = document.getElementById('popoverDocName');
  const popoverScore = document.getElementById('popoverScore');
  const popoverSnippet = document.getElementById('popoverSnippet');

  // Initial Load
  fetchChunksAndTelemetry();

  // =========================================================================
  // Modal Handlers (Pop-up Dropbox)
  // =========================================================================
  function openModal() {
    uploadModal.style.display = 'flex';
  }

  function closeModal() {
    uploadModal.style.display = 'none';
  }

  if (openUploadBtn) openUploadBtn.addEventListener('click', openModal);
  if (attachClipBtn) attachClipBtn.addEventListener('click', openModal);
  if (closeUploadModalBtn) closeUploadModalBtn.addEventListener('click', closeModal);
  if (modalDismissBtn) modalDismissBtn.addEventListener('click', closeModal);

  if (modalViewAuditBtn) {
    modalViewAuditBtn.addEventListener('click', () => {
      closeModal();
      openDrawer();
    });
  }

  uploadModal.addEventListener('click', (e) => {
    if (e.target === uploadModal) closeModal();
  });

  // =========================================================================
  // Drawer Handlers (Audit Log & Chunks Inspector)
  // =========================================================================
  function openDrawer() {
    auditLogDrawer.style.display = 'flex';
    fetchChunksAndTelemetry();
  }

  function closeDrawer() {
    auditLogDrawer.style.display = 'none';
  }

  if (openAuditBtn) openAuditBtn.addEventListener('click', openDrawer);
  if (closeAuditDrawerBtn) closeAuditDrawerBtn.addEventListener('click', closeDrawer);

  // Tab Switching inside Drawer
  function switchTab(activeBtn, activeContent) {
    [tabChunksBtn, tabLogsBtn, tabFilesBtn].forEach(b => b.classList.remove('active'));
    [tabContentChunks, tabContentLogs, tabContentFiles].forEach(c => c.style.display = 'none');
    activeBtn.classList.add('active');
    activeContent.style.display = 'flex';
  }

  if (tabChunksBtn) tabChunksBtn.addEventListener('click', () => switchTab(tabChunksBtn, tabContentChunks));
  if (tabLogsBtn) tabLogsBtn.addEventListener('click', () => {
    switchTab(tabLogsBtn, tabContentLogs);
    fetchSystemLogs();
  });
  if (tabFilesBtn) tabFilesBtn.addEventListener('click', () => {
    switchTab(tabFilesBtn, tabContentFiles);
    fetchUploadedFiles();
  });

  if (refreshChunksBtn) refreshChunksBtn.addEventListener('click', fetchChunksAndTelemetry);
  if (refreshLogsBtn) refreshLogsBtn.addEventListener('click', fetchSystemLogs);

  // Purge / Reset Handlers
  if (purgeDataBtn) purgeDataBtn.addEventListener('click', handlePurgeData);
  if (drawerPurgeBtn) drawerPurgeBtn.addEventListener('click', handlePurgeData);

  async function handlePurgeData() {
    if (!confirm('Purge all indexed documents, vectors, and chunks from the knowledge base?')) return;
    try {
      const res = await fetch('/clear-all', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        alert(`Purge complete. ${data.files_removed} files and all vector coordinates removed.`);
        resetDropZone();
        fetchChunksAndTelemetry();
      }
    } catch (e) {
      console.error('Failed to purge repository:', e);
    }
  }

  // =========================================================================
  // Telemetry & Chunk Inspector Fetchers
  // =========================================================================
  async function fetchChunksAndTelemetry() {
    try {
      const res = await fetch('/chunks');
      const data = await res.json();
      
      const chunkCount = data.total_chunks || 0;
      const wordCount = data.total_words || 0;

      if (navChunkCount) navChunkCount.textContent = chunkCount;
      if (telemetryChunkCount) telemetryChunkCount.textContent = chunkCount;
      if (telemetryWordCount) telemetryWordCount.textContent = wordCount.toLocaleString();

      renderChunksList(data.chunks || []);
      fetchUploadedFiles();
    } catch (e) {
      console.error('Error fetching chunks telemetry:', e);
    }
  }

  function renderChunksList(chunks) {
    if (!chunksListContainer) return;
    if (chunks.length === 0) {
      chunksListContainer.innerHTML = `
        <div class="empty-state-notice">
          No document chunks indexed.<br>Upload an enterprise document via the dropbox to inspect extracted words and coordinates.
        </div>
      `;
      return;
    }

    chunksListContainer.innerHTML = '';
    chunks.forEach((c) => {
      const card = document.createElement('div');
      card.className = 'chunk-card';
      const pageInfo = c.page_num ? ` • Page ${c.page_num}` : '';
      card.innerHTML = `
        <div class="chunk-header-row">
          <span class="chunk-doc-title">📄 ${escapeHtml(c.doc_name)}${pageInfo}</span>
          <span class="chunk-stats-badge">${c.word_count} words • ${c.char_count} chars</span>
        </div>
        <div class="chunk-raw-snippet">${escapeHtml(c.preview)}</div>
      `;
      chunksListContainer.appendChild(card);
    });
  }

  async function fetchUploadedFiles() {
    try {
      const res = await fetch('/uploaded-files');
      const data = await res.json();
      const files = data.files || [];

      if (telemetryDocCount) telemetryDocCount.textContent = files.length;
      if (!filesListContainer) return;

      if (files.length === 0) {
        filesListContainer.innerHTML = '<div class="empty-state-notice">No files ingested yet.</div>';
        return;
      }

      filesListContainer.innerHTML = '';
      files.forEach((f) => {
        const item = document.createElement('div');
        item.className = 'chunk-card';
        item.innerHTML = `
          <div class="chunk-header-row">
            <span class="chunk-doc-title">${escapeHtml(f.name)}</span>
            <span class="chunk-stats-badge">${f.size_kb} KB</span>
          </div>
          <div style="font-size: 0.7rem; color: var(--text-muted); font-family: var(--font-mono);">
            Indexed into vector store & ready for cross-encoder retrieval.
          </div>
        `;
        filesListContainer.appendChild(item);
      });
    } catch (e) {
      console.error('Error fetching uploaded files:', e);
    }
  }

  async function fetchSystemLogs() {
    if (!logsListContainer) return;
    try {
      const res = await fetch('/logs');
      const data = await res.json();
      const logs = data.logs || [];

      if (logs.length === 0) {
        logsListContainer.innerHTML = '<div class="empty-state-notice">No system events logged yet.</div>';
        return;
      }

      logsListContainer.innerHTML = '';
      logs.forEach((l) => {
        const item = document.createElement('div');
        item.className = 'log-event-item';
        item.innerHTML = `
          <div class="log-event-meta">
            <span class="log-event-cat">[${escapeHtml(l.category)}]</span>
            <span>${escapeHtml(l.timestamp)}</span>
          </div>
          <div class="log-event-title">${escapeHtml(l.title)}</div>
          <div class="log-event-detail">${escapeHtml(l.detail)}</div>
        `;
        logsListContainer.appendChild(item);
      });
    } catch (e) {
      console.error('Error fetching system logs:', e);
    }
  }

  // =========================================================================
  // Drag & Drop File Upload Flow
  // =========================================================================
  dropZone.addEventListener('click', () => fileInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      uploadFile(fileInput.files[0]);
    }
  });

  function resetDropZone() {
    dropPrompt.style.display = 'flex';
    uploadPreviewBox.style.display = 'none';
    fileInput.value = '';
    uploadStatus.innerHTML = '';
  }

  async function uploadFile(file) {
    const validExts = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp', '.gif', '.docx', '.txt', '.md', '.json', '.csv', '.tsv'];
    const name = file.name.toLowerCase();
    const isSupported = validExts.some(ext => name.endsWith(ext));

    if (!isSupported) {
      uploadStatus.innerHTML = '<span style="color: #EF4444;">Unsupported file format. Please upload PDF, PNG, JPG, CSV, DOCX, or TXT.</span>';
      return;
    }

    const isImg = file.type.startsWith('image/');
    let immediateUrl = '';
    if (isImg) immediateUrl = URL.createObjectURL(file);

    dropPrompt.style.display = 'none';
    uploadPreviewBox.style.display = 'flex';
    previewFileName.textContent = file.name;
    previewBadge.textContent = 'Parsing & OCR';
    previewTextExcerpt.textContent = 'Extracting machine-readable text and chunking...';

    if (isImg && immediateUrl) {
      previewMediaContainer.innerHTML = `<img src="${immediateUrl}" alt="${escapeHtml(file.name)}" />`;
    } else {
      previewMediaContainer.innerHTML = `<div style="font-size: 2rem; padding: 10px;">📄</div>`;
    }

    uploadStatus.innerHTML = '<span style="color: var(--text-pure);">⏳ Processing layout OCR & vector indexing...</span>';
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.status === 'success') {
        const confPct = Math.round((data.confidence || 0.95) * 100);
        uploadStatus.innerHTML = `<span style="color: var(--text-pure);">✓ Ingested: ${data.chunks_created} chunks added (${data.provenance || 'OCR'}).</span>`;
        previewBadge.textContent = `${confPct}% Conf`;
        previewTextExcerpt.textContent = data.preview_text ? `"${data.preview_text}"` : 'Machine-readable text indexed successfully.';
        fetchChunksAndTelemetry();
      } else {
        uploadStatus.innerHTML = `<span style="color: #EF4444;">Upload error: ${escapeHtml(data.error || 'Failed')}</span>`;
        previewBadge.textContent = 'Failed';
      }
    } catch (err) {
      uploadStatus.innerHTML = `<span style="color: #EF4444;">Network fault: ${escapeHtml(err.message)}</span>`;
    }
  }

  // =========================================================================
  // Live Typing Match Preview (POST /preview-confidence) with ~400ms debounce
  // =========================================================================
  const livePreviewMeter = document.getElementById('livePreviewMeter');
  const previewScoreBadge = document.getElementById('previewScoreBadge');
  const previewStatusBadge = document.getElementById('previewStatusBadge');
  const previewMeterBarFill = document.getElementById('previewMeterBarFill');
  let previewDebounceTimer = null;

  if (queryInput && livePreviewMeter) {
    queryInput.addEventListener('input', () => {
      const text = queryInput.value.trim();
      clearTimeout(previewDebounceTimer);

      if (text.length < 2) {
        livePreviewMeter.style.display = 'none';
        return;
      }

      previewDebounceTimer = setTimeout(async () => {
        try {
          const res = await fetch('/preview-confidence', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ partial_query: text })
          });
          if (!res.ok) return;
          const data = await res.json();
          updateLivePreviewMeter(data);
        } catch (e) {
          console.debug('Preview confidence fetch error:', e);
        }
      }, 400);
    });

    queryInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        livePreviewMeter.style.display = 'none';
      }
    });
  }

  function updateLivePreviewMeter(data) {
    if (!livePreviewMeter || !queryInput || queryInput.value.trim().length < 2) return;
    const score = Math.round(data.score || 0);
    const status = data.status || 'no_match';

    if (previewScoreBadge) previewScoreBadge.textContent = `${score}%`;
    if (previewMeterBarFill) previewMeterBarFill.style.width = `${Math.min(100, score)}%`;

    if (previewStatusBadge) {
      previewStatusBadge.className = `preview-status-badge status-${status}`;
      if (status === 'strong_match') {
        previewStatusBadge.textContent = 'Strong Match';
      } else if (status === 'weak_match') {
        previewStatusBadge.textContent = 'Weak Match';
      } else {
        previewStatusBadge.textContent = 'No Match';
      }
    }

    livePreviewMeter.style.display = 'flex';
  }

  // =========================================================================
  // Conversational Query Flow (Locked API Contract)
  // =========================================================================
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    if (livePreviewMeter) livePreviewMeter.style.display = 'none';
    const query = queryInput.value.trim();
    if (!query) return;
    sendQuery(query);
  });

  async function sendQuery(query) {
    if (livePreviewMeter) livePreviewMeter.style.display = 'none';
    appendMessage('user', query);
    queryInput.value = '';
    queryInput.disabled = true;
    submitBtn.disabled = true;

    const loaderRow = appendTypingIndicator();
    chatViewport.scrollTop = chatViewport.scrollHeight;

    try {
      const res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, role: 'employee' })
      });

      const data = await res.json();
      if (loaderRow._loadingInterval) clearInterval(loaderRow._loadingInterval);
      loaderRow.remove();

      if (data.status === 'answered') {
        renderAnsweredMessage(data);
      } else if (data.status === 'refused') {
        renderRefusalMessage(data);
      } else {
        renderErrorMessage(data);
      }

      fetchChunksAndTelemetry();
    } catch (err) {
      if (loaderRow._loadingInterval) clearInterval(loaderRow._loadingInterval);
      loaderRow.remove();
      renderErrorMessage({ reason: err.message });
    } finally {
      queryInput.disabled = false;
      submitBtn.disabled = false;
      queryInput.focus();
      chatViewport.scrollTop = chatViewport.scrollHeight;
    }
  }

  function appendMessage(role, text) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    row.innerHTML = `
      <div class="avatar-glyph">${role === 'user' ? 'YOU' : '✦'}</div>
      <div class="bubble">${escapeHtml(text)}</div>
    `;
    chatViewport.appendChild(row);
    chatViewport.scrollTop = chatViewport.scrollHeight;
    return row;
  }

  function appendTypingIndicator() {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.innerHTML = `
      <div class="avatar-glyph">✦</div>
      <div class="bubble glass-panel">
        <div class="glass-scanner-loading">
          <div class="scanner-doc-box">
            <div class="scanner-line"></div>
            <div class="scanner-line"></div>
            <div class="scanner-line"></div>
            <div class="scanner-laser"></div>
          </div>
          <div class="scanner-text-block">
            <span class="scanner-kicker">ARCHIVAL SEARCH IN FLIGHT</span>
            <span class="scanner-msg" id="scanMsg">Scanning vector coordinates...</span>
          </div>
        </div>
      </div>
    `;
    chatViewport.appendChild(row);

    const statuses = [
      'Scanning dense vector coordinates...',
      'Executing BM25 exact keyword match...',
      'Fusing candidates via Reciprocal Rank (RRF)...',
      'Cross-encoder reranking & 0.40 gate evaluation...'
    ];
    let statusIdx = 0;
    const msgEl = row.querySelector('#scanMsg');
    const intervalId = setInterval(() => {
      statusIdx = (statusIdx + 1) % statuses.length;
      if (msgEl) {
        msgEl.style.opacity = '0';
        setTimeout(() => {
          msgEl.textContent = statuses[statusIdx];
          msgEl.style.opacity = '1';
        }, 150);
      }
    }, 1400);

    row._loadingInterval = intervalId;
    return row;
  }

  function renderAnsweredMessage(data) {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    
    const confidencePct = Math.round((data.confidence || 0) * 100);

    // Build Unique Floating Glass Pill Citations
    let citationsHtml = '';
    if (data.sources && data.sources.length > 0) {
      citationsHtml = `
        <div class="citations-cluster" style="display: none;">
          <span class="citations-label">VERIFIED CITATIONS:</span>
          ${data.sources.map((s, idx) => `
            <div class="glass-citation-pill" 
                 data-doc="${escapeHtml(s.doc_name)}" 
                 data-page="${s.page_num || ''}"
                 data-snippet="${escapeHtml(s.snippet)}" 
                 data-score="${confidencePct}% Match">
              <span>📄 ${escapeHtml(s.doc_name)}</span>
              ${s.page_num ? `<span class="citation-page-tag">p.${s.page_num}</span>` : ''}
              <span>• ${confidencePct}%</span>
            </div>
          `).join('')}
        </div>
      `;
    }

    row.innerHTML = `
      <div class="avatar-glyph">✦</div>
      <div class="bubble glass-panel">
        <div class="answer-header-bar">
          <span class="kicker-grounded">GROUNDED SYNTHESIS</span>
          <div class="monotone-conf-capsule">
            <div class="conf-dot-silver"></div>
            <span>${confidencePct}% Match</span>
          </div>
        </div>
        <div class="answer-body-content" id="answerBodyTarget"></div>
        ${citationsHtml}
      </div>
    `;
    chatViewport.appendChild(row);
    chatViewport.scrollTop = chatViewport.scrollHeight;

    // Simulated fast typewriter word-by-word streaming reveal (~16ms/word)
    const target = row.querySelector('#answerBodyTarget');
    const citationsCluster = row.querySelector('.citations-cluster');
    const fullText = data.answer || '';
    const words = fullText.split(' ');
    let wordIdx = 0;
    let accumulated = '';

    function revealNextWord() {
      if (wordIdx < words.length) {
        accumulated += (wordIdx > 0 ? ' ' : '') + words[wordIdx];
        target.innerHTML = formatAnswer(accumulated) + '<span class="typewriter-cursor"></span>';
        wordIdx++;
        chatViewport.scrollTop = chatViewport.scrollHeight;
        setTimeout(revealNextWord, 16);
      } else {
        target.innerHTML = formatAnswer(fullText);
        if (citationsCluster) {
          citationsCluster.style.display = 'flex';
          chatViewport.scrollTop = chatViewport.scrollHeight;
          bindCitationPopovers(row);
        }
      }
    }

    revealNextWord();
  }

  function renderRefusalMessage(data) {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    const confPct = Math.round((data.confidence || 0) * 100);
    row.innerHTML = `
      <div class="avatar-glyph">✦</div>
      <div class="bubble glass-refusal-card">
        <div class="refusal-top-bar">
          <div class="refusal-badge-group">
            <span class="refusal-shield-icon">🛡️</span>
            <span>Deterministic Safeguard Active</span>
          </div>
          <span class="refusal-score-pill">${confPct}% Match</span>
        </div>
        <p class="refusal-description-text">
          ${escapeHtml(data.reason && data.reason !== 'insufficient_evidence' ? data.reason : 'Cross-encoder retrieval score fell below the strict confidence threshold (0.40). Refusal triggered deliberately to prevent hallucination — this inquiry is outside the verified coverage of your ingested enterprise documentation.')}
        </p>
      </div>
    `;
    chatViewport.appendChild(row);
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  function renderErrorMessage(data) {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.innerHTML = `
      <div class="avatar-glyph">✦</div>
      <div class="bubble glass-error-card">
        <div class="error-title-text">Generation Fault</div>
        <div class="error-detail-text">${escapeHtml(data.reason || 'Server error')}</div>
      </div>
    `;
    chatViewport.appendChild(row);
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  // Interactive Citation Popovers
  function bindCitationPopovers(parentRow) {
    parentRow.querySelectorAll('.glass-citation-pill').forEach(pill => {
      pill.addEventListener('mouseenter', (e) => {
        const rect = pill.getBoundingClientRect();
        popoverDocName.textContent = pill.getAttribute('data-doc') + (pill.getAttribute('data-page') ? ` (Page ${pill.getAttribute('data-page')})` : '');
        popoverScore.textContent = pill.getAttribute('data-score');
        popoverSnippet.textContent = `"${pill.getAttribute('data-snippet')}"`;

        citationPopover.style.display = 'block';
        citationPopover.style.top = `${rect.bottom + window.scrollY + 6}px`;
        citationPopover.style.left = `${Math.min(rect.left, window.innerWidth - 400)}px`;
      });

      pill.addEventListener('mouseleave', () => {
        citationPopover.style.display = 'none';
      });
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function formatAnswer(text) {
    if (!text) return '';
    let formatted = escapeHtml(text).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    return formatted.replace(/\n/g, '<br>');
  }
});
