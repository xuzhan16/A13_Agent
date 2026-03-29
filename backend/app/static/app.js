const state = {
  graph: null,
  personalizedGraph: null,
  lastRequest: null,
  lastReportResponse: null,
  parsedResumeText: '',
  lastStructuredProfile: null,
  lastFormFillSuggestion: null,
  graphInsights: null,
  graphDetailCache: new Map(),
  graphMode: 'global',
  graphSearch: '',
  graphCity: '',
  graphIndustry: '',
  graphNeighborOnly: false,
  selectedGraphNodeId: '',
  renderedGraph: null,
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
  resultNavigator: document.getElementById('resultNavigator'),
  resultNavigatorCount: document.getElementById('resultNavigatorCount'),
  statusBar: document.getElementById('statusBar'),
  resumeFile: document.getElementById('resumeFile'),
  resumePreview: document.getElementById('resumePreview'),
  resumeParseMeta: document.getElementById('resumeParseMeta'),
  applyStructuredBtn: document.getElementById('applyStructuredBtn'),
  structuredEmpty: document.getElementById('structuredEmpty'),
  structuredPanel: document.getElementById('structuredPanel'),
  structuredMeta: document.getElementById('structuredMeta'),
  structuredPendingCount: document.getElementById('structuredPendingCount'),
  structuredBasicInfo: document.getElementById('structuredBasicInfo'),
  structuredSkillCount: document.getElementById('structuredSkillCount'),
  structuredSkillList: document.getElementById('structuredSkillList'),
  structuredUnmatchedList: document.getElementById('structuredUnmatchedList'),
  structuredPendingList: document.getElementById('structuredPendingList'),
  structuredProjectList: document.getElementById('structuredProjectList'),
  structuredInternshipList: document.getElementById('structuredInternshipList'),
  structuredCampusList: document.getElementById('structuredCampusList'),
  structuredCertificateList: document.getElementById('structuredCertificateList'),
  structuredInnovationList: document.getElementById('structuredInnovationList'),
  followUpContainer: document.getElementById('followUpContainer'),
  followUpAnswerHint: document.getElementById('followUpAnswerHint'),
  questionCount: document.getElementById('questionCount'),
  softSkillCount: document.getElementById('softSkillCount'),
  softSkillOverview: document.getElementById('softSkillOverview'),
  trendMeta: document.getElementById('trendMeta'),
  trendPanel: document.getElementById('trendPanel'),
  graphInsightMeta: document.getElementById('graphInsightMeta'),
  graphInsightPanel: document.getElementById('graphInsightPanel'),
  viewPersonalGraphBtn: document.getElementById('viewPersonalGraphBtn'),
  viewGlobalGraphBtn: document.getElementById('viewGlobalGraphBtn'),
  graphSearchInput: document.getElementById('graphSearchInput'),
  graphSearchBtn: document.getElementById('graphSearchBtn'),
  graphCityFilter: document.getElementById('graphCityFilter'),
  graphIndustryFilter: document.getElementById('graphIndustryFilter'),
  graphNeighborBtn: document.getElementById('graphNeighborBtn'),
  graphFilterResetBtn: document.getElementById('graphFilterResetBtn'),
  graphToolbarHint: document.getElementById('graphToolbarHint'),
  personalGraphSummary: document.getElementById('personalGraphSummary'),
  graphDetailMeta: document.getElementById('graphDetailMeta'),
  graphDetailBody: document.getElementById('graphDetailBody'),
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

function setText(element, value) {
  if (!element) return;
  element.textContent = value ?? '';
}

function setHtml(element, value) {
  if (!element) return;
  element.innerHTML = value ?? '';
}

function setClassName(element, value) {
  if (!element) return;
  element.className = value;
}

function setStatus(message, mode = 'info') {
  if (!els.statusBar) return;
  setText(els.statusBar, message);
  els.statusBar.style.background = mode === 'error' ? 'rgba(200, 91, 61, 0.12)' : mode === 'success' ? 'rgba(45, 106, 79, 0.12)' : 'rgba(35, 74, 120, 0.08)';
  els.statusBar.style.color = mode === 'error' ? '#8d2d1a' : mode === 'success' ? '#2d6a4f' : '#234a78';
}

const splitCsv = (value) => String(value || '').split(/[，,]/).map((item) => item.trim()).filter(Boolean);
const splitLines = (value) => String(value || '').split(/\r?\n/).map((item) => item.trim()).filter(Boolean);

function parseFollowUpAnswers(value) {
  return splitLines(value).map((line) => {
    const parts = line.split(/[:：]/);
    if (parts.length >= 2) {
      return { question: parts[0].trim(), answer: parts.slice(1).join('：').trim() };
    }
    return { question: '补充信息', answer: line.trim() };
  }).filter((item) => item.answer);
}

function buildFollowUpAnswerMap(value) {
  const map = new Map();
  parseFollowUpAnswers(value).forEach((item) => {
    const question = String(item.question || '').trim();
    const answer = String(item.answer || '').trim();
    if (!question || !answer) return;
    map.set(question, answer);
  });
  return map;
}

function collectInlineFollowUpAnswers() {
  return Array.from(document.querySelectorAll('.followup-answer-input')).map((element) => ({
    question: String(element.dataset.question || '').trim(),
    answer: String(element.value || '').trim(),
  })).filter((item) => item.question && item.answer);
}

function syncFollowUpAnswerTextarea() {
  const textarea = document.getElementById('followUpAnswers');
  if (!textarea) return;
  const inlineAnswers = collectInlineFollowUpAnswers();
  if (!inlineAnswers.length) return;
  textarea.value = inlineAnswers.map((item) => `${item.question}：${item.answer}`).join('\n');
}

function updateFollowUpAnswerHint() {
  if (!els.followUpAnswerHint) return;
  const inlineAnswers = collectInlineFollowUpAnswers();
  const answeredCount = inlineAnswers.length;
  const totalCount = document.querySelectorAll('.followup-answer-input').length;
  if (!totalCount) {
    els.followUpAnswerHint.classList.add('hidden');
    return;
  }
  els.followUpAnswerHint.classList.remove('hidden');
  setText(els.followUpAnswerHint, `可在每个问题下方直接填写回答（已填写 ${answeredCount}/${totalCount}）。`);
}

function collectFollowUpAnswersForRequest() {
  const inlineAnswers = collectInlineFollowUpAnswers();
  if (inlineAnswers.length) {
    syncFollowUpAnswerTextarea();
    return inlineAnswers;
  }
  return parseFollowUpAnswers(document.getElementById('followUpAnswers').value);
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
      follow_up_answers: collectFollowUpAnswersForRequest(),
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

function escapeHtml(value) {
  return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function formatValue(value) {
  if (value == null || value === '') return '-';
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'object') {
    try { return JSON.stringify(value); } catch (error) { return String(value); }
  }
  return String(value);
}

const formatConfidence = (value) => value == null || Number.isNaN(Number(value)) ? '-' : `${Math.round(Number(value) * 100)}%`;
const fieldStatusLabel = (status) => status === 'confirmed' ? '已确认' : '待确认';
const fieldStatusClass = (status) => status === 'confirmed' ? 'confirmed' : 'pending';

const PENDING_FIELD_TO_INPUT = {
  'basic_info.name': 'name',
  'basic_info.school': 'school',
  'basic_info.major': 'major',
  'basic_info.degree': 'degree',
  'basic_info.graduation_year': 'graduationYear',
};

function setInputValue(id, value) {
  const element = document.getElementById(id);
  if (element) element.value = value == null ? '' : String(value);
}

function clearAutofillHighlights() {
  document.querySelectorAll('.autofilled-field').forEach((element) => element.classList.remove('autofilled-field'));
}

function highlightField(id, options = {}) {
  const element = document.getElementById(id);
  if (!element) return;
  element.classList.add('autofilled-field');
  if (options.focus) {
    element.focus();
    if (typeof element.scrollIntoView === 'function') {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
}

function highlightFields(ids) {
  clearAutofillHighlights();
  ids.filter(Boolean).forEach((id) => highlightField(id));
}

function mapPendingFieldToInput(fieldPath) {
  if (PENDING_FIELD_TO_INPUT[fieldPath]) return PENDING_FIELD_TO_INPUT[fieldPath];
  if (fieldPath.startsWith('project_experiences[')) return 'projectExperiences';
  if (fieldPath.startsWith('internship_experiences[')) return 'internshipExperiences';
  if (fieldPath.startsWith('campus_experiences[')) return 'campusExperiences';
  if (fieldPath.startsWith('certificates[')) return 'certificates';
  return '';
}

function appendSelfDescription(existing, addition) {
  const left = String(existing || '').trim();
  const right = String(addition || '').trim();
  if (!right) return left;
  if (!left) return right;
  if (left.includes(right)) return left;
  return `${left}；${right}`;
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

function loadSample() {
  Object.entries(DEMO_SAMPLE).forEach(([key, value]) => {
    const element = document.getElementById(key);
    if (element) element.value = value;
  });
  setStatus('已加载比赛演示样例，可以直接生成报告。', 'success');
}

function renderStructuredField(label, field) {
  const safeField = field || {};
  const value = safeField.value || '未识别';
  const status = safeField.status || 'pending_confirmation';
  return `
    <article class="structured-field ${fieldStatusClass(status)}">
      <div class="structured-field-head"><span>${escapeHtml(label)}</span><span class="badge ${fieldStatusClass(status)}">${escapeHtml(fieldStatusLabel(status))}</span></div>
      <strong>${escapeHtml(value)}</strong>
      <p>置信度 ${escapeHtml(formatConfidence(safeField.confidence))}</p>
      <p>${escapeHtml(safeField.source_excerpt || safeField.reason || '暂无来源片段')}</p>
    </article>
  `;
}

function renderExperienceItems(items, emptyMessage) {
  if (!items?.length) return `<div class="empty-inline">${escapeHtml(emptyMessage)}</div>`;
  return items.map((item) => {
    const tags = [];
    if (item.organization) tags.push(`组织：${item.organization}`);
    if (item.role) tags.push(`角色：${item.role}`);
    if (item.time_range) tags.push(`时间：${item.time_range}`);
    if (item.tech_stack?.length) tags.push(`技术：${item.tech_stack.join(', ')}`);
    return `
      <article class="structured-item-card ${item.pending_fields?.length ? 'has-pending' : ''}">
        <div class="structured-item-head"><strong>${escapeHtml(item.title || item.organization || '未命名经历')}</strong><span class="badge ${item.pending_fields?.length ? 'pending' : 'confirmed'}">${item.pending_fields?.length ? '待确认' : '已识别'}</span></div>
        ${tags.length ? `<div class="structured-inline-list">${tags.map((tag) => `<span class="pill">${escapeHtml(tag)}</span>`).join('')}</div>` : ''}
        <p>${escapeHtml(item.description || item.source_excerpt || '暂无描述')}</p>
        ${item.achievements?.length ? `<div class="structured-subtext">亮点：${escapeHtml(item.achievements.join('；'))}</div>` : ''}
      </article>
    `;
  }).join('');
}

function renderCertificateItems(items) {
  if (!items?.length) return '<div class="empty-inline">未识别到证书信息</div>';
  return items.map((item) => `
    <article class="structured-item-card ${item.pending_fields?.length ? 'has-pending' : ''}">
      <div class="structured-item-head"><strong>${escapeHtml(item.name || '未命名证书')}</strong><span class="badge ${item.pending_fields?.length ? 'pending' : 'confirmed'}">${item.pending_fields?.length ? '待确认' : '已识别'}</span></div>
      <p>获得时间：${escapeHtml(item.obtained_at || '待补充')}</p>
      <p>${escapeHtml(item.source_excerpt || '')}</p>
    </article>
  `).join('');
}

function renderInnovationItems(innovation) {
  if (!innovation) return '<div class="empty-inline">暂无创新能力指标</div>';
  const groups = [
    { flag: innovation.has_awards, label: '获奖经历', items: innovation.award_items },
    { flag: innovation.has_patents, label: '专利成果', items: innovation.patent_items },
    { flag: innovation.has_publications, label: '论文发表', items: innovation.publication_items },
    { flag: innovation.has_entrepreneurship, label: '创业经历', items: innovation.entrepreneurship_items },
  ].filter((item) => item.flag || item.items?.length);
  if (!groups.length) return '<div class="empty-inline">暂无创新能力指标</div>';
  return groups.map((group) => `
    <article class="structured-item-card">
      <div class="structured-item-head"><strong>${escapeHtml(group.label)}</strong><span class="badge confirmed">已识别</span></div>
      <p>${escapeHtml((group.items || []).join('；') || '已识别相关经历')}</p>
    </article>
  `).join('');
}
function renderPendingItems(items) {
  if (!items?.length) return '<div class="empty-inline">当前没有待确认字段，结构化结果较完整。</div>';
  return items.map((item) => {
    const inputId = mapPendingFieldToInput(item.field_path || '');
    return `
      <article class="pending-item-card" data-field-path="${escapeHtml(item.field_path || '')}" data-input-id="${escapeHtml(inputId)}">
        <div class="pending-item-head">
          <strong>${escapeHtml(item.label || item.field_path)}</strong>
          <span class="badge pending">点击定位</span>
        </div>
        <p>${escapeHtml(item.reason || '待确认')}</p>
        <span>${escapeHtml(item.field_path || '')}</span>
      </article>
    `;
  }).join('');
}

function renderStructuredPreview(profile, suggestion, fileMeta) {
  if (!els.structuredEmpty || !els.structuredPanel || !els.applyStructuredBtn) return;
  if (!profile) {
    els.structuredEmpty.classList.remove('hidden');
    els.structuredPanel.classList.add('hidden');
    els.applyStructuredBtn.disabled = true;
    return;
  }

  const basic = profile.basic_info || {};
  const skills = profile.skills || {};
  const pendingFields = profile.pending_fields || [];
  const matchedSkills = skills.matched_skills || [];
  const unmatched = skills.unmatched_candidates || [];

  els.structuredEmpty.classList.add('hidden');
  els.structuredPanel.classList.remove('hidden');
  els.applyStructuredBtn.disabled = !suggestion;
  const parseMessage = fileMeta.message ? ` · ${fileMeta.message}` : '';
  setText(els.structuredMeta, `${fileMeta.fileName || 'resume'} · ${fileMeta.charCount || 0} 字 · 已抽取 ${matchedSkills.length} 个技能${parseMessage}`);
  setText(els.structuredPendingCount, `${pendingFields.length} 项待确认`);
  setHtml(els.structuredBasicInfo, [
    renderStructuredField('姓名', basic.name),
    renderStructuredField('学校', basic.school),
    renderStructuredField('专业', basic.major),
    renderStructuredField('学历', basic.degree),
    renderStructuredField('毕业年份', basic.graduation_year),
  ].join(''));

  setText(els.structuredSkillCount, String(matchedSkills.length));
  setHtml(els.structuredSkillList, matchedSkills.length
    ? matchedSkills.map((item) => `<span class="pill ${fieldStatusClass(item.confidence >= 0.8 ? 'confirmed' : 'pending')}">${escapeHtml(item.canonical_name)} · ${escapeHtml(item.category)}</span>`).join('')
    : '<span class="empty-inline">未识别到知识库技能</span>');
  setHtml(els.structuredUnmatchedList, unmatched.length
    ? `<span class="structured-subtext">待补充技能候选：${escapeHtml(unmatched.join('、'))}</span>`
    : '<span class="structured-subtext">所有显著技能都已映射到技能词汇表。</span>');

  setHtml(els.structuredPendingList, renderPendingItems(pendingFields));
  setHtml(els.structuredProjectList, renderExperienceItems(profile.project_experiences, '未识别到项目经历'));
  setHtml(els.structuredInternshipList, renderExperienceItems(profile.internship_experiences, '未识别到实习经历'));
  setHtml(els.structuredCampusList, renderExperienceItems(profile.campus_experiences, '未识别到校园经历'));
  setHtml(els.structuredCertificateList, renderCertificateItems(profile.certificates));
  setHtml(els.structuredInnovationList, renderInnovationItems(profile.innovation_indicators));
}

function applyFormFillSuggestion(suggestion, options = {}) {
  if (!suggestion) {
    setStatus('当前没有可应用的结构化结果。', 'error');
    return;
  }

  const changedFields = [];

  setInputValue('name', suggestion.name || '');
  if (suggestion.name) changedFields.push('name');
  setInputValue('school', suggestion.school || '');
  if (suggestion.school) changedFields.push('school');
  setInputValue('major', suggestion.major || '');
  if (suggestion.major) changedFields.push('major');
  setInputValue('degree', suggestion.degree || '');
  if (suggestion.degree) changedFields.push('degree');
  setInputValue('graduationYear', suggestion.graduation_year || '');
  if (suggestion.graduation_year) changedFields.push('graduationYear');
  setInputValue('manualSkills', (suggestion.manual_skills || []).join(', '));
  if ((suggestion.manual_skills || []).length) changedFields.push('manualSkills');
  setInputValue('projectExperiences', (suggestion.project_experiences || []).join('\n'));
  if ((suggestion.project_experiences || []).length) changedFields.push('projectExperiences');
  setInputValue('internshipExperiences', (suggestion.internship_experiences || []).join('\n'));
  if ((suggestion.internship_experiences || []).length) changedFields.push('internshipExperiences');
  setInputValue('campusExperiences', (suggestion.campus_experiences || []).join('\n'));
  if ((suggestion.campus_experiences || []).length) changedFields.push('campusExperiences');
  setInputValue('certificates', (suggestion.certificates || []).join(', '));
  if ((suggestion.certificates || []).length) changedFields.push('certificates');
  setInputValue('selfDescription', appendSelfDescription(document.getElementById('selfDescription').value, suggestion.self_description || ''));
  if (suggestion.self_description) changedFields.push('selfDescription');

  highlightFields(changedFields);

  if (options.showStatus !== false) {
    const pendingCount = suggestion.pending_prompts?.length || 0;
    setStatus(`已自动回填表单，仍有 ${pendingCount} 项建议用户确认。`, 'success');
  }
}

async function parseResume() {
  const file = els.resumeFile.files?.[0];
  if (!file) {
    setStatus('请先选择一个简历文件。', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);
  setStatus('正在解析简历并生成结构化结果...');
  try {
    const response = await apiFetch('/api/v1/planning/resume/parse', { method: 'POST', body: formData });
    const data = await response.json();
    state.parsedResumeText = data.extracted_text || '';
    state.lastStructuredProfile = data.structured_profile || null;
    state.lastFormFillSuggestion = data.form_fill_suggestion || data.structured_profile?.form_fill_suggestion || null;

    document.getElementById('resumeText').value = state.parsedResumeText;
    setText(els.resumePreview, data.preview || '未提取到文本');
    setText(els.resumeParseMeta, `${data.file_name} · ${data.char_count} 字 · ${data.section_hints?.join(' / ') || '未识别章节'} · ${data.message || '解析完成'}`);
    renderStructuredPreview(state.lastStructuredProfile, state.lastFormFillSuggestion, { fileName: data.file_name, charCount: data.char_count, message: data.message || '' });
    if (state.lastFormFillSuggestion) applyFormFillSuggestion(state.lastFormFillSuggestion, { showStatus: false });
    const pendingCount = state.lastStructuredProfile?.pending_fields?.length || 0;
    setStatus(`简历解析完成，已回填表单；当前有 ${pendingCount} 项待确认。`, 'success');
  } catch (error) {
    setStatus(`简历解析失败：${error.message}`, 'error');
  }
}

function renderFollowUps(questions) {
  if (!els.followUpContainer || !els.questionCount) return;
  if (!questions?.length) {
    setClassName(els.followUpContainer, 'stack-list empty-state');
    setText(els.followUpContainer, '当前没有额外追问，信息已经比较完整。');
    setText(els.questionCount, '0');
    if (els.followUpAnswerHint) els.followUpAnswerHint.classList.add('hidden');
    return;
  }
  const existingAnswers = buildFollowUpAnswerMap(document.getElementById('followUpAnswers')?.value || '');
  setText(els.questionCount, String(questions.length));
  setClassName(els.followUpContainer, 'stack-list');
  setHtml(els.followUpContainer, questions.map((item) => `
    <article class="question-card">
      <h3>P${item.priority} · ${escapeHtml(item.question)}</h3>
      <p>${escapeHtml(item.reason)}</p>
      <label class="followup-answer-field">
        <span>你的回答</span>
        <textarea class="followup-answer-input" data-question="${escapeHtml(item.question)}" rows="2" placeholder="请填写这条追问的回答">${escapeHtml(existingAnswers.get(item.question) || '')}</textarea>
      </label>
    </article>
  `).join(''));
  updateFollowUpAnswerHint();
}

function buildResultNavigatorItems(response) {
  const matches = response?.match_results || [];
  const topMatch = matches[0];
  const softSkills = response?.student_profile?.soft_skill_assessments || [];
  const trendRoleHeat = response?.report?.industry_trend?.role_heat || [];
  const followUps = response?.follow_up_questions || [];
  const evidenceDimensions = topMatch?.evidence_trace?.dimensions || [];
  const graphNodeCount = state.graph?.metadata?.node_count || state.graph?.nodes?.length || 0;
  const graphInsightReady = Boolean(state.graphInsights?.focusJob);

  return [
    {
      key: 'soft-skill',
      title: '软素质画像',
      desc: softSkills.length ? `已生成 ${softSkills.length} 项评分结果` : '等待生成软素质评分',
      badge: softSkills.length ? '可查看' : '待生成',
      ready: softSkills.length > 0,
      targetId: 'softSkillSection',
    },
    {
      key: 'trend',
      title: '行业趋势',
      desc: trendRoleHeat.length ? `已生成 ${trendRoleHeat.length} 组趋势快照` : '等待生成趋势分析',
      badge: trendRoleHeat.length ? '可查看' : '待生成',
      ready: trendRoleHeat.length > 0,
      targetId: 'trendSection',
    },
    {
      key: 'follow-up',
      title: 'Agent 追问',
      desc: followUps.length ? `已生成 ${followUps.length} 个问题` : '等待生成追问',
      badge: followUps.length ? '可查看' : '待生成',
      ready: true,
      targetId: 'followUpSection',
    },
    {
      key: 'match',
      title: '岗位匹配',
      desc: topMatch ? `Top1：${topMatch.job_family}，${topMatch.overall_score} 分` : '等待生成匹配结果',
      badge: topMatch ? '可查看' : '待生成',
      ready: matches.length > 0,
      targetId: 'matchSection',
    },
    {
      key: 'evidence',
      title: 'Evidence Trace',
      desc: evidenceDimensions.length ? `包含 ${evidenceDimensions.length} 个评分维度` : '等待评分证据链',
      badge: evidenceDimensions.length ? '可查看' : '待生成',
      ready: evidenceDimensions.length > 0,
      targetId: 'evidenceSection',
    },
    {
      key: 'graph-insight',
      title: '图谱洞察',
      desc: graphInsightReady ? `聚焦 ${state.graphInsights?.focusJob || '-'} 的个性化图谱分析` : '等待加载图谱洞察',
      badge: graphInsightReady ? '可查看' : '待生成',
      ready: graphInsightReady,
      targetId: 'graphInsightSection',
    },
    {
      key: 'graph',
      title: '岗位图谱',
      desc: graphNodeCount ? `全局图谱节点 ${graphNodeCount}` : '等待图谱加载',
      badge: graphNodeCount ? '可查看' : '待加载',
      ready: graphNodeCount > 0,
      targetId: 'graphSection',
    },
    {
      key: 'report',
      title: '职业报告',
      desc: response?.report?.executive_summary ? '已生成完整职业规划报告' : '等待生成报告',
      badge: response?.report ? '可查看' : '待生成',
      ready: Boolean(response?.report),
      targetId: 'reportSection',
    },
  ];
}

function renderResultNavigator(response) {
  if (!els.resultNavigator || !els.resultNavigatorCount) return;
  if (!response) {
    setClassName(els.resultNavigator, 'result-nav-grid empty-state');
    setText(els.resultNavigator, '先生成职业报告，再从入口卡片跳转查看各部分结果。');
    setText(els.resultNavigatorCount, '0/8');
    return;
  }
  const items = buildResultNavigatorItems(response);
  const readyCount = items.filter((item) => item.ready).length;
  setText(els.resultNavigatorCount, `${readyCount}/${items.length}`);
  setClassName(els.resultNavigator, 'result-nav-grid');
  setHtml(els.resultNavigator, items.map((item) => `
    <button type="button" class="result-entry-btn ${item.ready ? 'ready' : 'pending'}" data-target-id="${escapeHtml(item.targetId)}">
      <div class="result-entry-head">
        <strong>${escapeHtml(item.title)}</strong>
        <span class="badge ${item.ready ? 'confirmed' : 'pending'}">${escapeHtml(item.badge)}</span>
      </div>
      <p>${escapeHtml(item.desc)}</p>
      <span class="result-entry-link">点击进入</span>
    </button>
  `).join(''));
}

function focusSectionById(targetId) {
  const section = document.getElementById(targetId);
  if (!section) return;
  document.querySelectorAll('.section-focus').forEach((element) => element.classList.remove('section-focus'));
  section.classList.add('section-focus');
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  window.setTimeout(() => section.classList.remove('section-focus'), 1800);
}

function softLevelLabel(level) {
  if (level === 'strong') return '优势明显';
  if (level === 'solid') return '表现稳定';
  if (level === 'developing') return '持续成长';
  return '待补强';
}

function renderSoftSkillAssessments(assessments) {
  if (!els.softSkillCount || !els.softSkillOverview) return;
  if (!assessments?.length) {
    setText(els.softSkillCount, '0');
    setClassName(els.softSkillOverview, 'soft-skill-grid empty-state');
    setText(els.softSkillOverview, '暂无软素质评估结果');
    return;
  }
  setText(els.softSkillCount, String(assessments.length));
  setClassName(els.softSkillOverview, 'soft-skill-grid');
  setHtml(els.softSkillOverview, assessments.map((item) => `
    <article class="soft-skill-card">
      <div class="soft-skill-head">
        <div>
          <h3>${escapeHtml(item.skill_name)}</h3>
          <p>${escapeHtml(softLevelLabel(item.level))}</p>
        </div>
        <div class="soft-skill-score">${escapeHtml(item.score)}</div>
      </div>
      <div class="dimension-bar compact"><span style="width: ${Math.max(6, Math.min(Number(item.score) || 0, 100))}%"></span></div>
      <p class="soft-skill-summary">${escapeHtml(item.summary || '暂无能力总结')}</p>
      <div class="soft-skill-indicators">
        ${(item.indicators || []).map((indicator) => `<span class="pill">${escapeHtml(indicator.indicator_name)} ${escapeHtml(indicator.score)}</span>`).join('')}
      </div>
      <div class="soft-skill-footer">
        <span>证据 ${escapeHtml((item.evidence_refs || []).length)}</span>
        <span>${escapeHtml((item.suggestions || [])[0] || '建议继续补充对应经历')}</span>
      </div>
    </article>
  `).join(''));
}

function renderIndustryTrend(trend) {
  if (!els.trendMeta || !els.trendPanel) return;
  if (!trend) {
    setText(els.trendMeta, 'snapshot');
    setClassName(els.trendPanel, 'trend-panel empty-state');
    setText(els.trendPanel, '暂无行业趋势分析');
    return;
  }

  setText(els.trendMeta, `${trend.snapshot_version || 'snapshot'} · ${trend.updated_at || '-'}`);
  setClassName(els.trendPanel, 'trend-panel');
  const roleHeat = trend.role_heat || [];
  const skillTrends = trend.missing_skill_trends || [];
  const shifts = trend.industry_shifts || [];
  const advice = trend.personalized_advice || [];

  setHtml(els.trendPanel, `
    <section class="trend-block">
      <div class="section-head minor">
        <h3>岗位冷热度</h3>
      </div>
      <div class="trend-card-grid">
        ${roleHeat.map((item) => `
          <article class="trend-card">
            <div class="trend-card-head">
              <strong>${escapeHtml(item.job_family)}</strong>
              <span class="badge confirmed">${escapeHtml(item.heat_score)} · ${escapeHtml(item.heat_level)}</span>
            </div>
            <p>${escapeHtml(item.summary || '')}</p>
            <div class="trend-metric-list">
              ${(item.metrics || []).map((metric) => `<span class="pill">${escapeHtml(metric.metric_name)} ${escapeHtml(metric.display_value || metric.score)}</span>`).join('')}
            </div>
          </article>
        `).join('') || '<div class="empty-inline">暂无岗位热度数据</div>'}
      </div>
    </section>
    <section class="trend-block">
      <div class="section-head minor">
        <h3>缺口技能热度</h3>
      </div>
      <div class="trend-card-grid">
        ${skillTrends.map((item) => `
          <article class="trend-card emphasis">
            <div class="trend-card-head">
              <strong>${escapeHtml(item.skill_name)}</strong>
              <span class="badge pending">${escapeHtml(item.heat_score)} · ${escapeHtml(item.heat_level)}</span>
            </div>
            <p>${escapeHtml(item.summary || '')}</p>
            <div class="trend-metric-list">
              ${(item.metrics || []).map((metric) => `<span class="pill">${escapeHtml(metric.metric_name)} ${escapeHtml(metric.display_value || metric.score)}</span>`).join('')}
            </div>
            <div class="structured-subtext">${escapeHtml(item.suggestion || '')}</div>
          </article>
        `).join('') || '<div class="empty-inline">暂无缺口技能趋势数据</div>'}
      </div>
    </section>
    <section class="trend-block">
      <div class="section-head minor">
        <h3>行业变化</h3>
      </div>
      <div class="stack-list">
        ${shifts.map((item) => `
          <article class="trend-shift-card">
            <div class="trend-card-head">
              <strong>${escapeHtml(item.topic)}</strong>
              <span class="badge confirmed">${escapeHtml(item.impact_level)}</span>
            </div>
            <p>${escapeHtml(item.summary || '')}</p>
            ${(item.opportunities || []).length ? `<div class="structured-subtext">机会：${escapeHtml(item.opportunities.join('；'))}</div>` : ''}
            ${(item.risks || []).length ? `<div class="structured-subtext">风险：${escapeHtml(item.risks.join('；'))}</div>` : ''}
          </article>
        `).join('') || '<div class="empty-inline">暂无行业变化信号</div>'}
      </div>
    </section>
    <section class="trend-block">
      <div class="section-head minor">
        <h3>未来 3 年建议</h3>
      </div>
      <div class="stack-list">
        ${advice.map((item) => `<article class="advice-card">${escapeHtml(item)}</article>`).join('') || '<div class="empty-inline">暂无个性化趋势建议</div>'}
      </div>
    </section>
  `);
}

function formatRatioPercent(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return '-';
  return `${Math.round(num * 1000) / 10}%`;
}

function renderGraphInsights(insights) {
  if (!els.graphInsightMeta || !els.graphInsightPanel) return;
  if (!insights) {
    setText(els.graphInsightMeta, 'pending');
    setClassName(els.graphInsightPanel, 'trend-panel empty-state');
    setText(els.graphInsightPanel, '生成报告后，这里会展示图谱洞察。');
    return;
  }

  const relatedJobs = insights.relatedJobs || [];
  const entryPoints = insights.entryPoints || [];
  const ranking = insights.influenceRanking || [];
  const clusterMembers = insights.clusterMembers || [];

  setText(els.graphInsightMeta, `${insights.focusJob || '-'} | ${insights.targetJob || '-'}`);
  setClassName(els.graphInsightPanel, 'trend-panel');
  setHtml(els.graphInsightPanel, `
    <section class="trend-block">
      <div class="section-head minor">
        <h3>相关岗位推荐</h3>
      </div>
      <div class="trend-card-grid">
        ${relatedJobs.map((item) => `
          <article class="trend-card">
            <div class="trend-card-head">
              <strong>${escapeHtml(item.job_family)}</strong>
              <span class="badge confirmed">样本 ${escapeHtml(item.sample_count || 0)}</span>
            </div>
            <p>${escapeHtml(item.description || '暂无岗位说明')}</p>
            <div class="trend-metric-list">
              ${(item.required_skills || []).slice(0, 4).map((skill) => `<span class="pill">${escapeHtml(skill)}</span>`).join('') || '<span class="pill">暂无技能标签</span>'}
            </div>
            ${(item.evidence_snippets || []).length ? `<div class="structured-subtext">${escapeHtml(item.evidence_snippets.slice(0, 2).join(' / '))}</div>` : ''}
          </article>
        `).join('') || '<div class="empty-inline">暂无相关岗位推荐</div>'}
      </div>
    </section>
    <section class="trend-block">
      <div class="section-head minor">
        <h3>目标岗位常见入口</h3>
      </div>
      <div class="stack-list">
        ${entryPoints.map((item) => `
          <article class="trend-shift-card">
            <div class="trend-card-head">
              <strong>${escapeHtml((item.jobs || []).join(' -> ') || '未找到路径')}</strong>
              <span class="badge ${item.is_feasible ? 'confirmed' : 'pending'}">${escapeHtml(formatRatioPercent(item.cumulative_success_rate || 0))}</span>
            </div>
            <p>共 ${escapeHtml(item.steps)} 步 / 预计 ${escapeHtml(item.estimated_time_cost || '-')} / 难度 ${escapeHtml(item.difficulty || '-')}</p>
            ${(item.missing_skills || []).length ? `<div class="structured-subtext">待补技能：${escapeHtml(item.missing_skills.join(', '))}</div>` : '<div class="structured-subtext">当前技能已覆盖这条路径的关键要求</div>'}
          </article>
        `).join('') || '<div class="empty-inline">暂无常见入口路径</div>'}
      </div>
    </section>
    <section class="trend-block">
      <div class="section-head minor">
        <h3>岗位影响力</h3>
      </div>
      <div class="stack-list">
        ${ranking.map((item, index) => `
          <article class="advice-card${item.job === insights.focusJob ? ' emphasis' : ''}">${index + 1}. ${escapeHtml(item.job)} / 影响力 ${escapeHtml(item.influence_score)}</article>
        `).join('') || '<div class="empty-inline">暂无影响力数据</div>'}
      </div>
    </section>
    <section class="trend-block">
      <div class="section-head minor">
        <h3>岗位聚类</h3>
      </div>
      <div class="trend-metric-list">
        ${clusterMembers.map((item) => `<span class="pill">${escapeHtml(item)}</span>`).join('') || '<span class="pill">暂无聚类结果</span>'}
      </div>
    </section>
  `);
}

async function loadGraphInsights(response) {
  const topMatch = response?.match_results?.[0];
  if (!topMatch) {
    state.graphInsights = null;
    renderGraphInsights(null);
    return;
  }

  const primaryPath = getPrimaryPathOption(response);
  const focusJob = topMatch.job_family;
  const targetJob = primaryPath?.target_role || focusJob;
  const tasks = {
    relatedJobs: apiFetch('/api/v1/planning/graph/related-jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job: focusJob, limit: 4 }),
    }).then((res) => res.json()),
    entryPoints: apiFetch('/api/v1/planning/graph/entry-points', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_job: targetJob, max_steps: 4 }),
    }).then((res) => res.json()),
    influencePayload: apiFetch('/api/v1/planning/graph/job-influence').then((res) => res.json()),
    clusters: apiFetch('/api/v1/planning/graph/job-clusters').then((res) => res.json()),
  };

  const settled = await Promise.allSettled(Object.values(tasks));
  const keys = Object.keys(tasks);
  const payload = {
    relatedJobs: [],
    entryPoints: [],
    influencePayload: { ranking: [] },
    clusters: {},
  };

  settled.forEach((result, index) => {
    const key = keys[index];
    if (result.status === 'fulfilled') {
      payload[key] = result.value;
      return;
    }
    console.warn(`Failed to load graph insight segment: ${key}`, result.reason);
  });

  const clusterMembers = Object.values(payload.clusters || {}).find((items) => Array.isArray(items) && items.includes(focusJob)) || [];
  state.graphInsights = {
    focusJob,
    targetJob,
    relatedJobs: payload.relatedJobs || [],
    entryPoints: (payload.entryPoints || []).slice(0, 3),
    influenceRanking: (payload.influencePayload?.ranking || []).slice(0, 5),
    clusterMembers,
  };
  renderGraphInsights(state.graphInsights);
}

function renderMatches(matches) {
  if (!els.matchContainer) return;
  if (!matches?.length) {
    setClassName(els.matchContainer, 'stack-list empty-state');
    setText(els.matchContainer, '暂无匹配结果');
    return;
  }
  if (state.selectedMatchIndex >= matches.length) state.selectedMatchIndex = 0;
  setClassName(els.matchContainer, 'stack-list');
  setHtml(els.matchContainer, matches.map((item, index) => `
    <article class="match-card ${index === state.selectedMatchIndex ? 'active' : ''}">
      <span class="match-score">匹配度 ${escapeHtml(item.overall_score)}</span>
      <h3>${escapeHtml(item.job_family)}</h3>
      <p>${escapeHtml(item.summary)}</p>
      <div class="skill-pills">
        ${(item.matched_skills || []).slice(0, 4).map((skill) => `<span class="pill">${escapeHtml(skill)}</span>`).join('')}
        ${(item.missing_skills || []).slice(0, 3).map((skill) => `<span class="pill warn">缺 ${escapeHtml(skill)}</span>`).join('')}
      </div>
      <div class="match-actions"><button class="ghost-btn evidence-btn" data-match-index="${index}">查看证据</button></div>
    </article>
  `).join(''));
}

function markdownToHtml(markdown) {
  const lines = String(markdown || '').split(/\r?\n/);
  const chunks = [];
  let inList = false;
  const closeList = () => { if (inList) { chunks.push('</ul>'); inList = false; } };

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      closeList();
      return;
    }
    if (trimmed.startsWith('### ')) { closeList(); chunks.push(`<h3>${escapeHtml(trimmed.slice(4))}</h3>`); return; }
    if (trimmed.startsWith('## ')) { closeList(); chunks.push(`<h2>${escapeHtml(trimmed.slice(3))}</h2>`); return; }
    if (trimmed.startsWith('# ')) { closeList(); chunks.push(`<h1>${escapeHtml(trimmed.slice(2))}</h1>`); return; }
    if (trimmed.startsWith('- ')) {
      if (!inList) { chunks.push('<ul>'); inList = true; }
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
  if (!els.executiveSummary || !els.reportPreview || !els.reportModeBadge) return;
  if (!report) {
    setText(els.executiveSummary, '请先生成职业报告');
    setClassName(els.reportPreview, 'report-preview empty-state');
    setText(els.reportPreview, '报告预览将在这里显示');
    return;
  }
  setText(els.executiveSummary, report.executive_summary || report.overview || '暂无摘要');
  setText(els.reportModeBadge, report.generation_mode || 'template');
  setClassName(els.reportPreview, 'report-preview');
  setHtml(els.reportPreview, markdownToHtml(report.report_markdown));
}
function renderEvidenceTrace(match) {
  if (!els.evidenceMatchName || !els.evidenceEmpty || !els.evidenceTracePanel) return;
  const trace = match?.evidence_trace;
  if (!trace) {
    setText(els.evidenceMatchName, 'No match selected');
    els.evidenceEmpty.classList.remove('hidden');
    els.evidenceTracePanel.classList.add('hidden');
    setHtml(els.evidenceDimensionList, '');
    setHtml(els.evidenceRawList, '');
    setText(els.evidenceRawCount, '0');
    return;
  }

  setText(els.evidenceMatchName, match.job_family || 'Untitled match');
  setText(els.evidenceScore, `${trace.final_score?.display_score ?? '-'} pts`);
  setText(els.evidenceFormula, trace.final_score?.formula || '-');
  setText(els.evidenceRuleVersion, trace.versions?.score_rule_version || '-');
  setText(els.evidenceKbVersion, trace.versions?.knowledge_base_version || '-');
  els.evidenceEmpty.classList.add('hidden');
  els.evidenceTracePanel.classList.remove('hidden');

  const dimensions = trace.dimensions || [];
  setHtml(els.evidenceDimensionList, dimensions.map((dimension) => `
    <article class="dimension-trace-card">
      <div class="dimension-trace-head">
        <div>
          <h3>${escapeHtml(dimension.name || dimension.dimension_name || '未命名维度')}</h3>
          <p>${escapeHtml(dimension.formula || 'n/a')}</p>
        </div>
        <div class="dimension-score-box">
          <strong>${escapeHtml(dimension.score)}</strong>
          <span>贡献 ${escapeHtml(dimension.weighted_score)}</span>
        </div>
      </div>
      <div class="dimension-bar"><span style="width: ${Math.max(6, Math.min(Number(dimension.score) || 0, 100))}%"></span></div>
      <div class="indicator-trace-list">
        ${(dimension.indicators || []).map((indicator) => `
          <section class="indicator-card">
            <div class="indicator-topline"><strong>${escapeHtml(indicator.indicator_name)}</strong><span>${escapeHtml(indicator.score)} x ${escapeHtml(indicator.weight_in_dimension)} = ${escapeHtml(indicator.weighted_score)}</span></div>
            <p class="indicator-formula">规则：${escapeHtml(indicator.formula || indicator.rule_id || 'n/a')}</p>
            <p class="indicator-raw">原始值：${escapeHtml(formatValue(indicator.raw_value))}</p>
            ${(indicator.deductions || []).length ? `<div class="deduction-list">${indicator.deductions.map((item) => `<span class="pill warn">${escapeHtml(item.reason)} (${escapeHtml(item.delta)})</span>`).join('')}</div>` : ''}
            ${(indicator.evidence_refs || []).length ? `<div class="evidence-ref-list">${indicator.evidence_refs.map((item) => `<span class="pill ref">${escapeHtml(item)}</span>`).join('')}</div>` : ''}
          </section>
        `).join('')}
      </div>
      <div class="dimension-evidence-list">
        ${(dimension.evidences || []).map((item) => `
          <article class="evidence-card-mini">
            <div class="evidence-meta"><span class="badge">${escapeHtml(item.evidence_id || '-')}</span><span>${escapeHtml(item.source_type || item.source || '-')}</span></div>
            <p>${escapeHtml(item.excerpt || '')}</p>
          </article>
        `).join('') || '<div class="empty-inline">当前维度没有挂载原始证据。</div>'}
      </div>
    </article>
  `).join(''));

  const evidences = trace.evidences || [];
  setText(els.evidenceRawCount, String(evidences.length));
  setHtml(els.evidenceRawList, evidences.map((item) => `
    <article class="evidence-raw-card">
      <div class="evidence-meta"><span class="badge">${escapeHtml(item.evidence_id || '-')}</span><span>${escapeHtml(item.source_type || item.source || '-')}</span><span>${escapeHtml(item.source_ref || '-')}</span></div>
      <p>${escapeHtml(item.excerpt || '')}</p>
      <div class="evidence-footer"><span>confidence: ${escapeHtml(item.confidence ?? '-')}</span><span>rule: ${escapeHtml(item.extract_rule || '-')}</span></div>
    </article>
  `).join(''));
}

function polarPosition(cx, cy, radius, angle) {
  return { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius };
}

function createSvgElement(tag) {
  return document.createElementNS('http://www.w3.org/2000/svg', tag);
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

function normalizeVector(dx, dy) {
  const length = Math.hypot(dx, dy) || 1;
  return { x: dx / length, y: dy / length };
}

function estimateLabelBox(lines, fontSize) {
  const maxLength = Math.max(...lines.map((line) => line.length), 1);
  return {
    width: maxLength * fontSize * 0.68 + 18,
    height: lines.length * (fontSize + 4) + 10,
  };
}

function formatMoneyRange(min, max) {
  const minValue = Number(min);
  const maxValue = Number(max);
  const hasMin = Number.isFinite(minValue) && min !== null && min !== '';
  const hasMax = Number.isFinite(maxValue) && max !== null && max !== '';
  if (!hasMin && !hasMax) return '-';
  if (hasMin && hasMax) return `${minValue} - ${maxValue} / 月`;
  if (hasMin) return `${minValue}+ / 月`;
  return `<= ${maxValue} / 月`;
}

function renderPillCollection(values, emptyText = '暂无数据') {
  if (!values?.length) {
    return `<span class="empty-inline">${escapeHtml(emptyText)}</span>`;
  }
  return values.map((item) => `<span class="pill">${escapeHtml(item)}</span>`).join('');
}

function renderJumpPills(values, options = {}) {
  const { emptyText = '暂无数据', nodeType = 'job_family', activeId = '' } = options;
  if (!values?.length) {
    return `<span class="empty-inline">${escapeHtml(emptyText)}</span>`;
  }
  return values.map((item) => {
    const value = typeof item === 'string' ? item : (item?.id || item?.label || item?.target_id || '');
    const label = typeof item === 'string' ? item : (item?.label || item?.id || item?.target_id || '');
    const activeClass = value === activeId ? ' is-active' : '';
    return `<button type="button" class="graph-jump-btn${activeClass}" data-graph-jump="${escapeHtml(value)}" data-node-type="${escapeHtml(nodeType)}">${escapeHtml(label)}</button>`;
  }).join('');
}

function renderRelationCards(items, emptyText) {
  if (!items?.length) {
    return `<div class="empty-inline">${escapeHtml(emptyText)}</div>`;
  }
  return items.map((item) => `
    <article class="graph-relation-card">
      <div class="trend-card-head">
        <strong>${escapeHtml(item.label || item.target_id || '-')}</strong>
        <span class="badge confirmed">${escapeHtml(item.relation_type || '-')}</span>
      </div>
      <p>成功率 ${escapeHtml(formatRatioPercent(item.success_rate || 0))} / 时间 ${escapeHtml(item.time_cost || '-')} / 难度 ${escapeHtml(item.difficulty || '-')}</p>
      ${(item.required_skills || []).length ? `<div class="structured-subtext">所需技能：${escapeHtml(item.required_skills.join(' / '))}</div>` : ''}
      ${(item.evidence || []).length ? `<div class="structured-subtext">证据：${escapeHtml(item.evidence.join(' / '))}</div>` : ''}
    </article>
  `).join('');
}

function renderPathCards(paths, emptyText) {
  if (!paths?.length) {
    return `<div class="empty-inline">${escapeHtml(emptyText)}</div>`;
  }
  return paths.map((pathJobs) => `
    <article class="graph-path-card">
      <strong>${escapeHtml((pathJobs || []).join(' -> '))}</strong>
    </article>
  `).join('');
}

function renderGraphDetailPlaceholder(
  message = '点击图谱中的节点或连线，查看岗位基础信息、城市分布、技能要求和转岗证据。',
  meta = 'idle',
) {
  if (!els.graphDetailMeta || !els.graphDetailBody) return;
  setText(els.graphDetailMeta, meta);
  setClassName(els.graphDetailBody, 'graph-detail-body empty-state');
  setText(els.graphDetailBody, message);
}

function renderGraphEdgeDetail(edge) {
  if (!els.graphDetailMeta || !els.graphDetailBody) return;
  setText(els.graphDetailMeta, '连线详情');
  setClassName(els.graphDetailBody, 'graph-detail-body');
  setHtml(els.graphDetailBody, `
    <article class="graph-detail-card">
      <div class="graph-detail-head">
        <div>
          <h3>${escapeHtml(edge.source)} -> ${escapeHtml(edge.target)}</h3>
          <p>${escapeHtml(edge.reason || '转岗或成长关系的图谱连线。')}</p>
        </div>
        <span class="badge confirmed">${escapeHtml(edge.edge_type || '-')}</span>
      </div>
      <div class="graph-meta-pills">
        <div class="graph-meta-pill">成功率<br /><strong>${escapeHtml(formatRatioPercent(edge.success_rate || 0))}</strong></div>
        <div class="graph-meta-pill">时间成本<br /><strong>${escapeHtml(edge.time_cost || '-')}</strong></div>
        <div class="graph-meta-pill">难度<br /><strong>${escapeHtml(edge.difficulty || '-')}</strong></div>
        <div class="graph-meta-pill">Case Count<br /><strong>${escapeHtml(edge.case_count || 0)}</strong></div>
      </div>
      <div class="graph-detail-section">
        <strong>所需技能</strong>
        <div class="trend-metric-list">${renderPillCollection(edge.required_skills, '暂无标注')}</div>
      </div>
      <div class="graph-detail-section">
        <strong>待补技能</strong>
        <div class="trend-metric-list">${renderPillCollection(edge.missing_skills, '当前未标注')}</div>
      </div>
      <div class="graph-detail-section">
        <strong>证据来源</strong>
        <div class="trend-metric-list">${renderPillCollection(edge.evidence, '暂无证据')}</div>
      </div>
    </article>
  `);
}

function renderGraphEntityDetail(detail, fallbackNode) {
  if (!els.graphDetailMeta || !els.graphDetailBody) return;
  const nodeType = String(detail?.node_type || fallbackNode?.node_type || 'job_family');
  const typeLabelMap = {
    job_family: '岗位节点',
    skill: '技能节点',
    ability: '能力节点',
  };
  const title = detail?.label || fallbackNode?.label || detail?.entity_id || '-';
  const description = detail?.description || fallbackNode?.description || '暂无详细说明';
  const cities = uniqueList([...(detail?.cities || []), ...(detail?.top_cities || [])]);
  const industries = uniqueList([...(detail?.industries || []), ...(detail?.top_industries || [])]);
  const topSkills = uniqueList([...(detail?.top_skills || []), ...(detail?.required_skills || [])]);
  const jumpJobs = uniqueList([...(detail?.recommended_jobs || []), ...(detail?.linked_jobs || [])]);

  setText(els.graphDetailMeta, typeLabelMap[nodeType] || nodeType);
  setClassName(els.graphDetailBody, 'graph-detail-body');
  setHtml(els.graphDetailBody, `
    <article class="graph-detail-card">
      <div class="graph-detail-head">
        <div>
          <h3>${escapeHtml(title)}</h3>
          <p>${escapeHtml(description)}</p>
        </div>
        <span class="badge confirmed">${escapeHtml(nodeType)}</span>
      </div>
      <div class="graph-meta-pills">
        <div class="graph-meta-pill">样本量<br /><strong>${escapeHtml(detail?.sample_count || fallbackNode?.sample_count || 0)}</strong></div>
        <div class="graph-meta-pill">影响力<br /><strong>${escapeHtml(detail?.influence_score || 0)}</strong></div>
        <div class="graph-meta-pill">薪资区间<br /><strong>${escapeHtml(formatMoneyRange(detail?.salary_min_monthly, detail?.salary_max_monthly))}</strong></div>
        <div class="graph-meta-pill">市场需求<br /><strong>${escapeHtml(detail?.market_demand || '-')}</strong></div>
      </div>
      <div class="graph-detail-section">
        <strong>高频技能</strong>
        <div class="trend-metric-list">${renderPillCollection(topSkills, '暂无技能标签')}</div>
      </div>
      <div class="graph-detail-section">
        <strong>核心要求</strong>
        <div class="trend-metric-list">${renderPillCollection(detail?.required_skills, '??')}</div>
      </div>
      <div class="graph-detail-section">
        <strong>加分项</strong>
        <div class="trend-metric-list">${renderPillCollection(detail?.bonus_skills, '??')}</div>
      </div>
      <div class="graph-detail-section">
        <strong>软素质 / 证书</strong>
        <div class="trend-metric-list">${renderPillCollection(uniqueList([...(detail?.soft_skills || []), ...(detail?.certificates || [])]), '??')}</div>
      </div>
      <div class="graph-detail-section">
        <strong>城市与行业</strong>
        <div class="trend-metric-list">${renderPillCollection(uniqueList([...cities, ...industries]), '暂无区域或行业标签')}</div>
      </div>
      <div class="graph-detail-section">
        <strong>岗位推荐 / 一键跳转</strong>
        <div class="graph-jump-list">${renderJumpPills(jumpJobs, { emptyText: '暂无可跳转岗位', activeId: state.selectedGraphNodeId })}</div>
      </div>
      <div class="graph-detail-section">
        <strong>纵向成长路径</strong>
        <div class="graph-jump-list">${renderJumpPills(detail?.vertical_growth_path, { emptyText: '??', activeId: state.selectedGraphNodeId })}</div>
      </div>
      <div class="graph-detail-section">
        <strong>横向转岗方向</strong>
        <div class="graph-jump-list">${renderJumpPills(detail?.transfer_paths, { emptyText: '??', activeId: state.selectedGraphNodeId })}</div>
      </div>
      <div class="graph-detail-section">
        <strong>常见入口路径</strong>
        <div class="graph-path-list">${(detail?.entry_paths || []).length ? (detail.entry_paths || []).map((pathJobs) => `
          <article class="graph-path-card">
            <strong>${escapeHtml((pathJobs || []).join(' -> '))}</strong>
            <div class="graph-jump-list">${renderJumpPills(pathJobs || [], { emptyText: '暂无路径节点', activeId: state.selectedGraphNodeId })}</div>
          </article>
        `).join('') : '<div class="empty-inline">暂无入口路径</div>'}</div>
      </div>
      <div class="graph-detail-section">
        <strong>证据摘要</strong>
        <div class="graph-path-list">${(detail?.evidence_snippets || []).length ? (detail.evidence_snippets || []).map((item) => `<article class="graph-path-card">${escapeHtml(item)}</article>`).join('') : '<div class="empty-inline">暂无额外证据摘要</div>'}</div>
      </div>
    </article>
    <section class="graph-detail-section">
      <strong>上游路径 / 入口岗位</strong>
      <div class="graph-relation-list">${renderRelationCards(detail?.incoming_relations, '暂无上游关系')}</div>
    </section>
    <section class="graph-detail-section">
      <strong>下游路径 / 可去岗位</strong>
      <div class="graph-relation-list">${renderRelationCards(detail?.outgoing_relations, '暂无下游关系')}</div>
    </section>
  `);
}

async function loadGraphEntityDetail(node) {
  if (!node || !els.graphDetailMeta || !els.graphDetailBody) return;
  const entityId = node.node_type === 'skill' && String(node.id || '').startsWith('skill::') ? node.label : node.id;
  const cacheKey = `${node.node_type}:${entityId}`;
  if (state.graphDetailCache.has(cacheKey)) {
    renderGraphEntityDetail(state.graphDetailCache.get(cacheKey), node);
    return;
  }

  renderGraphDetailPlaceholder('正在加载节点详情...', 'loading');
  try {
    const response = await apiFetch('/api/v1/planning/graph/entity-detail', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_id: entityId, node_type: node.node_type || 'job_family' }),
    });
    const payload = await response.json();
    state.graphDetailCache.set(cacheKey, payload);
    renderGraphEntityDetail(payload, node);
  } catch (error) {
    renderGraphDetailPlaceholder(`节点详情加载失败：${error.message}`, 'error');
  }
}

function appendGraphNodeLabel(group, node, pos, radius, centerX, centerY) {
  const lines = breakLabel(node.label, node.node_type === 'job_family' ? 6 : 5);
  const fontSize = node.node_type === 'job_family' ? 13 : 11;
  const lineHeight = fontSize + 3;
  const vector = normalizeVector(pos.x - centerX, pos.y - centerY);
  const anchor = Math.abs(vector.x) < 0.25 ? 'middle' : (vector.x > 0 ? 'start' : 'end');
  const labelOffset = radius + (node.node_type === 'job_family' ? 22 : 18);
  const labelX = pos.x + vector.x * labelOffset;
  const labelY = pos.y + vector.y * labelOffset;
  const box = estimateLabelBox(lines, fontSize);

  const text = createSvgElement('text');
  text.setAttribute('class', 'graph-node-label');
  text.setAttribute('text-anchor', anchor);
  text.setAttribute('font-size', String(fontSize));
  const startY = labelY - ((lines.length - 1) * lineHeight) / 2;
  lines.forEach((lineText, index) => {
    const tspan = createSvgElement('tspan');
    tspan.setAttribute('x', String(labelX));
    tspan.setAttribute('y', String(startY + index * lineHeight));
    tspan.textContent = lineText;
    text.appendChild(tspan);
  });
  group.appendChild(text);

  let rectX = labelX - box.width / 2;
  if (anchor === 'start') rectX = labelX - 8;
  if (anchor === 'end') rectX = labelX - box.width + 8;
  const rect = createSvgElement('rect');
  rect.setAttribute('class', 'graph-label-bg');
  rect.setAttribute('x', String(rectX));
  rect.setAttribute('y', String(labelY - box.height / 2));
  rect.setAttribute('rx', '12');
  rect.setAttribute('ry', '12');
  rect.setAttribute('width', String(box.width));
  rect.setAttribute('height', String(box.height));
  group.insertBefore(rect, text);
}

function getActiveGraphSource() {
  if (state.graphMode === 'personal' && state.personalizedGraph) return state.personalizedGraph;
  return state.graph;
}

function getGraphNodeById(graph, nodeId) {
  if (!graph?.nodes?.length) return null;
  return graph.nodes.find((node) => node.id === nodeId || node.label === nodeId || node.id === `skill::${nodeId}`) || null;
}

function findFirstMatchingGraphNode(graph, searchText) {
  const query = String(searchText || '').trim().toLowerCase();
  if (!query || !graph?.nodes?.length) return null;
  return graph.nodes.find((node) => (
    matchesGraphSearch(node, query)
    && matchesGraphJobFilters(node, state.graphCity, state.graphIndustry)
    && (node.node_type === 'job_family' || node.node_type === 'skill')
  )) || null;
}

function matchesGraphSearch(node, query) {
  const normalized = String(query || '').trim().toLowerCase();
  if (!normalized) return true;
  const haystack = [
    node.id,
    node.label,
    node.description,
    ...(node.top_skills || []),
    ...(node.top_cities || []),
    ...(node.top_industries || []),
    ...(node.badges || []),
  ].join(' ').toLowerCase();
  return haystack.includes(normalized);
}

function matchesGraphJobFilters(node, city, industry) {
  if (node.node_type !== 'job_family') return true;
  if (city && !(node.top_cities || []).includes(city)) return false;
  if (industry && !(node.top_industries || []).includes(industry)) return false;
  return true;
}

function buildGraphView(graph) {
  if (!graph) return null;
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  const searchText = String(state.graphSearch || '').trim().toLowerCase();
  const hasSearch = Boolean(searchText);
  const hasJobFilter = Boolean(state.graphCity || state.graphIndustry);
  const matchedIds = new Set();

  if (hasSearch || hasJobFilter) {
    nodes.forEach((node) => {
      if (!matchesGraphJobFilters(node, state.graphCity, state.graphIndustry)) return;
      if (!matchesGraphSearch(node, searchText)) return;
      matchedIds.add(node.id);
    });
  } else {
    nodes.forEach((node) => matchedIds.add(node.id));
  }

  let visibleNodeIds = new Set();
  if (!hasSearch && !hasJobFilter) {
    nodes.forEach((node) => visibleNodeIds.add(node.id));
  } else {
    matchedIds.forEach((id) => visibleNodeIds.add(id));
    edges.forEach((edge) => {
      if (matchedIds.has(edge.source) || matchedIds.has(edge.target)) {
        visibleNodeIds.add(edge.source);
        visibleNodeIds.add(edge.target);
      }
    });
  }

  let visibleNodes = nodes.filter((node) => visibleNodeIds.has(node.id));
  let visibleEdges = edges.filter((edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target));

  if (state.graphNeighborOnly && state.selectedGraphNodeId) {
    const focusId = state.selectedGraphNodeId;
    const oneHopNodeIds = new Set([focusId]);
    visibleEdges.forEach((edge) => {
      if (edge.source === focusId) oneHopNodeIds.add(edge.target);
      if (edge.target === focusId) oneHopNodeIds.add(edge.source);
    });
    visibleNodes = visibleNodes.filter((node) => oneHopNodeIds.has(node.id));
    visibleEdges = visibleEdges.filter((edge) => oneHopNodeIds.has(edge.source) && oneHopNodeIds.has(edge.target));
  }

  return {
    ...graph,
    nodes: visibleNodes,
    edges: visibleEdges,
    metadata: {
      ...(graph.metadata || {}),
      source_mode: state.graphMode,
      filtered_node_count: visibleNodes.length,
      filtered_edge_count: visibleEdges.length,
    },
  };
}

function fillGraphSelectOptions(element, values, placeholder, currentValue) {
  if (!element) return;
  const options = [`<option value="">${escapeHtml(placeholder)}</option>`]
    .concat(values.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`));
  setHtml(element, options.join(''));
  element.value = values.includes(currentValue) ? currentValue : '';
}

function populateGraphFilterOptions(graph) {
  const jobNodes = (graph?.nodes || []).filter((node) => node.node_type === 'job_family');
  const cities = uniqueList(jobNodes.flatMap((node) => node.top_cities || []));
  const industries = uniqueList(jobNodes.flatMap((node) => node.top_industries || []));
  fillGraphSelectOptions(els.graphCityFilter, cities, '全部城市', state.graphCity);
  fillGraphSelectOptions(els.graphIndustryFilter, industries, '全部行业', state.graphIndustry);
  state.graphCity = els.graphCityFilter?.value || '';
  state.graphIndustry = els.graphIndustryFilter?.value || '';
}

function syncGraphToolbar(viewGraph) {
  if (els.graphSearchInput && els.graphSearchInput.value !== state.graphSearch) {
    els.graphSearchInput.value = state.graphSearch;
  }
  if (els.graphNeighborBtn) {
    els.graphNeighborBtn.disabled = !state.selectedGraphNodeId;
    els.graphNeighborBtn.classList.toggle('active', Boolean(state.graphNeighborOnly && state.selectedGraphNodeId));
    els.graphNeighborBtn.textContent = state.graphNeighborOnly ? '退出一阶邻居' : '一阶邻居';
  }
  if (els.graphToolbarHint) {
    const modeLabel = state.graphMode === 'personal' ? '当前为个性化子图' : '当前为全局图谱';
    const focusLabel = state.selectedGraphNodeId ? ` · 已选中 ${state.selectedGraphNodeId}` : '';
    const filterParts = [state.graphSearch && `搜索：${state.graphSearch}`, state.graphCity && `城市：${state.graphCity}`, state.graphIndustry && `行业：${state.graphIndustry}`].filter(Boolean);
    const filterLabel = filterParts.length ? ` ? ${filterParts.join(' / ')}` : '';
    const countLabel = viewGraph ? ` · 显示 ${viewGraph.nodes.length} 个节点 / ${viewGraph.edges.length} 条关系` : '';
    setText(els.graphToolbarHint, `${modeLabel}${focusLabel}${filterLabel}${countLabel}`);
  }
}

function applyGraphView(options = {}) {
  const sourceGraph = getActiveGraphSource();
  if (!sourceGraph) return;
  populateGraphFilterOptions(sourceGraph);
  const viewGraph = buildGraphView(sourceGraph);
  state.renderedGraph = viewGraph;
  renderGraph(viewGraph, options);
  syncGraphToolbar(viewGraph);
}

async function focusGraphNode(nodeId, options = {}) {
  const { resetFilters = false, showStatus = true } = options;
  if (!nodeId) return;

  let sourceGraph = getActiveGraphSource();
  let node = getGraphNodeById(sourceGraph, nodeId);
  if (!node && state.graph) {
    node = getGraphNodeById(state.graph, nodeId);
    if (node) {
      state.graphMode = 'global';
      sourceGraph = state.graph;
      updateGraphMode(false);
    }
  }
  if (!node) {
    setStatus(`图谱中未找到节点：${nodeId}`, 'error');
    return;
  }

  if (resetFilters) {
    state.graphSearch = '';
    state.graphCity = '';
    state.graphIndustry = '';
  }
  state.selectedGraphNodeId = node.id;
  state.graphNeighborOnly = true;
  applyGraphView({ resetDetail: false });
  await loadGraphEntityDetail(node);
  if (showStatus) {
    setStatus(`已聚焦节点：${node.label}`, 'success');
  }
}

function renderGraph(graph, options = {}) {
  if (!graph) return;
  const svg = els.graphSvg;
  if (!svg) return;
  svg.innerHTML = '';
  svg.setAttribute('viewBox', '0 0 1320 760');
  const width = 1320;
  const height = 760;
  const centerX = width / 2;
  const centerY = height / 2;

  if (!graph.nodes?.length) {
    const empty = createSvgElement('text');
    empty.setAttribute('x', String(centerX));
    empty.setAttribute('y', String(centerY));
    empty.setAttribute('text-anchor', 'middle');
    empty.setAttribute('fill', '#6a6d73');
    empty.setAttribute('font-size', '18');
    empty.textContent = '当前筛选条件下没有可展示的图谱节点';
    svg.appendChild(empty);
    setText(els.heroGraphNodes, '0');
    if (options.resetDetail !== false) renderGraphDetailPlaceholder('当前筛选条件下没有可展示的节点，请调整搜索或筛选条件。', 'empty');
    return;
  }

  const jobNodes = graph.nodes.filter((node) => node.node_type === 'job_family');
  const stageNodes = graph.nodes.filter((node) => node.node_type !== 'job_family');
  const positionMap = new Map();
  const jobRingRadius = Math.min(250, 190 + jobNodes.length * 5);
  const outerRingRadius = Math.min(360, 285 + stageNodes.length * 2);

  jobNodes.forEach((node, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(jobNodes.length, 1) - Math.PI / 2;
    positionMap.set(node.id, polarPosition(centerX, centerY, jobRingRadius, angle));
  });
  stageNodes.forEach((node, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(stageNodes.length, 1) - Math.PI / 2 + 0.12;
    positionMap.set(node.id, polarPosition(centerX, centerY, outerRingRadius, angle));
  });

  graph.edges.forEach((edge) => {
    const source = positionMap.get(edge.source);
    const target = positionMap.get(edge.target);
    if (!source || !target) return;
    const line = createSvgElement('line');
    line.setAttribute('x1', String(source.x));
    line.setAttribute('y1', String(source.y));
    line.setAttribute('x2', String(target.x));
    line.setAttribute('y2', String(target.y));
    line.setAttribute('class', `graph-edge ${normalizeGraphEdgeType(edge.edge_type)} ${edge.highlight || ''}`.trim());
    line.addEventListener('click', (event) => {
      event.stopPropagation();
      renderGraphEdgeDetail(edge);
    });
    svg.appendChild(line);
  });

  graph.nodes.forEach((node) => {
    const pos = positionMap.get(node.id);
    if (!pos) return;
    const group = createSvgElement('g');
    const activeClass = node.id === state.selectedGraphNodeId ? 'selected' : '';
    group.setAttribute('class', `graph-node ${node.node_type || ''} ${node.highlight || ''} ${activeClass}`.trim());
    const circle = createSvgElement('circle');
    const radius = node.node_type === 'job_family' ? 32 : 20;
    circle.setAttribute('cx', String(pos.x));
    circle.setAttribute('cy', String(pos.y));
    circle.setAttribute('r', String(radius));
    circle.setAttribute('fill', node.node_type === 'job_family' ? '#c85b3d' : '#234a78');
    circle.setAttribute('fill-opacity', node.node_type === 'job_family' ? '0.92' : '0.9');
    group.appendChild(circle);

    const title = createSvgElement('title');
    title.textContent = `${node.label}\n样本：${node.sample_count || 0}\n说明：${node.description || '-'}`;
    group.appendChild(title);

    svg.appendChild(group);
    appendGraphNodeLabel(group, node, pos, radius, centerX, centerY);
    group.addEventListener('click', async (event) => {
      event.stopPropagation();
      state.selectedGraphNodeId = node.id;
      state.graphNeighborOnly = true;
      applyGraphView({ resetDetail: false });
      await loadGraphEntityDetail(node);
      syncGraphToolbar(state.renderedGraph || graph);
    });
  });

  svg.onclick = () => {
    if (state.selectedGraphNodeId || state.graphNeighborOnly) {
      state.selectedGraphNodeId = '';
      state.graphNeighborOnly = false;
      applyGraphView({ resetDetail: false });
    }
    renderGraphDetailPlaceholder();
  };
  if (options.resetDetail !== false) renderGraphDetailPlaceholder();
  setText(els.heroGraphNodes, String(graph.metadata?.filtered_node_count || graph.nodes.length));
}

function uniqueList(values) {
  const result = [];
  const seen = new Set();
  (values || []).forEach((item) => {
    const text = String(item || '').trim();
    if (!text || seen.has(text)) return;
    seen.add(text);
    result.push(text);
  });
  return result;
}

function getPrimaryPathOption(response) {
  const candidates = [
    ...(response?.path_options || []),
    ...(response?.report?.recommended_paths || []),
  ];
  return candidates.find((item) => (item.path_jobs || []).length >= 2) || candidates[0] || null;
}

function getStudentSkillList(response) {
  return uniqueList([
    ...(response?.student_profile?.hard_skills || []),
    ...(response?.match_results?.[0]?.matched_skills || []),
    ...(response?.student_profile?.certificates || []),
  ]);
}

function normalizeGraphEdgeType(value) {
  const text = String(value || '').toLowerCase();
  if (text.includes('vertical')) return 'vertical';
  if (text.includes('require')) return 'requires';
  if (text.includes('has_skill') || text.includes('owned_skill')) return 'owned_skill';
  if (text.includes('missing_skill')) return 'missing_skill';
  if (text.includes('target_skill')) return 'target_skill';
  return text.includes('transfer') ? 'transfer' : text || 'transfer';
}

function updateGraphMode(isPersonal) {
  if (els.viewPersonalGraphBtn) els.viewPersonalGraphBtn.disabled = isPersonal;
  if (els.viewGlobalGraphBtn) els.viewGlobalGraphBtn.disabled = !isPersonal;
}

function renderPersonalGraphSummary(summary, option) {
  if (!els.personalGraphSummary) return;
  const pathJobs = summary?.selected_path || option?.path_jobs || [];
  const missingSkills = uniqueList([
    ...(summary?.missing_skills || []),
    ...(option?.missing_skills || []),
  ]);
  setClassName(els.personalGraphSummary, 'personal-graph-summary');
  setHtml(els.personalGraphSummary, `
    <article class="trend-card">
      <div class="trend-card-head">
        <strong>${escapeHtml(option?.path_name || '个性化路径')}</strong>
        <span class="badge confirmed">目标：${escapeHtml(summary?.target_job || option?.target_role || pathJobs[pathJobs.length - 1] || '-')}</span>
      </div>
      <p>${escapeHtml(option?.fit_reason || '该子图聚焦当前学生最值得优先查看的职业路径、缺口技能和证据来源。')}</p>
      <div class="trend-metric-list">
        <span class="pill">路径：${escapeHtml(pathJobs.join(' -> ') || '-')}</span>
        <span class="pill">准备度：${escapeHtml(summary?.readiness_score ?? option?.readiness_score ?? '-')}</span>
        <span class="pill">成功率：${escapeHtml(summary?.estimated_success_rate ?? option?.estimated_success_rate ?? '-')}</span>
        <span class="pill">时间成本：${escapeHtml(summary?.estimated_time_cost || option?.estimated_time_cost || '-')}</span>
      </div>
      <div class="structured-subtext">缺口技能：${escapeHtml(missingSkills.join(', ') || '当前没有识别到关键缺口')}</div>
      <div class="structured-subtext">证据来源：${escapeHtml((summary?.evidence_sources || option?.evidence_sources || []).join(' / ') || '当前没有额外证据')}</div>
    </article>
  `);
}

function renderGraphPlaceholder(message) {
  if (!els.personalGraphSummary) return;
  setClassName(els.personalGraphSummary, 'personal-graph-summary empty-state');
  setText(els.personalGraphSummary, message);
}

async function viewPersonalGraph() {
  if (!state.lastReportResponse) {
    setStatus('请先生成职业报告，再查看个人图谱。', 'error');
    return;
  }
  const option = getPrimaryPathOption(state.lastReportResponse);
  const topMatch = state.lastReportResponse.match_results?.[0];
  if (!option || !topMatch) {
    setStatus('当前报告中还没有可用的路径结果。', 'error');
    return;
  }

  try {
    const response = await apiFetch('/api/v1/planning/graph/personalized-subgraph', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        focus_job: topMatch.job_family,
        target_job: option.target_role || null,
        recommended_jobs: (state.lastReportResponse.match_results || []).slice(0, 3).map((item) => item.job_family),
        student_skills: getStudentSkillList(state.lastReportResponse),
        missing_skills: uniqueList([...(topMatch.missing_skills || []), ...(option.missing_skills || [])]),
        max_paths: 3,
      }),
    });
    state.personalizedGraph = await response.json();
    state.graphMode = 'personal';
    state.selectedGraphNodeId = state.personalizedGraph.summary?.focus_job || topMatch.job_family;
    state.graphNeighborOnly = true;
    renderPersonalGraphSummary(state.personalizedGraph.summary, option);
    updateGraphMode(true);
    applyGraphView({ resetDetail: true });
    setStatus('已切换到个人子图。', 'success');
  } catch (error) {
    setStatus(`查看个人图谱失败：${error.message}`, 'error');
  }
}

function viewGlobalGraph() {
  if (!state.graph) {
    setStatus('全局图谱尚未加载完成。', 'error');
    return;
  }
  state.graphMode = 'global';
  state.selectedGraphNodeId = '';
  state.graphNeighborOnly = false;
  updateGraphMode(false);
  applyGraphView({ resetDetail: true });
  renderGraphPlaceholder(state.lastReportResponse ? '已恢复全局图谱，你可以随时再次查看个人子图。' : '已显示全局图谱，先生成报告后可查看个人子图。');
  setStatus('已恢复全局图谱。', 'success');
}

function renderMetrics(response) {
  const metadata = response?.metadata || {};
  const topMatch = response?.match_results?.[0];
  setText(els.metricKnowledgeSource, metadata.knowledge_base_source || '-');
  setText(els.metricProfileMode, metadata.profile_mode || '-');
  setText(els.metricReportMode, metadata.report_mode || '-');
  setText(els.metricTopJob, topMatch ? `${topMatch.job_family} · ${topMatch.overall_score}` : '-');
  setText(els.heroMode, metadata.llm_enabled ? 'LLM' : 'Rule');
}

async function loadGraph() {
  try {
    const response = await apiFetch('/api/v1/planning/job-graph');
    state.graph = await response.json();
    state.graphMode = 'global';
    applyGraphView({ resetDetail: true });
    renderGraphPlaceholder(state.lastReportResponse ? '报告已更新，可点击“查看我的图谱”切换到个性化子图。' : '先生成职业报告，再点击“查看我的图谱”。');
    updateGraphMode(false);
  } catch (error) {
    setStatus(`加载岗位图谱失败：${error.message}`, 'error');
  }
}

async function loadJobFamilies() {
  try {
    const response = await apiFetch('/api/v1/planning/job-families');
    const data = await response.json();
    setText(els.heroJobCount, String(data.length));
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
    setText(els.metricKnowledgeSource, data.metadata?.knowledge_base_source || '-');
    setText(els.metricProfileMode, data.metadata?.profile_mode || '-');
    setText(els.heroMode, data.metadata?.llm_enabled ? 'LLM' : 'Rule');
    setStatus('Agent 追问已生成。', 'success');
  } catch (error) {
    setStatus(`生成追问失败：${error.message}`, 'error');
  }
}

async function generateReport() {
  const request = collectRequest();
  state.lastRequest = request;
  setStatus('正在生成职业报告...');
  try {
    const response = await apiFetch('/api/v1/planning/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    const data = await response.json();
    state.lastReportResponse = data;
    state.personalizedGraph = null;
    state.graphInsights = null;
    state.selectedGraphNodeId = '';
    state.graphNeighborOnly = false;
    state.selectedMatchIndex = 0;
    renderMetrics(data);
    renderMatches(data.match_results);
    renderFollowUps(data.follow_up_questions);
    renderSoftSkillAssessments(data.student_profile?.soft_skill_assessments);
    renderIndustryTrend(data.report?.industry_trend);
    renderGraphInsights(null);
    renderReport(data.report);
    renderEvidenceTrace(data.match_results?.[state.selectedMatchIndex]);
    renderGraphPlaceholder('生成报告后，可切换查看个人子图。');
    updateGraphMode(false);
    if (state.graph) {
      state.graphMode = 'global';
      applyGraphView({ resetDetail: true });
    }
    await loadGraphInsights(data);
    renderResultNavigator(data);
    setStatus('职业报告已生成。', 'success');
  } catch (error) {
    setStatus(`生成职业报告失败：${error.message}`, 'error');
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

function bindEvents() {
  document.getElementById('loadSampleBtn')?.addEventListener('click', loadSample);
  document.getElementById('parseResumeBtn')?.addEventListener('click', parseResume);
  document.getElementById('applyStructuredBtn')?.addEventListener('click', () => applyFormFillSuggestion(state.lastFormFillSuggestion));
  document.getElementById('followUpBtn')?.addEventListener('click', generateFollowUps);
  document.getElementById('generateBtn')?.addEventListener('click', generateReport);
  document.getElementById('downloadMarkdownBtn')?.addEventListener('click', downloadMarkdown);
  document.getElementById('downloadJsonBtn')?.addEventListener('click', downloadJson);
  els.viewPersonalGraphBtn?.addEventListener('click', viewPersonalGraph);
  els.viewGlobalGraphBtn?.addEventListener('click', viewGlobalGraph);
  els.graphSearchBtn?.addEventListener('click', async () => {
    const sourceGraph = getActiveGraphSource();
    state.graphSearch = els.graphSearchInput?.value.trim() || '';
    if (!state.graphSearch) {
      applyGraphView({ resetDetail: false });
      return;
    }
    const found = findFirstMatchingGraphNode(sourceGraph, state.graphSearch);
    if (!found) {
      applyGraphView({ resetDetail: false });
      setStatus(`未找到匹配节点：${state.graphSearch}`, 'error');
      return;
    }
    await focusGraphNode(found.id, { showStatus: false });
    setStatus(`已定位到节点：${found.label}`, 'success');
  });
  els.graphSearchInput?.addEventListener('keydown', async (event) => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    els.graphSearchBtn?.click();
  });
  els.graphCityFilter?.addEventListener('change', () => {
    state.graphCity = els.graphCityFilter?.value || '';
    applyGraphView({ resetDetail: false });
  });
  els.graphIndustryFilter?.addEventListener('change', () => {
    state.graphIndustry = els.graphIndustryFilter?.value || '';
    applyGraphView({ resetDetail: false });
  });
  els.graphNeighborBtn?.addEventListener('click', () => {
    if (!state.selectedGraphNodeId) return;
    state.graphNeighborOnly = !state.graphNeighborOnly;
    applyGraphView({ resetDetail: false });
  });
  els.graphFilterResetBtn?.addEventListener('click', () => {
    state.graphSearch = '';
    state.graphCity = '';
    state.graphIndustry = '';
    state.selectedGraphNodeId = '';
    state.graphNeighborOnly = false;
    if (els.graphSearchInput) els.graphSearchInput.value = '';
    applyGraphView({ resetDetail: true });
    setStatus('已重置图谱搜索与筛选条件。', 'success');
  });
  els.graphDetailBody?.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-graph-jump]');
    if (!button) return;
    const nodeId = button.dataset.graphJump || '';
    if (!nodeId) return;
    await focusGraphNode(nodeId, { resetFilters: true });
  });
  els.resultNavigator?.addEventListener('click', (event) => {
    const button = event.target.closest('.result-entry-btn');
    if (!button) return;
    const targetId = button.dataset.targetId || '';
    if (!targetId) return;
    focusSectionById(targetId);
  });
  els.followUpContainer?.addEventListener('input', (event) => {
    if (!event.target.classList.contains('followup-answer-input')) return;
    syncFollowUpAnswerTextarea();
    updateFollowUpAnswerHint();
  });
  els.structuredPendingList?.addEventListener('click', (event) => {
    const card = event.target.closest('.pending-item-card');
    if (!card) return;
    const inputId = card.dataset.inputId || '';
    if (!inputId) return;
    highlightField(inputId, { focus: true });
    setStatus(`已定位到待确认字段：${card.dataset.fieldPath || inputId}`, 'info');
  });
  els.matchContainer?.addEventListener('click', (event) => {
    const button = event.target.closest('.evidence-btn');
    if (!button || !state.lastReportResponse?.match_results?.length) return;
    state.selectedMatchIndex = Number(button.dataset.matchIndex) || 0;
    renderMatches(state.lastReportResponse.match_results);
    renderEvidenceTrace(state.lastReportResponse.match_results[state.selectedMatchIndex]);
    setStatus(`证据链已展开：${state.lastReportResponse.match_results[state.selectedMatchIndex].job_family}`, 'success');
  });
}

async function init() {
  bindEvents();
  renderResultNavigator(null);
  loadSample();
  await Promise.all([loadJobFamilies(), loadGraph()]);
  setStatus('前端 Demo 已准备完成，可以直接演示。', 'success');
}

init();
