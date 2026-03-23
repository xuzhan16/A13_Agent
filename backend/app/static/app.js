const state = {
  graph: null,
  lastRequest: null,
  lastReportResponse: null,
  parsedResumeText: '',
  selectedMatchIndex: 0,
};

const DEMO_SAMPLE = {
  name: '李华',
  school: '某理工大学',
  major: '软件工程',
  degree: '本科',
  graduationYear: '2026',
  targetRoles: 'Java开发工程师, 软件测试工程师',
  targetCities: '深圳, 上海',
  desiredIndustries: '互联网, 计算机软件',
  selfDescription: '学习能力强，善于沟通，喜欢工程化开发，也愿意通过项目不断补齐短板。',
  resumeText: '熟悉 Java、Spring Boot、MySQL、Redis，完成过校园管理系统和博客系统开发，参与企业管理系统开发与测试联调。',
  manualSkills: 'Java, Spring Boot, MySQL, Redis',
  projectExperiences: '校园管理系统：负责后端接口设计、数据库设计、权限模块开发。\n博客系统：负责登录、文章模块和部署。',
  internshipExperiences: '在软件公司参与企业管理系统开发与测试联调。',
  campusExperiences: '技术社团负责人，组织校内开发训练营。',
  certificates: '英语四级',
  followUpAnswers: '你偏向什么岗位：希望优先做后端开发，也接受测试开发方向。',
};

const els = {
  heroJobCount: document.getElementById('heroJobCount'),
  heroGraphNodes: document.getElementById('heroGraphNodes'),
  heroMode: document.getElementById('heroMode'),
  metricKnowledgeSource: document.getElementById('metricKnowledgeSource'),
  metricProfileMode: document.getElementById('metricProfileMode'),
  metricReportMode: document.getElementById('metricReportMode'),
  metricTopJob: document.getElementById('metricTopJob'),
  statusBar: document.getElementById('statusBar'),
  resumeFile: document.getElementById('resumeFile'),
  resumePreview: document.getElementById('resumePreview'),
  resumeParseMeta: document.getElementById('resumeParseMeta'),
  followUpContainer: document.getElementById('followUpContainer'),
  questionCount: document.getElementById('questionCount'),
  matchContainer: document.getElementById('matchContainer'),
  graphSvg: document.getElementById('graphSvg'),
  executiveSummary: document.getElementById('executiveSummary'),
  reportPreview: document.getElementById('reportPreview'),
  reportModeBadge: document.getElementById('reportModeBadge'),
  evidenceMatchName: document.getElementById('evidenceMatchName'),
  evidenceEmpty: document.getElementById('evidenceEmpty'),
  evidenceTracePanel: document.getElementById('evidenceTracePanel'),
  evidenceScore: document.getElementById('evidenceScore'),
  evidenceFormula: document.getElementById('evidenceFormula'),
  evidenceRuleVersion: document.getElementById('evidenceRuleVersion'),
  evidenceKbVersion: document.getElementById('evidenceKbVersion'),
  evidenceDimensionList: document.getElementById('evidenceDimensionList'),
  evidenceRawCount: document.getElementById('evidenceRawCount'),
  evidenceRawList: document.getElementById('evidenceRawList'),
};

function setStatus(message, mode = 'info') {
  els.statusBar.textContent = message;
  els.statusBar.style.background = mode === 'error'
    ? 'rgba(200, 91, 61, 0.12)'
    : mode === 'success'
      ? 'rgba(45, 106, 79, 0.12)'
      : 'rgba(35, 74, 120, 0.08)';
  els.statusBar.style.color = mode === 'error'
    ? '#8d2d1a'
    : mode === 'success'
      ? '#2d6a4f'
      : '#234a78';
}

function splitCsv(value) {
  return value.split(/[，,]/).map(item => item.trim()).filter(Boolean);
}

function splitLines(value) {
  return value.split(/\r?\n/).map(item => item.trim()).filter(Boolean);
}

function parseFollowUpAnswers(value) {
  return splitLines(value).map((line) => {
    const parts = line.split(/[:：]/);
    if (parts.length >= 2) {
      return { question: parts[0].trim(), answer: parts.slice(1).join('：').trim() };
    }
    return { question: '补充信息', answer: line.trim() };
  }).filter(item => item.answer);
}

function collectRequest() {
  return {
    intake: {
      basic_info: {
        name: document.getElementById('name').value.trim(),
        school: document.getElementById('school').value.trim(),
        major: document.getElementById('major').value.trim(),
        degree: document.getElementById('degree').value.trim(),
        graduation_year: Number(document.getElementById('graduationYear').value) || null,
      },
      preference: {
        target_roles: splitCsv(document.getElementById('targetRoles').value),
        target_cities: splitCsv(document.getElementById('targetCities').value),
        desired_industries: splitCsv(document.getElementById('desiredIndustries').value),
        prefer_stability: false,
        prefer_innovation: true,
      },
      resume_text: document.getElementById('resumeText').value.trim(),
      self_description: document.getElementById('selfDescription').value.trim(),
      manual_skills: splitCsv(document.getElementById('manualSkills').value),
      project_experiences: splitLines(document.getElementById('projectExperiences').value),
      internship_experiences: splitLines(document.getElementById('internshipExperiences').value),
      campus_experiences: splitLines(document.getElementById('campusExperiences').value),
      certificates: splitCsv(document.getElementById('certificates').value),
      follow_up_answers: parseFollowUpAnswers(document.getElementById('followUpAnswers').value),
    },
    preferred_job_family: splitCsv(document.getElementById('targetRoles').value)[0] || null,
    top_k_matches: 3,
    max_follow_up_questions: 4,
  };
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response;
}

function loadSample() {
  Object.entries(DEMO_SAMPLE).forEach(([key, value]) => {
    const element = document.getElementById(key);
    if (element) {
      element.value = value;
    }
  });
  setStatus('已加载比赛演示样例，可以直接生成报告。', 'success');
}

async function parseResume() {
  const file = els.resumeFile.files?.[0];
  if (!file) {
    setStatus('请先选择一个简历文件。', 'error');
    return;
  }
  const formData = new FormData();
  formData.append('file', file);
  setStatus('正在解析简历文件...');
  try {
    const response = await apiFetch('/api/v1/planning/resume/parse', { method: 'POST', body: formData });
    const data = await response.json();
    state.parsedResumeText = data.extracted_text || '';
    document.getElementById('resumeText').value = state.parsedResumeText;
    els.resumePreview.textContent = data.preview || '未提取到文本';
    els.resumeParseMeta.textContent = `${data.file_name} · ${data.char_count} 字 · ${data.section_hints.join(' / ') || '未识别章节'}`;
    setStatus('简历解析完成，已同步填充到简历文本。', 'success');
  } catch (error) {
    setStatus(`简历解析失败：${error.message}`, 'error');
  }
}

function renderFollowUps(questions) {
  if (!questions?.length) {
    els.followUpContainer.className = 'stack-list empty-state';
    els.followUpContainer.textContent = '当前没有额外追问，信息已经比较完整。';
    els.questionCount.textContent = '0';
    return;
  }
  els.questionCount.textContent = String(questions.length);
  els.followUpContainer.className = 'stack-list';
  els.followUpContainer.innerHTML = questions.map((item) => `
    <article class="question-card">
      <h3>P${item.priority} · ${escapeHtml(item.question)}</h3>
      <p>${escapeHtml(item.reason)}</p>
    </article>
  `).join('');
}

function renderMatches(matches) {
  if (!matches?.length) {
    els.matchContainer.className = 'stack-list empty-state';
    els.matchContainer.textContent = 'No matches yet';
    return;
  }
  if (state.selectedMatchIndex >= matches.length) {
    state.selectedMatchIndex = 0;
  }
  els.matchContainer.className = 'stack-list';
  els.matchContainer.innerHTML = matches.map((item, index) => `
    <article class="match-card ${index === state.selectedMatchIndex ? 'active' : ''}">
      <span class="match-score">??? ${item.overall_score}</span>
      <h3>${escapeHtml(item.job_family)}</h3>
      <p>${escapeHtml(item.summary)}</p>
      <div class="skill-pills">
        ${(item.matched_skills || []).slice(0, 4).map((skill) => `<span class="pill">${escapeHtml(skill)}</span>`).join('')}
        ${(item.missing_skills || []).slice(0, 3).map((skill) => `<span class="pill warn">???${escapeHtml(skill)}</span>`).join('')}
      </div>
      <div class="match-actions">
        <button class="ghost-btn evidence-btn" data-match-index="${index}">View Evidence</button>
      </div>
    </article>
  `).join('');
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function markdownToHtml(markdown) {
  const lines = String(markdown || '').split(/\r?\n/);
  const chunks = [];
  let inList = false;

  const closeList = () => {
    if (inList) {
      chunks.push('</ul>');
      inList = false;
    }
  };

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      closeList();
      return;
    }
    if (trimmed.startsWith('### ')) {
      closeList();
      chunks.push(`<h3>${escapeHtml(trimmed.slice(4))}</h3>`);
      return;
    }
    if (trimmed.startsWith('## ')) {
      closeList();
      chunks.push(`<h2>${escapeHtml(trimmed.slice(3))}</h2>`);
      return;
    }
    if (trimmed.startsWith('# ')) {
      closeList();
      chunks.push(`<h1>${escapeHtml(trimmed.slice(2))}</h1>`);
      return;
    }
    if (trimmed.startsWith('- ')) {
      if (!inList) {
        chunks.push('<ul>');
        inList = true;
      }
      chunks.push(`<li>${escapeHtml(trimmed.slice(2))}</li>`);
      return;
    }
    closeList();
    chunks.push(`<p>${escapeHtml(trimmed)}</p>`);
  });

  closeList();
  return chunks.join('');
}

function renderReport(report) {
  if (!report) {
    els.executiveSummary.textContent = 'Generate a report first';
    els.reportPreview.className = 'report-preview empty-state';
    els.reportPreview.textContent = 'Report preview will appear here';
    return;
  }
  els.executiveSummary.textContent = report.executive_summary || report.overview || 'No executive summary';
  els.reportModeBadge.textContent = report.generation_mode || 'template';
  els.reportPreview.className = 'report-preview';
  els.reportPreview.innerHTML = markdownToHtml(report.report_markdown);
}

function renderEvidenceTrace(match) {
  const trace = match?.evidence_trace;
  if (!trace) {
    els.evidenceMatchName.textContent = 'No match selected';
    els.evidenceEmpty.classList.remove('hidden');
    els.evidenceTracePanel.classList.add('hidden');
    els.evidenceDimensionList.innerHTML = '';
    els.evidenceRawList.innerHTML = '';
    els.evidenceRawCount.textContent = '0';
    return;
  }

  els.evidenceMatchName.textContent = match.job_family || 'Untitled match';
  els.evidenceScore.textContent = `${trace.final_score?.display_score ?? '-'} pts`;
  els.evidenceFormula.textContent = trace.final_score?.formula || '-';
  els.evidenceRuleVersion.textContent = trace.versions?.score_rule_version || '-';
  els.evidenceKbVersion.textContent = trace.versions?.knowledge_base_version || '-';
  els.evidenceEmpty.classList.add('hidden');
  els.evidenceTracePanel.classList.remove('hidden');

  const dimensions = trace.dimensions || [];
  els.evidenceDimensionList.innerHTML = dimensions.map((dimension) => `
    <article class="dimension-trace-card">
      <div class="dimension-trace-head">
        <div>
          <h3>${escapeHtml(dimension.name)}</h3>
          <p>${escapeHtml(dimension.formula || 'n/a')}</p>
        </div>
        <div class="dimension-score-box">
          <strong>${escapeHtml(dimension.score)}</strong>
          <span>Contribution ${escapeHtml(dimension.weighted_score)}</span>
        </div>
      </div>
      <div class="dimension-bar"><span style="width: ${Math.max(6, Math.min(Number(dimension.score) || 0, 100))}%"></span></div>
      <div class="indicator-trace-list">
        ${(dimension.indicators || []).map((indicator) => `
          <section class="indicator-card">
            <div class="indicator-topline">
              <strong>${escapeHtml(indicator.indicator_name)}</strong>
              <span>${escapeHtml(indicator.score)} x ${escapeHtml(indicator.weight_in_dimension)} = ${escapeHtml(indicator.weighted_score)}</span>
            </div>
            <p class="indicator-formula">Rule: ${escapeHtml(indicator.formula || indicator.rule_id || 'n/a')}</p>
            <p class="indicator-raw">Raw value: ${escapeHtml(formatValue(indicator.raw_value))}</p>
            ${(indicator.deductions || []).length ? `<div class="deduction-list">${indicator.deductions.map((item) => `<span class="pill warn">${escapeHtml(item.reason)} (${escapeHtml(item.delta)})</span>`).join('')}</div>` : ''}
            ${(indicator.evidence_refs || []).length ? `<div class="evidence-ref-list">${indicator.evidence_refs.map((item) => `<span class="pill ref">${escapeHtml(item)}</span>`).join('')}</div>` : ''}
          </section>
        `).join('')}
      </div>
      <div class="dimension-evidence-list">
        ${(dimension.evidences || []).map((item) => `
          <article class="evidence-card-mini">
            <div class="evidence-meta">
              <span class="badge">${escapeHtml(item.evidence_id || '-')}</span>
              <span>${escapeHtml(item.source_type || item.source || '-')}</span>
            </div>
            <p>${escapeHtml(item.excerpt || '')}</p>
          </article>
        `).join('') || '<div class="empty-inline">No source evidence in this dimension.</div>'}
      </div>
    </article>
  `).join('');

  const evidences = trace.evidences || [];
  els.evidenceRawCount.textContent = String(evidences.length);
  els.evidenceRawList.innerHTML = evidences.map((item) => `
    <article class="evidence-raw-card">
      <div class="evidence-meta">
        <span class="badge">${escapeHtml(item.evidence_id || '-')}</span>
        <span>${escapeHtml(item.source_type || item.source || '-')}</span>
        <span>${escapeHtml(item.source_ref || '-')}</span>
      </div>
      <p>${escapeHtml(item.excerpt || '')}</p>
      <div class="evidence-footer">
        <span>confidence: ${escapeHtml(item.confidence ?? '-')}</span>
        <span>rule: ${escapeHtml(item.extract_rule || '-')}</span>
      </div>
    </article>
  `).join('');
}

function formatValue(value) {
  if (value == null || value === '') {
    return '-';
  }
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value, null, 0);
    } catch (error) {
      return String(value);
    }
  }
  return String(value);
}

function polarPosition(cx, cy, radius, angle) {
  return {
    x: cx + Math.cos(angle) * radius,
    y: cy + Math.sin(angle) * radius,
  };
}

function renderGraph(graph) {
  if (!graph) {
    return;
  }
  const svg = els.graphSvg;
  svg.innerHTML = '';
  const width = 1100;
  const height = 620;
  const centerX = width / 2;
  const centerY = height / 2;
  const jobNodes = graph.nodes.filter((node) => node.node_type === 'job_family');
  const stageNodes = graph.nodes.filter((node) => node.node_type !== 'job_family');
  const positionMap = new Map();

  jobNodes.forEach((node, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(jobNodes.length, 1) - Math.PI / 2;
    positionMap.set(node.id, polarPosition(centerX, centerY, 170, angle));
  });
  stageNodes.forEach((node, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(stageNodes.length, 1) - Math.PI / 2 + 0.18;
    positionMap.set(node.id, polarPosition(centerX, centerY, 265, angle));
  });

  graph.edges.forEach((edge) => {
    const source = positionMap.get(edge.source);
    const target = positionMap.get(edge.target);
    if (!source || !target) return;
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', source.x);
    line.setAttribute('y1', source.y);
    line.setAttribute('x2', target.x);
    line.setAttribute('y2', target.y);
    line.setAttribute('class', `graph-edge ${edge.edge_type}`);
    svg.appendChild(line);
  });

  graph.nodes.forEach((node) => {
    const pos = positionMap.get(node.id);
    if (!pos) return;
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('class', 'graph-node');
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    const radius = node.node_type === 'job_family' ? 38 : 26;
    circle.setAttribute('cx', pos.x);
    circle.setAttribute('cy', pos.y);
    circle.setAttribute('r', radius);
    circle.setAttribute('fill', node.node_type === 'job_family' ? '#c85b3d' : '#234a78');
    circle.setAttribute('fill-opacity', node.node_type === 'job_family' ? '0.9' : '0.85');
    g.appendChild(circle);

    const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
    title.textContent = `${node.label}\n样本数：${node.sample_count || 0}\n技能：${(node.top_skills || []).join('、')}`;
    g.appendChild(title);

    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', pos.x);
    text.setAttribute('y', pos.y - 4);
    text.setAttribute('text-anchor', 'middle');
    const lines = breakLabel(node.label, node.node_type === 'job_family' ? 7 : 5);
    lines.forEach((lineText, idx) => {
      const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
      tspan.setAttribute('x', pos.x);
      tspan.setAttribute('dy', idx === 0 ? '0' : '14');
      tspan.textContent = lineText;
      text.appendChild(tspan);
    });
    text.setAttribute('fill', '#fffaf3');
    text.setAttribute('font-size', node.node_type === 'job_family' ? '12' : '11');
    g.appendChild(text);
    svg.appendChild(g);
  });

  els.heroGraphNodes.textContent = String(graph.metadata?.node_count || graph.nodes.length);
}

function breakLabel(label, chunkSize) {
  const result = [];
  let text = String(label || '');
  while (text.length > chunkSize) {
    result.push(text.slice(0, chunkSize));
    text = text.slice(chunkSize);
  }
  if (text) result.push(text);
  return result.slice(0, 3);
}

function renderMetrics(response) {
  const metadata = response?.metadata || {};
  const topMatch = response?.match_results?.[0];
  els.metricKnowledgeSource.textContent = metadata.knowledge_base_source || '-';
  els.metricProfileMode.textContent = metadata.profile_mode || '-';
  els.metricReportMode.textContent = metadata.report_mode || '-';
  els.metricTopJob.textContent = topMatch ? `${topMatch.job_family} · ${topMatch.overall_score}` : '-';
  els.heroMode.textContent = metadata.llm_enabled ? 'LLM' : 'Rule';
}

async function loadGraph() {
  try {
    const response = await apiFetch('/api/v1/planning/job-graph');
    state.graph = await response.json();
    renderGraph(state.graph);
  } catch (error) {
    setStatus(`加载岗位图谱失败：${error.message}`, 'error');
  }
}

async function loadJobFamilies() {
  try {
    const response = await apiFetch('/api/v1/planning/job-families');
    const data = await response.json();
    els.heroJobCount.textContent = String(data.length);
  } catch (error) {
    setStatus(`加载岗位画像失败：${error.message}`, 'error');
  }
}

async function generateFollowUps() {
  const request = collectRequest();
  state.lastRequest = request;
  setStatus('正在生成 Agent 追问...');
  try {
    const response = await apiFetch('/api/v1/planning/follow-up-questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        intake: request.intake,
        preferred_job_family: request.preferred_job_family,
        top_k_matches: request.top_k_matches,
        max_questions: request.max_follow_up_questions,
      }),
    });
    const data = await response.json();
    renderFollowUps(data.questions);
    els.metricKnowledgeSource.textContent = data.metadata.knowledge_base_source;
    els.metricProfileMode.textContent = data.metadata.profile_mode;
    els.heroMode.textContent = data.metadata.llm_enabled ? 'LLM' : 'Rule';
    setStatus('Agent 追问已生成。', 'success');
  } catch (error) {
    setStatus(`生成追问失败：${error.message}`, 'error');
  }
}

async function generateReport() {
  const request = collectRequest();
  state.lastRequest = request;
  setStatus('Generating career report...');
  try {
    const response = await apiFetch('/api/v1/planning/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    const data = await response.json();
    state.lastReportResponse = data;
    state.selectedMatchIndex = 0;
    renderMetrics(data);
    renderMatches(data.match_results);
    renderFollowUps(data.follow_up_questions);
    renderReport(data.report);
    renderEvidenceTrace(data.match_results?.[state.selectedMatchIndex]);
    setStatus('Career report generated.', 'success');
  } catch (error) {
    setStatus(`Report generation failed: ${error.message}`, 'error');
  }
}

async function downloadMarkdown() {
  if (!state.lastRequest) {
    setStatus('请先生成一份职业报告，再导出 Markdown。', 'error');
    return;
  }
  setStatus('正在导出 Markdown...');
  try {
    const response = await apiFetch('/api/v1/planning/report/export-markdown', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.lastRequest),
    });
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const fileName = match ? match[1] : 'career_report.md';
    triggerDownload(blob, fileName);
    setStatus('Markdown 导出完成。', 'success');
  } catch (error) {
    setStatus(`导出 Markdown 失败：${error.message}`, 'error');
  }
}

function downloadJson() {
  if (!state.lastReportResponse) {
    setStatus('请先生成职业报告，再导出 JSON。', 'error');
    return;
  }
  const blob = new Blob([JSON.stringify(state.lastReportResponse, null, 2)], { type: 'application/json' });
  triggerDownload(blob, 'career_report.json');
  setStatus('JSON 导出完成。', 'success');
}

function triggerDownload(blob, fileName) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function bindEvents() {
  document.getElementById('loadSampleBtn').addEventListener('click', loadSample);
  document.getElementById('parseResumeBtn').addEventListener('click', parseResume);
  document.getElementById('followUpBtn').addEventListener('click', generateFollowUps);
  document.getElementById('generateBtn').addEventListener('click', generateReport);
  document.getElementById('downloadMarkdownBtn').addEventListener('click', downloadMarkdown);
  document.getElementById('downloadJsonBtn').addEventListener('click', downloadJson);
  els.matchContainer.addEventListener('click', (event) => {
    const button = event.target.closest('.evidence-btn');
    if (!button || !state.lastReportResponse?.match_results?.length) {
      return;
    }
    state.selectedMatchIndex = Number(button.dataset.matchIndex) || 0;
    renderMatches(state.lastReportResponse.match_results);
    renderEvidenceTrace(state.lastReportResponse.match_results[state.selectedMatchIndex]);
    setStatus(`Evidence trace ready: ${state.lastReportResponse.match_results[state.selectedMatchIndex].job_family}`, 'success');
  });
}

async function init() {
  bindEvents();
  loadSample();
  await Promise.all([loadJobFamilies(), loadGraph()]);
  setStatus('前端 Demo 已准备完成，可以直接演示。', 'success');
}

init();
