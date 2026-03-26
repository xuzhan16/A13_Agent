const state = {
  viz: null,
  lastPaths: [],
};

const DEMO_CASE = {
  fromJob: 'Java开发工程师',
  toJob: '架构师',
  maxSteps: 5,
  studentSkills: ['Java', 'Spring Boot', 'MySQL', '接口设计'],
};

const els = {
  uri: document.getElementById('neo4j-uri'),
  user: document.getElementById('neo4j-user'),
  password: document.getElementById('neo4j-password'),
  database: document.getElementById('neo4j-database'),
  fromJob: document.getElementById('from-job'),
  toJob: document.getElementById('to-job'),
  maxSteps: document.getElementById('max-steps'),
  studentSkills: document.getElementById('student-skills'),
  renderGraph: document.getElementById('render-graph'),
  queryPaths: document.getElementById('query-paths'),
  queryPersonalized: document.getElementById('query-personalized'),
  queryStatus: document.getElementById('query-status'),
  pathResults: document.getElementById('path-results'),
  detailPanel: document.getElementById('detail-panel'),
  caseSummary: document.getElementById('case-summary'),
  loadCase: document.getElementById('load-case'),
};

function getStudentSkills() {
  return els.studentSkills.value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function renderPill(text) {
  return `<span class="pill">${text}</span>`;
}

function formatPercent(value) {
  if (value === undefined || value === null || value === '') {
    return '-';
  }
  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return String(value);
  }
  return `${(numeric * 100).toFixed(1)}%`;
}

function setDetail(html) {
  els.detailPanel.innerHTML = html;
}

function setCaseSummary(html) {
  els.caseSummary.innerHTML = html;
}

function renderDetailForNode(node) {
  const properties = node.raw?.properties || {};
  const topSkills = (properties.top_skills || []).map(renderPill).join('');
  const topCities = (properties.top_cities || []).map(renderPill).join('');
  setDetail(`
    <div class="card">
      <h3>${node.label || node.id}</h3>
      <div class="meta">
        <div>类型：${properties.node_type || 'job_family'}</div>
        <div>样本量：${properties.sample_count || 0}</div>
      </div>
      <p>${properties.description || '暂无描述'}</p>
      <div><strong>高频技能</strong><div>${topSkills || '<span class="muted">暂无</span>'}</div></div>
      <div style="margin-top:10px;"><strong>重点城市</strong><div>${topCities || '<span class="muted">暂无</span>'}</div></div>
    </div>
  `);
}

function renderDetailForEdge(edge) {
  const props = edge.raw?.properties || {};
  const evidence = (props.evidence || []).map(renderPill).join('');
  const requiredSkills = (props.required_skills || []).map(renderPill).join('');
  setDetail(`
    <div class="card">
      <h3>${edge.from} -> ${edge.to}</h3>
      <div class="meta">
        <div>关系：${edge.label || edge.raw?.type || 'TRANSFER_TO'}</div>
        <div>成功率：${formatPercent(props.success_rate)}</div>
        <div>时间成本：${props.time_cost || '-'}</div>
        <div>难度：${props.difficulty || '-'}</div>
      </div>
      <div><strong>需补齐技能</strong><div>${requiredSkills || '<span class="muted">暂无</span>'}</div></div>
      <div style="margin-top:10px;"><strong>证据来源</strong><div>${evidence || '<span class="muted">暂无</span>'}</div></div>
      <p style="margin-top:10px;">${props.reason || ''}</p>
    </div>
  `);
}

function renderPathResults(paths) {
  state.lastPaths = paths;
  if (!paths.length) {
    els.pathResults.innerHTML = '<div class="empty">没有查询到符合条件的路径。</div>';
    return;
  }
  els.pathResults.innerHTML = paths.map((path, index) => `
    <div class="card">
      <div class="path-chain">${path.jobs.join(' -> ')}</div>
      <div class="meta">
        <div>步数：${path.steps}</div>
        <div>累计成功率：${formatPercent(path.cumulative_success_rate)}</div>
        <div>时间成本：${path.estimated_time_cost}</div>
        <div>难度：${path.difficulty}</div>
        <div>准备度：${Math.round((path.ready_ratio || 0) * 100)}%</div>
        <div>可立即走：${path.is_feasible ? '是' : '否'}</div>
      </div>
      <div><strong>缺失技能</strong><div>${(path.missing_skills || []).map(renderPill).join('') || '<span class="muted">暂无</span>'}</div></div>
      <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
        <button type="button" data-index="${index}" class="show-evidence">查看证据链</button>
      </div>
    </div>
  `).join('');

  document.querySelectorAll('.show-evidence').forEach((button) => {
    button.addEventListener('click', async () => {
      const path = state.lastPaths[Number(button.dataset.index)];
      await loadPathEvidence(path.jobs);
    });
  });
}

function renderBestPathSummary(path, modeLabel) {
  if (!path) {
    setCaseSummary('<div class="empty">暂无推荐路径。</div>');
    return;
  }
  setCaseSummary(`
    <div class="card">
      <h3>${modeLabel}</h3>
      <div class="path-chain">${path.jobs.join(' -> ')}</div>
      <div class="meta">
        <div>累计成功率：${formatPercent(path.cumulative_success_rate)}</div>
        <div>时间成本：${path.estimated_time_cost}</div>
        <div>难度：${path.difficulty}</div>
        <div>准备度：${Math.round((path.ready_ratio || 0) * 100)}%</div>
      </div>
      <div><strong>最值得优先补齐</strong><div>${(path.missing_skills || []).map(renderPill).join('') || '<span class="muted">当前没有明显缺口</span>'}</div></div>
    </div>
  `);
}

async function loadPathEvidence(pathJobs) {
  const response = await fetch('/api/v1/planning/graph/path-evidence', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path_jobs: pathJobs, student_skills: getStudentSkills() }),
  });
  if (!response.ok) {
    setDetail(`<div class="empty">证据链查询失败：${response.status}</div>`);
    return;
  }
  const payload = await response.json();
  const steps = (payload.edge_chain || []).map((edge) => `
    <div class="card">
      <h3>${edge.source_job} -> ${edge.target_job}</h3>
      <div class="meta">
        <div>关系：${edge.relation_type}</div>
        <div>成功率：${formatPercent(edge.success_rate)}</div>
        <div>时间成本：${edge.time_cost}</div>
        <div>难度：${edge.difficulty}</div>
      </div>
      <div><strong>所需技能</strong><div>${(edge.required_skills || []).map(renderPill).join('') || '<span class="muted">暂无</span>'}</div></div>
      <div style="margin-top: 8px;"><strong>待补齐</strong><div>${(edge.missing_skills || []).map(renderPill).join('') || '<span class="muted">暂无</span>'}</div></div>
      <div style="margin-top: 8px;"><strong>证据</strong><div>${(edge.evidence || []).map(renderPill).join('') || '<span class="muted">暂无</span>'}</div></div>
    </div>
  `).join('');
  setDetail(`
    <div class="card">
      <h3>路径证据链</h3>
      <p>${(payload.path_jobs || []).join(' -> ')}</p>
      <div><strong>路径总缺口</strong><div>${(payload.aggregated_missing_skills || []).map(renderPill).join('') || '<span class="muted">暂无</span>'}</div></div>
      <div style="margin-top: 10px;"><strong>证据来源汇总</strong><div>${(payload.evidence_sources || []).map(renderPill).join('') || '<span class="muted">暂无</span>'}</div></div>
    </div>
    ${steps}
  `);
}

async function queryPaths(kind) {
  els.queryStatus.textContent = '正在查询...';
  const endpoint = kind === 'personalized'
    ? '/api/v1/planning/graph/personalized-paths'
    : '/api/v1/planning/graph/transfer-paths';
  const body = kind === 'personalized'
    ? {
        from_job: els.fromJob.value.trim(),
        target_job: els.toJob.value.trim(),
        student_skills: getStudentSkills(),
        max_steps: Number(els.maxSteps.value || 5),
        limit: 10,
      }
    : {
        from_job: els.fromJob.value.trim(),
        to_job: els.toJob.value.trim(),
        max_steps: Number(els.maxSteps.value || 5),
      };

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    els.queryStatus.textContent = `查询失败：${response.status}`;
    renderPathResults([]);
    renderBestPathSummary(null, '暂无结果');
    return;
  }

  const payload = await response.json();
  els.queryStatus.textContent = `已返回 ${payload.length} 条路径`;
  renderPathResults(payload);
  renderBestPathSummary(payload[0], kind === 'personalized' ? '个性化最优路径' : '最短候选路径');
  if (kind === 'personalized' && payload[0]) {
    await loadPathEvidence(payload[0].jobs);
  }
}

function buildVizConfig() {
  return {
    containerId: 'viz',
    neo4j: {
      serverUrl: els.uri.value.trim(),
      serverUser: els.user.value.trim(),
      serverPassword: els.password.value,
      database: els.database.value.trim() || 'neo4j',
    },
    labels: {
      Job: {
        label: 'label',
        value: 'sample_count',
        [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
          function: {
            title: (node) => JSON.stringify(node.properties, null, 2),
          },
        },
      },
      Skill: {
        label: 'name',
        [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
          function: {
            title: (node) => JSON.stringify(node.properties, null, 2),
          },
        },
      },
      Ability: {
        label: 'name',
        [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
          function: {
            title: (node) => JSON.stringify(node.properties, null, 2),
          },
        },
      },
    },
    relationships: {
      TRANSFER_TO: {
        value: 'weight',
        label: 'difficulty',
        [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
          function: {
            title: (rel) => JSON.stringify(rel.properties, null, 2),
          },
        },
      },
      VERTICAL_TO: {
        value: 'success_rate',
        label: 'time_cost',
        [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
          function: {
            title: (rel) => JSON.stringify(rel.properties, null, 2),
          },
        },
      },
      REQUIRES: { label: 'requirement_type' },
      DEPENDS_ON: { label: 'dependency_strength' },
    },
    initialCypher: 'MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 200',
  };
}

function bindNetworkEvents() {
  if (!state.viz || !state.viz.network) {
    return;
  }
  state.viz.network.on('click', (params) => {
    if (params.nodes.length > 0) {
      const node = state.viz.nodes.get(params.nodes[0]);
      renderDetailForNode(node);
      return;
    }
    if (params.edges.length > 0) {
      const edge = state.viz.edges.get(params.edges[0]);
      renderDetailForEdge(edge);
    }
  });
}

function renderGraph() {
  try {
    state.viz = new NeoVis.default(buildVizConfig());
    state.viz.render();
    state.viz.registerOnEvent('completed', () => {
      bindNetworkEvents();
      els.queryStatus.textContent = '图谱已渲染';
    });
  } catch (error) {
    els.queryStatus.textContent = `图谱渲染失败：${error.message}`;
  }
}

function loadDemoCase() {
  els.fromJob.value = DEMO_CASE.fromJob;
  els.toJob.value = DEMO_CASE.toJob;
  els.maxSteps.value = DEMO_CASE.maxSteps;
  els.studentSkills.value = DEMO_CASE.studentSkills.join(',');
  renderBestPathSummary(null, '学生 C 案例');
  setDetail('<div class="empty">已加载学生 C 案例，接下来点击“查询个性化路径”即可直接演示。</div>');
  els.queryStatus.textContent = '学生 C 案例已加载';
}

els.renderGraph.addEventListener('click', renderGraph);
els.queryPaths.addEventListener('click', () => queryPaths('all'));
els.queryPersonalized.addEventListener('click', () => queryPaths('personalized'));
els.loadCase.addEventListener('click', loadDemoCase);

loadDemoCase();
