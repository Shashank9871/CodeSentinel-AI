/**
 * CodeSentinel AI - Frontend Application Controller
 */

// Application State
const state = {
  activeMode: 'github', // 'github' | 'code'
  activeTab: 'code-tab',
  samples: [],
  currentReview: null,
  activeCode: '',
  activeFileName: 'auth_service.py',
  filterSeverity: 'all',
  settings: {
    provider: localStorage.getItem('cs_provider') || 'heuristic',
    apiKey: localStorage.getItem('cs_api_key') || '',
    model: localStorage.getItem('cs_model') || 'gemini-1.5-flash',
    strictness: localStorage.getItem('cs_strictness') || 'standard',
    githubToken: localStorage.getItem('cs_gh_token') || ''
  }
};

// Initialization
document.addEventListener('DOMContentLoaded', async () => {
  initSettingsUI();
  await loadSamplesIndex();
  // Auto-load first demo scenario for rich immediate preview
  loadSample('sample-auth-vuln');
});

// Settings Management
function initSettingsUI() {
  document.getElementById('settingProvider').value = state.settings.provider;
  document.getElementById('settingApiKey').value = state.settings.apiKey;
  document.getElementById('settingStrictness').value = state.settings.strictness;
  document.getElementById('settingGithubToken').value = state.settings.githubToken;
  updateProviderSettings();

  document.getElementById('openSettingsBtn').addEventListener('click', () => toggleSettingsModal(true));
}

function updateProviderSettings() {
  const provider = document.getElementById('settingProvider').value;
  const apiKeyGroup = document.getElementById('apiKeyGroup');
  const modelGroup = document.getElementById('modelGroup');
  const modelSelect = document.getElementById('settingModel');
  const apiKeyLabel = document.getElementById('apiKeyLabel');
  const activeEngineLabel = document.getElementById('activeEngineLabel');

  if (provider === 'heuristic') {
    apiKeyGroup.classList.add('hidden');
    modelGroup.classList.add('hidden');
    activeEngineLabel.textContent = 'Engine: Heuristic + AST';
  } else if (provider === 'gemini') {
    apiKeyGroup.classList.remove('hidden');
    modelGroup.classList.remove('hidden');
    apiKeyLabel.textContent = 'Google Gemini API Key';
    modelSelect.innerHTML = `
      <option value="gemini-1.5-flash">gemini-1.5-flash (Fast & Accurate)</option>
      <option value="gemini-2.0-flash">gemini-2.0-flash (Next-Gen)</option>
      <option value="gemini-1.5-pro">gemini-1.5-pro (Deep Reasoning)</option>
    `;
    activeEngineLabel.textContent = 'Engine: Google Gemini';
  } else if (provider === 'openai') {
    apiKeyGroup.classList.remove('hidden');
    modelGroup.classList.remove('hidden');
    apiKeyLabel.textContent = 'OpenAI API Key';
    modelSelect.innerHTML = `
      <option value="gpt-4o-mini">gpt-4o-mini (Fast & Cost-effective)</option>
      <option value="gpt-4o">gpt-4o (Frontier Model)</option>
    `;
    activeEngineLabel.textContent = 'Engine: OpenAI GPT-4o';
  }
}

function toggleSettingsModal(show) {
  const modal = document.getElementById('settingsModal');
  if (show) {
    modal.classList.remove('hidden');
  } else {
    modal.classList.add('hidden');
  }
  lucide.createIcons();
}

function saveSettings() {
  state.settings.provider = document.getElementById('settingProvider').value;
  state.settings.apiKey = document.getElementById('settingApiKey').value.trim();
  state.settings.strictness = document.getElementById('settingStrictness').value;
  state.settings.githubToken = document.getElementById('settingGithubToken').value.trim();
  
  const modelElem = document.getElementById('settingModel');
  if (modelElem) {
    state.settings.model = modelElem.value;
    localStorage.setItem('cs_model', state.settings.model);
  }

  localStorage.setItem('cs_provider', state.settings.provider);
  localStorage.setItem('cs_api_key', state.settings.apiKey);
  localStorage.setItem('cs_strictness', state.settings.strictness);
  localStorage.setItem('cs_gh_token', state.settings.githubToken);

  updateProviderSettings();
  toggleSettingsModal(false);
  showToast('Settings saved successfully!');
}

// Mode Switching
function switchMode(mode) {
  state.activeMode = mode;
  const githubSection = document.getElementById('githubInputSection');
  const codeSection = document.getElementById('codeInputSection');
  const modeGithubBtn = document.getElementById('modeGithubBtn');
  const modeCodeBtn = document.getElementById('modeCodeBtn');

  if (mode === 'github') {
    githubSection.classList.remove('hidden');
    codeSection.classList.add('hidden');
    modeGithubBtn.className = 'flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition bg-slate-800 text-cyan-400 border border-slate-700';
    modeCodeBtn.className = 'flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm text-slate-400 hover:text-slate-200 transition hover:bg-slate-800/50';
  } else {
    codeSection.classList.remove('hidden');
    githubSection.classList.add('hidden');
    modeCodeBtn.className = 'flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition bg-slate-800 text-cyan-400 border border-slate-700';
    modeGithubBtn.className = 'flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm text-slate-400 hover:text-slate-200 transition hover:bg-slate-800/50';
  }
  lucide.createIcons();
}

// Load Samples Index from Backend
async function loadSamplesIndex() {
  try {
    const res = await fetch('/api/samples');
    if (res.ok) {
      state.samples = await res.json();
    }
  } catch (err) {
    console.error('Failed to load sample presets', err);
  }
}

// 1-Click Load Preset
async function loadSample(sampleId) {
  let sample = state.samples.find(s => s.id === sampleId);
  if (!sample) {
    await loadSamplesIndex();
    sample = state.samples.find(s => s.id === sampleId);
  }
  if (!sample) return;

  // Populate Code Editor
  switchMode('code');
  document.getElementById('fileNameInput').value = sample.title.split(':')[0] + '.py';
  document.getElementById('languageSelect').value = sample.language || 'python';
  document.getElementById('rawCodeTextarea').value = sample.code;

  state.activeCode = sample.code;
  state.activeFileName = sample.title;

  showToast(`Loaded: ${sample.title}`);
  // Immediately trigger review for instant showcase!
  executeDirectReview();
}

function clearCodeInput() {
  document.getElementById('rawCodeTextarea').value = '';
}

// Execute Direct Review
async function executeDirectReview() {
  const code = document.getElementById('rawCodeTextarea').value;
  if (!code.trim()) {
    showToast('Please enter or paste code to review.', 'warning');
    return;
  }

  const fileName = document.getElementById('fileNameInput').value.trim() || 'code.py';
  const language = document.getElementById('languageSelect').value;

  state.activeCode = code;
  state.activeFileName = fileName;

  showLoading(true, 'Analyzing code patterns, security vulnerabilities, and code quality...');

  try {
    const payload = {
      code: code,
      file_path: fileName,
      language: language,
      strictness: state.settings.strictness,
      provider: state.settings.provider,
      api_key: state.settings.apiKey || undefined,
      model: state.settings.model || undefined
    };

    const res = await fetch('/api/review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Review failed.');
    }

    state.currentReview = data;
    renderReviewDashboard(data);
    showToast('Review completed successfully!');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

// Execute GitHub PR Review
async function executeGithubReview() {
  const prUrl = document.getElementById('githubPrUrl').value.trim();
  if (!prUrl) {
    showToast('Please enter a GitHub Pull Request URL.', 'warning');
    return;
  }

  showLoading(true, 'Fetching PR diff from GitHub & running AI review...');

  try {
    const payload = {
      pr_url: prUrl,
      github_token: state.settings.githubToken || undefined,
      provider: state.settings.provider,
      api_key: state.settings.apiKey || undefined,
      model: state.settings.model || undefined,
      strictness: state.settings.strictness
    };

    const res = await fetch('/api/review/github', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to review GitHub PR.');
    }

    const prInfo = data.pr_info;
    const review = data.review;

    state.activeCode = prInfo.diff || (prInfo.files && prInfo.files[0] ? prInfo.files[0].patch : '# No diff');
    state.activeFileName = `${prInfo.title} (${prInfo.branch})`;

    state.currentReview = review;
    renderReviewDashboard(review);
    showToast(`Reviewed PR: ${prInfo.title}`);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

// Render Review Results
function renderReviewDashboard(review) {
  document.getElementById('resultsSection').classList.remove('hidden');

  // Verdict
  const verdictBadge = document.getElementById('verdictBadge');
  const verdictText = document.getElementById('verdictText');
  const verdictIcon = document.getElementById('verdictIcon');
  const executiveCard = document.getElementById('executiveCard');

  const verdict = review.verdict || 'COMMENT';
  verdictText.textContent = verdict.replace('_', ' ');

  if (verdict === 'REQUEST_CHANGES') {
    verdictBadge.className = 'px-3.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center space-x-1.5 bg-rose-500/20 text-rose-300 border border-rose-500/40 glow-danger';
    verdictIcon.setAttribute('data-lucide', 'alert-octagon');
    executiveCard.style.borderColor = 'rgba(239, 68, 68, 0.4)';
  } else if (verdict === 'APPROVE') {
    verdictBadge.className = 'px-3.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center space-x-1.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 glow-success';
    verdictIcon.setAttribute('data-lucide', 'check-circle-2');
    executiveCard.style.borderColor = 'rgba(16, 185, 129, 0.4)';
  } else {
    verdictBadge.className = 'px-3.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center space-x-1.5 bg-amber-500/20 text-amber-300 border border-amber-500/40 glow-warning';
    verdictIcon.setAttribute('data-lucide', 'help-circle');
    executiveCard.style.borderColor = 'rgba(245, 158, 11, 0.4)';
  }

  // Engine Used
  document.getElementById('engineText').textContent = review.engine_used || 'CodeSentinel Engine';

  // Executive Summary
  document.getElementById('executiveSummaryText').textContent = review.executive_summary || 'Review completed.';

  // Issue Counts
  const counts = review.counts || { critical: 0, high: 0, medium: 0, low: 0 };
  document.getElementById('countCritical').textContent = counts.critical || 0;
  document.getElementById('countHigh').textContent = counts.high || 0;
  document.getElementById('countMedium').textContent = counts.medium || 0;
  document.getElementById('countLow').textContent = counts.low || 0;

  // Score Radial Meter & Grade
  const score = Math.max(0, Math.min(100, review.score || 0));
  document.getElementById('scoreValue').textContent = score;
  const scoreCircle = document.getElementById('scoreCircle');
  scoreCircle.style.setProperty('--score-pct', `${score}%`);

  const gradeBadge = document.getElementById('gradeBadge');
  const riskLevelText = document.getElementById('riskLevelText');
  const grade = review.grade || 'C';
  gradeBadge.textContent = grade;

  if (grade === 'A+' || grade === 'A') {
    gradeBadge.className = 'text-2xl font-black text-emerald-400';
    riskLevelText.textContent = 'Low Risk';
    riskLevelText.className = 'text-[11px] text-emerald-400/80 font-medium';
    scoreCircle.style.setProperty('--accent-cyan', '#10b981');
  } else if (grade === 'B' || grade === 'C') {
    gradeBadge.className = 'text-2xl font-black text-amber-400';
    riskLevelText.textContent = 'Moderate Risk';
    riskLevelText.className = 'text-[11px] text-amber-400/80 font-medium';
    scoreCircle.style.setProperty('--accent-cyan', '#f59e0b');
  } else {
    gradeBadge.className = 'text-2xl font-black text-rose-400';
    riskLevelText.textContent = 'Critical Risk';
    riskLevelText.className = 'text-[11px] text-rose-400/80 font-medium';
    scoreCircle.style.setProperty('--accent-cyan', '#ef4444');
  }

  // Active file name
  document.getElementById('activeReviewFileName').textContent = state.activeFileName;

  // Tab counts
  const totalIssues = (review.comments || []).length;
  document.getElementById('tabIssuesCount').textContent = totalIssues;

  // Render Tabs
  renderInteractiveCodeView(review);
  renderIssuesList(review.comments || []);
  renderArchitectureRisks(review);
  renderMarkdownExport(review);

  // Switch to code tab by default
  switchResultTab('code-tab');

  lucide.createIcons();
}

// Render Interactive Line-by-Line Code View
function renderInteractiveCodeView(review) {
  const container = document.getElementById('codeLinesContainer');
  container.innerHTML = '';

  const lines = state.activeCode.split('\n');
  const commentsByLine = {};

  (review.comments || []).forEach(comment => {
    const lineNum = comment.line_number || 1;
    if (!commentsByLine[lineNum]) commentsByLine[lineNum] = [];
    commentsByLine[lineNum].push(comment);
  });

  lines.forEach((lineText, idx) => {
    const lineNum = idx + 1;
    const issuesOnLine = commentsByLine[lineNum] || [];

    let lineSeverityClass = '';
    if (issuesOnLine.some(i => i.severity === 'critical')) lineSeverityClass = 'line-critical';
    else if (issuesOnLine.some(i => i.severity === 'high')) lineSeverityClass = 'line-high';
    else if (issuesOnLine.some(i => i.severity === 'medium')) lineSeverityClass = 'line-medium';
    else if (issuesOnLine.some(i => i.severity === 'low')) lineSeverityClass = 'line-low';

    const lineRow = document.createElement('div');
    lineRow.className = `code-line ${lineSeverityClass}`;
    
    // Line number element
    const numEl = document.createElement('div');
    numEl.className = 'line-num';
    numEl.textContent = lineNum;

    // Code content element
    const contentEl = document.createElement('div');
    contentEl.className = 'line-content';
    contentEl.textContent = lineText || ' ';

    lineRow.appendChild(numEl);
    lineRow.appendChild(contentEl);
    container.appendChild(lineRow);

    // If issues exist on this line, render inline comment box directly underneath
    if (issuesOnLine.length > 0) {
      issuesOnLine.forEach(issue => {
        const commentBox = document.createElement('div');
        commentBox.className = 'inline-comment-box p-3.5 border border-slate-700/80';
        
        let badgeClass = 'badge-medium';
        if (issue.severity === 'critical') badgeClass = 'badge-critical';
        else if (issue.severity === 'high') badgeClass = 'badge-high';
        else if (issue.severity === 'low') badgeClass = 'badge-low';

        commentBox.innerHTML = `
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center space-x-2">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${badgeClass}">
                ${issue.severity}
              </span>
              <span class="text-xs font-semibold text-white">${escapeHtml(issue.title)}</span>
              <span class="text-[10px] text-slate-400 capitalize">(${escapeHtml(issue.category || 'quality')})</span>
            </div>
            <span class="text-[10px] text-slate-500 font-mono">Line ${lineNum}</span>
          </div>

          <p class="text-xs text-slate-300 mt-2 leading-relaxed">
            ${escapeHtml(issue.description)}
          </p>

          ${issue.suggestion ? `
            <div class="mt-2.5 bg-slate-950 p-2.5 rounded border border-slate-800">
              <div class="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                <span class="font-semibold text-emerald-400 flex items-center space-x-1">
                  <i data-lucide="check" class="w-3 h-3"></i>
                  <span>Suggested Fix:</span>
                </span>
                <button onclick="copyToClipboard('${escapeJs(issue.suggestion)}', this)" class="text-slate-400 hover:text-white flex items-center space-x-1 transition text-[10px]">
                  <i data-lucide="copy" class="w-3 h-3"></i>
                  <span>Copy Fix</span>
                </button>
              </div>
              <pre class="font-mono text-xs text-emerald-300 whitespace-pre-wrap">${escapeHtml(issue.suggestion)}</pre>
            </div>
          ` : ''}
        `;

        container.appendChild(commentBox);
      });
    }
  });
}

// Render Issues Breakdown List
function renderIssuesList(comments) {
  const container = document.getElementById('issuesListContainer');
  container.innerHTML = '';

  const filtered = state.filterSeverity === 'all' 
    ? comments 
    : comments.filter(c => c.severity === state.filterSeverity);

  document.getElementById('filteredCount').textContent = filtered.length;

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-500 text-xs">
        No issues matching the selected severity filter.
      </div>
    `;
    return;
  }

  filtered.forEach(issue => {
    let badgeClass = 'badge-medium';
    if (issue.severity === 'critical') badgeClass = 'badge-critical';
    else if (issue.severity === 'high') badgeClass = 'badge-high';
    else if (issue.severity === 'low') badgeClass = 'badge-low';

    const card = document.createElement('div');
    card.className = 'glass-card p-4 space-y-2';
    card.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase ${badgeClass}">${issue.severity}</span>
          <h4 class="text-xs font-semibold text-slate-200">${escapeHtml(issue.title)}</h4>
        </div>
        <span class="text-xs text-slate-400 font-mono">${escapeHtml(issue.file_path || 'file')}:${issue.line_number || 1}</span>
      </div>

      <p class="text-xs text-slate-300 leading-relaxed">${escapeHtml(issue.description)}</p>

      ${issue.suggestion ? `
        <div class="mt-2 bg-slate-950 p-2.5 rounded border border-slate-800/80">
          <div class="flex items-center justify-between text-[11px] mb-1">
            <span class="text-emerald-400 font-medium">Recommended Action:</span>
            <button onclick="copyToClipboard('${escapeJs(issue.suggestion)}', this)" class="text-slate-400 hover:text-white text-[10px] flex items-center space-x-1">
              <i data-lucide="copy" class="w-3 h-3"></i>
              <span>Copy</span>
            </button>
          </div>
          <pre class="font-mono text-xs text-emerald-300 whitespace-pre-wrap">${escapeHtml(issue.suggestion)}</pre>
        </div>
      ` : ''}
    `;
    container.appendChild(card);
  });
}

function filterIssues(severity) {
  state.filterSeverity = severity;
  if (state.currentReview) {
    renderIssuesList(state.currentReview.comments || []);
    lucide.createIcons();
  }
}

// Render Architecture & Commendations
function renderArchitectureRisks(review) {
  const risksList = document.getElementById('keyRisksList');
  const notesList = document.getElementById('positiveNotesList');

  risksList.innerHTML = '';
  notesList.innerHTML = '';

  const risks = review.key_risks || [];
  if (risks.length === 0) {
    risksList.innerHTML = '<li class="text-slate-500">No critical architectural risks detected.</li>';
  } else {
    risks.forEach(r => {
      const li = document.createElement('li');
      li.className = 'flex items-start space-x-2';
      li.innerHTML = `
        <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5"></i>
        <span>${escapeHtml(r)}</span>
      `;
      risksList.appendChild(li);
    });
  }

  const notes = review.positive_notes || [];
  if (notes.length === 0) {
    notesList.innerHTML = '<li class="text-slate-500">Standard implementation.</li>';
  } else {
    notes.forEach(n => {
      const li = document.createElement('li');
      li.className = 'flex items-start space-x-2';
      li.innerHTML = `
        <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5"></i>
        <span>${escapeHtml(n)}</span>
      `;
      notesList.appendChild(li);
    });
  }
}

// Render Markdown PR Review Output
function renderMarkdownExport(review) {
  const mdArea = document.getElementById('markdownExportArea');
  const verdictEmoji = review.verdict === 'APPROVE' ? '✅' : (review.verdict === 'REQUEST_CHANGES' ? '❌' : '⚠️');
  
  let md = `## ${verdictEmoji} CodeSentinel AI Review Summary\n\n`;
  md += `**Verdict:** \`${review.verdict}\` | **Health Score:** \`${review.score}/100\` (Grade: **${review.grade}**) | **Engine:** ${review.engine_used}\n\n`;
  md += `### 📋 Executive Summary\n${review.executive_summary}\n\n`;

  const counts = review.counts || {};
  md += `| Critical | High | Medium | Low |\n`;
  md += `| :---: | :---: | :---: | :---: |\n`;
  md += `| ${counts.critical || 0} | ${counts.high || 0} | ${counts.medium || 0} | ${counts.low || 0} |\n\n`;

  if (review.comments && review.comments.length > 0) {
    md += `### 🔍 Detailed Findings & Inline Suggestions\n\n`;
    review.comments.forEach((c, i) => {
      md += `#### ${i + 1}. [${c.severity.toUpperCase()}] ${c.title} (${c.file_path || 'file'}:${c.line_number || 1})\n`;
      md += `${c.description}\n\n`;
      if (c.suggestion) {
        md += `\`\`\`suggestion\n${c.suggestion}\n\`\`\`\n\n`;
      }
    });
  }

  if (review.key_risks && review.key_risks.length > 0) {
    md += `### ⚠️ Key Risks & Considerations\n`;
    review.key_risks.forEach(r => md += `- ${r}\n`);
    md += `\n`;
  }

  md += `---\n*Generated autonomously by CodeSentinel AI*`;
  mdArea.textContent = md;
}

// Copy Markdown
function copyMarkdownReport() {
  const text = document.getElementById('markdownExportArea').textContent;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('copyBtnText');
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy Markdown'; }, 2000);
    showToast('Markdown report copied to clipboard!');
  });
}

// Post Review Directly to GitHub
async function postReviewToGithub() {
  const token = state.settings.githubToken;
  if (!token) {
    showToast('GitHub Personal Access Token required in Settings.', 'warning');
    toggleSettingsModal(true);
    return;
  }

  const prUrl = document.getElementById('githubPrUrl').value.trim();
  if (!prUrl) {
    showToast('No GitHub PR URL available to submit to.', 'warning');
    return;
  }

  const body = document.getElementById('markdownExportArea').textContent;
  const event = state.currentReview.verdict === 'APPROVE' ? 'APPROVE' : (state.currentReview.verdict === 'REQUEST_CHANGES' ? 'REQUEST_CHANGES' : 'COMMENT');

  try {
    const res = await fetch('/api/github/post-review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pr_url: prUrl,
        github_token: token,
        event: event,
        body: body
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to submit review');
    showToast('Successfully published review to GitHub PR!');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Result Tabs Navigation
function switchResultTab(tabId) {
  state.activeTab = tabId;
  const tabIds = ['code-tab', 'issues-tab', 'risks-tab', 'export-tab'];
  
  tabIds.forEach(id => {
    const btn = document.getElementById(
      id === 'code-tab' ? 'tabBtnCode' :
      id === 'issues-tab' ? 'tabBtnIssues' :
      id === 'risks-tab' ? 'tabBtnRisks' : 'tabBtnExport'
    );
    const content = document.getElementById(
      id === 'code-tab' ? 'codeTabContent' :
      id === 'issues-tab' ? 'issuesTabContent' :
      id === 'risks-tab' ? 'risksTabContent' : 'exportTabContent'
    );

    if (id === tabId) {
      btn.className = 'px-4 py-3 text-xs font-semibold border-b-2 border-cyan-400 text-cyan-400 flex items-center space-x-2 transition';
      content.classList.remove('hidden');
    } else {
      btn.className = 'px-4 py-3 text-xs font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center space-x-2 transition';
      content.classList.add('hidden');
    }
  });

  lucide.createIcons();
}

// Utilities
function showLoading(show, message = '') {
  const el = document.getElementById('loadingIndicator');
  const text = document.getElementById('loadingStatusText');
  if (show) {
    text.textContent = message;
    el.classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
  } else {
    el.classList.add('hidden');
  }
}

function showToast(msg, type = 'info') {
  const toast = document.getElementById('toast');
  const text = document.getElementById('toastMsg');
  const icon = document.getElementById('toastIcon');

  text.textContent = msg;
  if (type === 'error') {
    toast.className = 'fixed bottom-6 right-6 px-4 py-3 rounded-lg bg-rose-950 border border-rose-800 shadow-xl text-xs font-medium text-rose-200 flex items-center space-x-2 transition-all duration-300 transform translate-y-0 opacity-100 z-50';
    icon.setAttribute('data-lucide', 'alert-circle');
  } else if (type === 'warning') {
    toast.className = 'fixed bottom-6 right-6 px-4 py-3 rounded-lg bg-amber-950 border border-amber-800 shadow-xl text-xs font-medium text-amber-200 flex items-center space-x-2 transition-all duration-300 transform translate-y-0 opacity-100 z-50';
    icon.setAttribute('data-lucide', 'alert-triangle');
  } else {
    toast.className = 'fixed bottom-6 right-6 px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 shadow-xl text-xs font-medium text-slate-200 flex items-center space-x-2 transition-all duration-300 transform translate-y-0 opacity-100 z-50';
    icon.setAttribute('data-lucide', 'check-circle');
  }

  lucide.createIcons();
  setTimeout(() => {
    toast.className = toast.className.replace('translate-y-0 opacity-100', 'translate-y-24 opacity-0');
  }, 3500);
}

function copyToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    if (btnElement) {
      const orig = btnElement.innerHTML;
      btnElement.innerHTML = '<span class="text-emerald-400">Copied!</span>';
      setTimeout(() => { btnElement.innerHTML = orig; lucide.createIcons(); }, 1800);
    }
    showToast('Copied to clipboard!');
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeJs(str) {
  if (!str) return '';
  return String(str)
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '');
}

