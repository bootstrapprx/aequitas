<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount, onDestroy } from "svelte";
  import { createEventDispatcher } from "svelte";
  import { setupLiveUpdates, cleanupLiveUpdates } from "./stores/governance";

  const dispatch = createEventDispatcher();

  let loading = true;
  let error = null;
  let dashboard = null;

  onMount(async () => {
    await loadDashboard();

    // PHASE 2.3: Setup live updates for real-time dashboard refresh
    await setupLiveUpdates({
      onGoalChange: async () => {
        console.log('[Dashboard] Goal changed, reloading...');
        await loadDashboard();
      },
      onPhaseChange: async () => {
        console.log('[Dashboard] Phase changed, reloading...');
        await loadDashboard();
      }
    });
  });

  onDestroy(async () => {
    await cleanupLiveUpdates();
  });

  async function loadDashboard() {
    try {
      loading = true;
      error = null;
      console.log("Loading dashboard...");
      dashboard = await invoke("get_aequitas_dashboard");
      console.log("Dashboard loaded:", dashboard);
    } catch (err) {
      error = err?.toString?.() ?? String(err);
      console.error("Failed to load Aequitas dashboard:", err);
    } finally {
      loading = false;
    }
  }

  function formatPercentage(value) {
    return value.toFixed(1) + "%";
  }

  function formatDate(dateStr) {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString();
  }

  function navigateToGoals() {
    dispatch("navigate", { view: "goals" });
  }

  function navigateToPhases() {
    dispatch("navigate", { view: "phases" });
  }

  function filterBlockedGoals() {
    dispatch("navigate", { view: "goals", filter: "blocked" });
  }

  function viewGoal(goalId) {
    dispatch("navigate", { view: "goals", goalId });
  }
</script>

<div class="dashboard">
  {#if loading}
    <div class="loading">
      <div class="spinner" />
      <p>Loading dashboard...</p>
    </div>
  {:else if error}
    <div class="error">
      <h2>⚠️ Error Loading Dashboard</h2>
      <p class="error-msg">{error}</p>
      <button on:click={loadDashboard} class="btn-retry">Retry</button>
    </div>
  {:else if dashboard}
    <!-- Hero Section -->
    <div class="hero">
      <div class="hero-content">
        <h1 class="title">Aequitas Progress</h1>
        <p class="mission">Finish Aequitas · Leave a Trace · Continue Evolution</p>
      </div>
      <button on:click={loadDashboard} class="btn-refresh">
        <span>↻</span> Refresh
      </button>
    </div>

    <!-- KPI Cards -->
    <div class="kpi-grid">
      <!-- Completion Card -->
      <button class="kpi-card large" on:click={navigateToGoals}>
        <div class="kpi-icon">🎯</div>
        <div class="kpi-content">
          <div class="kpi-value">{formatPercentage(dashboard.completion.percentage)}</div>
          <div class="kpi-label">Overall Completion</div>
          <div class="kpi-detail">{dashboard.completion.done_goals} of {dashboard.completion.total_goals} goals</div>
        </div>
        <div class="kpi-progress">
          <div class="progress-bar">
            <div class="progress-fill" style="width: {dashboard.completion.percentage}%" />
          </div>
        </div>
      </button>

      <!-- Active Goals -->
      <button class="kpi-card" on:click={navigateToGoals}>
        <div class="kpi-icon active">⚡</div>
        <div class="kpi-content">
          <div class="kpi-value">{dashboard.completion.active_goals}</div>
          <div class="kpi-label">Active</div>
        </div>
      </button>

      <!-- Blocked Goals -->
      <button class="kpi-card {dashboard.completion.blocked_goals > 0 ? 'warning' : ''}" on:click={filterBlockedGoals}>
        <div class="kpi-icon blocked">🚧</div>
        <div class="kpi-content">
          <div class="kpi-value">{dashboard.completion.blocked_goals}</div>
          <div class="kpi-label">Blocked</div>
        </div>
      </button>

      <!-- Velocity -->
      <button class="kpi-card" on:click={navigateToGoals}>
        <div class="kpi-icon">📈</div>
        <div class="kpi-content">
          <div class="kpi-value">{dashboard.recent_activity.velocity.toFixed(2)}</div>
          <div class="kpi-label">Goals/Day</div>
        </div>
      </button>
    </div>

    <!-- Current Phase -->
    {#if dashboard.current_phase.phase_number}
      <div class="phase-card">
        <div class="phase-header">
          <div class="phase-info">
            <span class="phase-badge">Phase {dashboard.current_phase.phase_number}</span>
            <h2 class="phase-title">{dashboard.current_phase.phase_title}</h2>
            <span class="status-badge {dashboard.current_phase.phase_status}">
              {dashboard.current_phase.phase_status}
            </span>
          </div>
          <button class="btn-action" on:click={navigateToPhases}>View Details →</button>
        </div>
        <div class="phase-stats">
          <div class="stat">
            <div class="stat-value">{dashboard.current_phase.done_in_phase}</div>
            <div class="stat-label">Complete</div>
          </div>
          <div class="stat">
            <div class="stat-value">{dashboard.current_phase.goals_in_phase - dashboard.current_phase.done_in_phase}</div>
            <div class="stat-label">Remaining</div>
          </div>
          <div class="stat">
            <div class="stat-value">{formatPercentage(dashboard.current_phase.phase_completion)}</div>
            <div class="stat-label">Progress</div>
          </div>
        </div>
        <div class="progress-bar phase-progress">
          <div class="progress-fill phase" style="width: {dashboard.current_phase.phase_completion}%" />
        </div>
      </div>
    {:else}
      <div class="phase-card empty">
        <div class="empty-state">
          <span class="empty-icon">📋</span>
          <p>No active phase detected</p>
          <button class="btn-action" on:click={navigateToPhases}>Set Active Phase</button>
        </div>
      </div>
    {/if}

    <!-- Two Column Layout -->
    <div class="two-col">
      <!-- Blockers -->
      <div class="panel">
        <div class="panel-header">
          <h3>🚨 Critical Blockers</h3>
          <span class="count-badge">{dashboard.blockers.length}</span>
        </div>
        {#if dashboard.blockers.length > 0}
          <div class="list">
            {#each dashboard.blockers.slice(0, 5) as blocker}
              <button class="list-item blocker" on:click={() => viewGoal(blocker.goal_id)}>
                <div class="item-header">
                  <span class="goal-id">{blocker.goal_id}</span>
                  <span class="badge danger">{blocker.blocking_count} blocked</span>
                </div>
                <div class="item-title">{blocker.title}</div>
                {#if blocker.reason}
                  <div class="item-reason">{blocker.reason}</div>
                {/if}
              </button>
            {/each}
          </div>
          {#if dashboard.blockers.length > 5}
            <button class="btn-more" on:click={filterBlockedGoals}>
              View all {dashboard.blockers.length} blockers →
            </button>
          {/if}
        {:else}
          <div class="empty-state small">
            <span class="empty-icon">✅</span>
            <p>No blockers - great work!</p>
          </div>
        {/if}
      </div>

      <!-- Critical Path -->
      <div class="panel">
        <div class="panel-header">
          <h3>🎯 Critical Path</h3>
          <span class="count-badge">{dashboard.critical_path.length}</span>
        </div>
        {#if dashboard.critical_path.length > 0}
          <div class="list">
            {#each dashboard.critical_path.slice(0, 5) as critical}
              <button class="list-item critical" on:click={() => viewGoal(critical.goal_id)}>
                <div class="item-header">
                  <span class="goal-id">{critical.goal_id}</span>
                  <span class="badge primary">{critical.reverse_dependencies} deps</span>
                </div>
                <div class="item-title">{critical.title}</div>
                <div class="item-meta">
                  <span class="status-dot {critical.status}" />
                  {critical.status}
                  {#if critical.phase}· Phase {critical.phase}{/if}
                </div>
              </button>
            {/each}
          </div>
          {#if dashboard.critical_path.length > 5}
            <button class="btn-more" on:click={navigateToGoals}>
              View all {dashboard.critical_path.length} critical goals →
            </button>
          {/if}
        {:else}
          <div class="empty-state small">
            <span class="empty-icon">📊</span>
            <p>No dependencies tracked</p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Health Metrics -->
    <div class="health-grid">
      <div class="health-card {dashboard.health.blocked_percentage > 20 ? 'warning' : 'good'}">
        <div class="health-value">{formatPercentage(dashboard.health.blocked_percentage)}</div>
        <div class="health-label">Blocked Rate</div>
      </div>
      <div class="health-card {dashboard.health.orphaned_goals > 0 ? 'warning' : 'good'}">
        <div class="health-value">{dashboard.health.orphaned_goals}</div>
        <div class="health-label">Orphaned Goals</div>
      </div>
      <div class="health-card {dashboard.health.missing_dependencies > 0 ? 'error' : 'good'}">
        <div class="health-value">{dashboard.health.missing_dependencies}</div>
        <div class="health-label">Missing Deps</div>
      </div>
      <div class="health-card {dashboard.health.audit_errors > 0 ? 'error' : 'good'}">
        <div class="health-value">{dashboard.health.audit_errors}</div>
        <div class="health-label">Audit Errors</div>
      </div>
    </div>
  {/if}
</div>

<style>
  .dashboard {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    gap: 1rem;
  }

  .spinner {
    width: 48px;
    height: 48px;
    border: 4px solid rgba(148, 163, 184, 0.2);
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .error {
    text-align: center;
    padding: 3rem;
    background: rgba(239, 68, 68, 0.1);
    border-radius: 12px;
    border: 2px solid rgba(239, 68, 68, 0.5);
  }

  .error-msg {
    color: #fca5a5;
    margin: 1rem 0;
    font-family: monospace;
  }

  .btn-retry {
    padding: 0.75rem 2rem;
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-retry:hover {
    background: #dc2626;
    transform: translateY(-1px);
  }

  /* Hero */
  .hero {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding: 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    color: white;
  }

  .title {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0 0 0.5rem 0;
  }

  .mission {
    font-size: 1.1rem;
    opacity: 0.95;
    margin: 0;
  }

  .btn-refresh {
    padding: 0.75rem 1.5rem;
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 8px;
    color: white;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .btn-refresh:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
  }

  .btn-refresh span {
    font-size: 1.3rem;
    display: inline-block;
  }

  .btn-refresh:hover span {
    animation: spin 0.5s linear;
  }

  /* KPI Grid */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .kpi-card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(100, 116, 139, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s;
    text-align: left;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
  }

  .kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.8);
    border-color: #3b82f6;
    background: rgba(15, 23, 42, 0.8);
  }

  .kpi-card.large {
    grid-column: span 2;
  }

  .kpi-card.warning {
    border-color: #f59e0b;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(245, 158, 11, 0.1) 100%);
  }

  .kpi-icon {
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  }

  .kpi-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: #f1f5f9;
    margin-bottom: 0.25rem;
  }

  .kpi-label {
    font-size: 0.9rem;
    color: #cbd5e1;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .kpi-detail {
    font-size: 0.875rem;
    color: #94a3b8;
    margin-top: 0.5rem;
  }

  .kpi-progress {
    margin-top: 1rem;
  }

  .progress-bar {
    height: 8px;
    background: rgba(100, 116, 139, 0.2);
    border-radius: 999px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
    transition: width 0.5s ease;
  }

  .progress-fill.phase {
    background: linear-gradient(90deg, #10b981 0%, #06b6d4 100%);
  }

  /* Phase Card */
  .phase-card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(100, 116, 139, 0.3);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
  }

  .phase-card.empty {
    background: rgba(15, 23, 42, 0.3);
  }

  .phase-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .phase-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .phase-badge {
    padding: 0.5rem 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.875rem;
  }

  .phase-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    color: #f1f5f9;
  }

  .status-badge {
    padding: 0.375rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .status-badge.active {
    background: rgba(59, 130, 246, 0.2);
    color: #93c5fd;
  }

  .btn-action {
    padding: 0.625rem 1.25rem;
    background: rgba(51, 65, 85, 0.5);
    border: 1px solid rgba(100, 116, 139, 0.3);
    border-radius: 8px;
    font-weight: 600;
    color: #cbd5e1;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-action:hover {
    background: rgba(51, 65, 85, 0.8);
    transform: translateX(2px);
    border-color: #3b82f6;
  }

  .phase-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    margin-bottom: 1.5rem;
  }

  .stat {
    text-align: center;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 800;
    color: #f1f5f9;
  }

  .stat-label {
    font-size: 0.875rem;
    color: #cbd5e1;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
  }

  .phase-progress {
    height: 12px;
  }

  /* Two Column */
  .two-col {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .panel {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(100, 116, 139, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .panel-header h3 {
    font-size: 1.125rem;
    font-weight: 700;
    margin: 0;
    color: #f1f5f9;
  }

  .count-badge {
    padding: 0.25rem 0.75rem;
    background: rgba(51, 65, 85, 0.6);
    border-radius: 999px;
    font-size: 0.875rem;
    font-weight: 700;
    color: #cbd5e1;
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .list-item {
    padding: 1rem;
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(100, 116, 139, 0.3);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
  }

  .list-item:hover {
    background: rgba(30, 41, 59, 0.6);
    border-color: rgba(100, 116, 139, 0.5);
    transform: translateX(4px);
  }

  .list-item.blocker:hover {
    border-color: #ef4444;
  }

  .list-item.critical:hover {
    border-color: #3b82f6;
  }

  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .goal-id {
    font-family: monospace;
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 600;
  }

  .badge {
    padding: 0.25rem 0.625rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .badge.danger {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
  }

  .badge.primary {
    background: rgba(59, 130, 246, 0.2);
    color: #93c5fd;
  }

  .item-title {
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 0.5rem;
  }

  .item-reason {
    font-size: 0.875rem;
    color: #fca5a5;
  }

  .item-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: #94a3b8;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .status-dot.active { background: #3b82f6; }
  .status-dot.blocked { background: #ef4444; }
  .status-dot.done { background: #10b981; }
  .status-dot.planned { background: #94a3b8; }

  .btn-more {
    width: 100%;
    padding: 0.75rem;
    margin-top: 0.75rem;
    background: rgba(30, 41, 59, 0.3);
    border: 1px dashed rgba(100, 116, 139, 0.5);
    border-radius: 8px;
    color: #cbd5e1;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-more:hover {
    background: rgba(30, 41, 59, 0.5);
    border-color: #3b82f6;
  }

  /* Health Grid */
  .health-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
  }

  .health-card {
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    transition: all 0.3s;
    backdrop-filter: blur(10px);
  }

  .health-card.good {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%);
    border: 2px solid rgba(16, 185, 129, 0.4);
  }

  .health-card.warning {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.1) 100%);
    border: 2px solid rgba(245, 158, 11, 0.4);
  }

  .health-card.error {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.1) 100%);
    border: 2px solid rgba(239, 68, 68, 0.4);
  }

  .health-value {
    font-size: 2rem;
    font-weight: 800;
    color: #f1f5f9;
  }

  .health-label {
    font-size: 0.875rem;
    color: #cbd5e1;
    font-weight: 600;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
  }

  .empty-state.small {
    padding: 2rem 1rem;
  }

  .empty-icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 1rem;
    filter: grayscale(50%);
    opacity: 0.5;
  }

  .empty-state p {
    color: #94a3b8;
    margin: 0 0 1rem 0;
  }
</style>
