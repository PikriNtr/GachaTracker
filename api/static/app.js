/**
 * GachaTracker Interactive Web Dashboard Logic (Phase 12)
 */

const API_BASE = window.location.origin;

// State management
let state = {
  currentDiscordId: '',
  currentGame: 'wuthering_waves',
  activeTab: 'wuthering_waves',
  gamesConfig: {},
  pullsOffset: 0,
  pullsLimit: 20,
  pullsTotal: 0,
  loadedAccounts: []
};

// Game display configurations
const GAME_META = {
  wuthering_waves: {
    name: 'Wuthering Waves',
    icon: '🌊',
    currency: 'Astrites'
  },
  genshin_impact: {
    name: 'Genshin Impact',
    icon: '🌌',
    currency: 'Primogems'
  },
  honkai_star_rail: {
    name: 'Honkai: Star Rail',
    icon: '🚂',
    currency: 'Stellar Jades'
  }
};

// Initialization
document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await checkApiHealth();
  await loadGamesMetadata();
  
  // Check URL parameters for discord_id
  const urlParams = new URLSearchParams(window.location.search);
  const discordIdParam = urlParams.get('id');
  if (discordIdParam) {
    document.getElementById('discordIdInput').value = discordIdParam;
    await loadUserData(discordIdParam);
  }
});

function setupEventListeners() {
  document.getElementById('searchBtn').addEventListener('click', () => {
    const id = document.getElementById('discordIdInput').value.trim();
    if (id) loadUserData(id);
  });

  document.getElementById('discordIdInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const id = document.getElementById('discordIdInput').value.trim();
      if (id) loadUserData(id);
    }
  });

  // Tab navigation
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      switchTab(tab);
    });
  });

  // Table filters
  document.getElementById('poolFilterSelect').addEventListener('change', () => {
    state.pullsOffset = 0;
    fetchAndRenderPulls();
  });

  document.getElementById('rarityFilterSelect').addEventListener('change', () => {
    state.pullsOffset = 0;
    fetchAndRenderPulls();
  });

  document.getElementById('pullSearchInput').addEventListener('input', debounce(() => {
    state.pullsOffset = 0;
    fetchAndRenderPulls();
  }, 300));

  // Pagination buttons
  document.getElementById('prevPageBtn').addEventListener('click', () => {
    if (state.pullsOffset > 0) {
      state.pullsOffset = Math.max(0, state.pullsOffset - state.pullsLimit);
      fetchAndRenderPulls();
    }
  });

  document.getElementById('nextPageBtn').addEventListener('click', () => {
    if (state.pullsOffset + state.pullsLimit < state.pullsTotal) {
      state.pullsOffset += state.pullsLimit;
      fetchAndRenderPulls();
    }
  });
}

// API Health Check
async function checkApiHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      document.getElementById('apiStatusBadge').className = 'status-indicator online';
      document.getElementById('apiStatusText').textContent = 'API Connected';
    } else {
      throw new Error();
    }
  } catch (err) {
    document.getElementById('apiStatusBadge').className = 'status-indicator';
    document.getElementById('apiStatusBadge').style.borderColor = 'rgba(239, 68, 68, 0.4)';
    document.getElementById('apiStatusBadge').style.color = '#ef4444';
    document.getElementById('apiStatusText').textContent = 'API Offline';
  }
}

// Load Games Metadata
async function loadGamesMetadata() {
  try {
    const res = await fetch(`${API_BASE}/games`);
    if (res.ok) {
      const data = await res.json();
      data.games.forEach(g => {
        state.gamesConfig[g.game_id] = g;
      });
    }
  } catch (err) {
    console.error('Failed to load games metadata:', err);
  }
}

// Quick lookup button handler
window.quickLookup = function(id) {
  document.getElementById('discordIdInput').value = id;
  loadUserData(id);
};

// Switch Tab
function switchTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
  });

  // Hide all main views
  document.getElementById('welcomeState').classList.add('hidden');
  document.getElementById('gameDashboardView').classList.add('hidden');
  document.getElementById('unifiedProfileView').classList.add('hidden');
  document.getElementById('bannerScheduleView').classList.add('hidden');

  if (tab === 'banner_schedule') {
    document.getElementById('bannerScheduleView').classList.remove('hidden');
    loadScheduleForGame(state.currentGame);
  } else if (tab === 'unified_profile') {
    if (state.currentDiscordId) {
      document.getElementById('unifiedProfileView').classList.remove('hidden');
      loadUnifiedProfile(state.currentDiscordId);
    } else {
      showAlert('Please enter a Discord ID first to view cross-game profile.');
      document.getElementById('welcomeState').classList.remove('hidden');
    }
  } else {
    // Game tab: wuthering_waves, genshin_impact, or honkai_star_rail
    state.currentGame = tab;
    if (state.currentDiscordId) {
      document.getElementById('gameDashboardView').classList.remove('hidden');
      renderGameDashboard(state.currentDiscordId, tab);
    } else {
      document.getElementById('welcomeState').classList.remove('hidden');
    }
  }
}

// Load User Data
async function loadUserData(discordId) {
  state.currentDiscordId = discordId;
  showLoading(true);
  closeAlert();

  try {
    const res = await fetch(`${API_BASE}/accounts/${discordId}`);
    if (!res.ok) {
      if (res.status === 404) {
        throw new Error(`No account data found for Discord ID: "${discordId}". Import history first via bot or API.`);
      }
      throw new Error(`Failed to load account data (status ${res.status}).`);
    }

    const data = await res.json();
    state.loadedAccounts = data.accounts || [];

    // If current tab is not a game, switch to first found game or stay
    if (['unified_profile', 'banner_schedule'].includes(state.activeTab)) {
      switchTab(state.activeTab);
    } else {
      // Find matching game or default to first available
      const hasCurrentGame = state.loadedAccounts.some(a => a.game_id === state.currentGame);
      if (!hasCurrentGame && state.loadedAccounts.length > 0) {
        state.currentGame = state.loadedAccounts[0].game_id;
        state.activeTab = state.currentGame;
      }
      switchTab(state.activeTab);
    }
  } catch (err) {
    showAlert(err.message);
    document.getElementById('gameDashboardView').classList.add('hidden');
    document.getElementById('unifiedProfileView').classList.add('hidden');
    document.getElementById('welcomeState').classList.remove('hidden');
  } finally {
    showLoading(false);
  }
}

// Render Game Dashboard
async function renderGameDashboard(discordId, gameId) {
  const meta = GAME_META[gameId] || { name: gameId, icon: '🎮', currency: 'Pulls' };
  
  document.getElementById('viewGameTitle').textContent = meta.name;
  document.getElementById('gameAvatarBadge').textContent = meta.icon;
  document.getElementById('discordIdLabel').textContent = discordId;

  // Find account info
  const acc = state.loadedAccounts.find(a => a.game_id === gameId);
  if (!acc) {
    document.getElementById('playerUidLabel').textContent = 'No Account Linked';
    document.getElementById('statTotalPulls').textContent = '0';
    document.getElementById('pityCardsContainer').innerHTML = `<div class="pity-card"><p style="color: var(--text-dim)">No pull data imported for ${meta.name}.</p></div>`;
    document.getElementById('analyticsContainer').innerHTML = '';
    document.getElementById('pullsTableBody').innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">No pulls found.</td></tr>';
    return;
  }

  document.getElementById('playerUidLabel').textContent = acc.player_id;
  document.getElementById('statTotalPulls').textContent = acc.total_pulls.toLocaleString();

  // Populate pool filter options
  populatePoolFilter(gameId);

  // Fetch Pity, Stats, and Pulls in parallel
  await Promise.all([
    fetchAndRenderPity(discordId, gameId),
    fetchAndRenderStats(discordId, gameId),
    fetchAndRenderPulls()
  ]);
}

function populatePoolFilter(gameId) {
  const select = document.getElementById('poolFilterSelect');
  select.innerHTML = '<option value="">All Banner Pools</option>';
  const config = state.gamesConfig[gameId];
  if (config && config.names) {
    for (const [poolId, poolName] of Object.entries(config.names)) {
      const opt = document.createElement('option');
      opt.value = poolId;
      opt.textContent = `${poolName} (${poolId})`;
      select.appendChild(opt);
    }
  }
}

// Fetch & Render Pity Cards
async function fetchAndRenderPity(discordId, gameId) {
  const container = document.getElementById('pityCardsContainer');
  container.innerHTML = '<p style="color: var(--text-dim)">Loading pity...</p>';

  try {
    const res = await fetch(`${API_BASE}/accounts/${discordId}/pity/${gameId}`);
    if (!res.ok) {
      container.innerHTML = '<p style="color: var(--text-dim)">No pity data available.</p>';
      return;
    }

    const data = await res.json();
    container.innerHTML = '';

    const banners = data.banners || {};
    for (const [poolId, info] of Object.entries(banners)) {
      const bannerName = info.banner_name || `Banner Pool ${poolId}`;
      const pity = info.current_pity || 0;
      const maxPity = info.max_pity || 80;
      const percentage = Math.min(100, Math.round((pity / maxPity) * 100));
      const isHighPity = percentage >= 75;

      let badgeClass = 'not-applicable';
      let badgeText = 'N/A';
      if (info.is_guaranteed === true) {
        badgeClass = 'guaranteed';
        badgeText = '✨ 100% Guaranteed';
      } else if (info.is_guaranteed === false) {
        badgeClass = 'fifty-fifty';
        badgeText = '🎲 50/50 Active';
      }

      const card = document.createElement('div');
      card.className = 'pity-card glass-panel';
      card.innerHTML = `
        <div class="pity-card-header">
          <span class="pity-banner-name">${escapeHtml(bannerName)}</span>
          <span class="guarantee-badge ${badgeClass}">${badgeText}</span>
        </div>
        <div class="pity-main-metric">
          <span class="pity-number">${pity}</span>
          <span class="pity-max">/ ${maxPity} pulls</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar-fill ${isHighPity ? 'high-pity' : ''}" style="width: ${percentage}%"></div>
        </div>
        <div class="pity-card-footer">
          <span>5★ count: <strong>${info.five_star_count || 0}</strong></span>
          <span>50/50 Win: <strong>${info.win_5050_count || 0}</strong> / Loss: <strong>${info.loss_5050_count || 0}</strong></span>
        </div>
      `;
      container.appendChild(card);
    }
  } catch (err) {
    container.innerHTML = `<p style="color: var(--text-dim)">Error loading pity: ${err.message}</p>`;
  }
}

// Fetch & Render Deep Statistics
async function fetchAndRenderStats(discordId, gameId) {
  const container = document.getElementById('analyticsContainer');
  container.innerHTML = '<p style="color: var(--text-dim)">Loading statistics...</p>';

  try {
    const res = await fetch(`${API_BASE}/accounts/${discordId}/stats/${gameId}`);
    if (!res.ok) {
      container.innerHTML = '';
      return;
    }

    const data = await res.json();
    container.innerHTML = '';

    let total5Star = 0;
    let total4Star = 0;
    let totalPullsAcc = 0;
    let sumPities = 0;
    let pityPoints = 0;

    const pools = data.pools || {};
    for (const [poolId, s] of Object.entries(pools)) {
      total5Star += (s.char_5star || 0) + (s.weapon_5star || 0);
      total4Star += (s.char_4star || 0) + (s.weapon_4star || 0);
      totalPullsAcc += (s.count || 0);
      
      const avgPity = s.avg_pity_5star ? s.avg_pity_5star.toFixed(1) : '--';
      const poolName = s.pool_name || `Pool ${poolId}`;

      const card = document.createElement('div');
      card.className = 'analytic-card glass-panel';
      card.innerHTML = `
        <h4>${escapeHtml(poolName)}</h4>
        <div class="pool-stat-row">
          <span style="color: var(--text-dim)">Total Pulls</span>
          <strong>${s.count || 0}</strong>
        </div>
        <div class="pool-stat-row">
          <span style="color: var(--gold-5star)">5★ Rate / Count</span>
          <strong>${s.char_5star + s.weapon_5star} <span style="font-size: 0.8rem; color: var(--text-dim)">(${s.char_5star}C / ${s.weapon_5star}W)</span></strong>
        </div>
        <div class="pool-stat-row">
          <span style="color: var(--purple-4star)">4★ Rate / Count</span>
          <strong>${s.char_4star + s.weapon_4star} <span style="font-size: 0.8rem; color: var(--text-dim)">(${s.char_4star}C / ${s.weapon_4star}W)</span></strong>
        </div>
        <div class="pool-stat-row">
          <span style="color: var(--text-dim)">Average 5★ Pity</span>
          <strong>${avgPity}</strong>
        </div>
        <div class="pool-stat-row">
          <span style="color: var(--text-dim)">Early 5★ (&lt;50 pity)</span>
          <strong>${s.early_5star_count || 0}</strong>
        </div>
      `;
      container.appendChild(card);
    }

    document.getElementById('stat5StarCount').textContent = total5Star;
    document.getElementById('stat4StarCount').textContent = total4Star;
    document.getElementById('statAvgPity').textContent = total5Star > 0 ? (totalPullsAcc / total5Star).toFixed(1) : '--';

  } catch (err) {
    container.innerHTML = `<p style="color: var(--text-dim)">Error loading analytics: ${err.message}</p>`;
  }
}

// Fetch & Render Pulls Table
async function fetchAndRenderPulls() {
  const tbody = document.getElementById('pullsTableBody');
  const poolVal = document.getElementById('poolFilterSelect').value;
  const rarityVal = document.getElementById('rarityFilterSelect').value;
  const searchVal = document.getElementById('pullSearchInput').value.trim().toLowerCase();

  tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">Loading pulls...</td></tr>';

  let url = `${API_BASE}/accounts/${state.currentDiscordId}/pulls/${state.currentGame}?limit=${state.pullsLimit}&offset=${state.pullsOffset}`;
  if (poolVal) url += `&card_pool_type=${encodeURIComponent(poolVal)}`;
  if (rarityVal) url += `&quality_level=${encodeURIComponent(rarityVal)}`;

  try {
    const res = await fetch(url);
    if (!res.ok) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">No pull history.</td></tr>';
      return;
    }

    const data = await res.json();
    state.pullsTotal = data.total || 0;

    let items = data.items || [];
    if (searchVal) {
      items = items.filter(p => (p.resource_name || '').toLowerCase().includes(searchVal));
    }

    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">No pulls match the filter.</td></tr>';
    } else {
      tbody.innerHTML = '';
      items.forEach(p => {
        const tr = document.createElement('tr');
        
        let rarityClass = `rarity-${p.quality_level || 3}`;
        let nameClass = p.quality_level === 5 ? 'gold-text' : (p.quality_level === 4 ? 'purple-text' : '');
        
        let winText = '--';
        if (p.is_5050_win === true) winText = '<span style="color: #34d399">Won</span>';
        else if (p.is_5050_win === false) winText = '<span style="color: #ef4444">Lost</span>';

        tr.innerHTML = `
          <td><span class="rarity-pill ${rarityClass}">${p.quality_level}★</span></td>
          <td><strong class="item-name ${nameClass}">${escapeHtml(p.resource_name || 'Unknown')}</strong></td>
          <td>${escapeHtml(p.item_type || 'Unknown')}</td>
          <td>${escapeHtml(p.card_pool_type || '--')}</td>
          <td><strong>${p.pity_at_pull || '--'}</strong></td>
          <td>${winText}</td>
          <td style="color: var(--text-dim); font-family: var(--font-mono); font-size: 0.8rem;">${p.time || '--'}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Pagination info
    const start = state.pullsTotal === 0 ? 0 : state.pullsOffset + 1;
    const end = Math.min(state.pullsOffset + state.pullsLimit, state.pullsTotal);
    document.getElementById('paginationInfo').textContent = `Showing ${start}-${end} of ${state.pullsTotal} pulls`;
    document.getElementById('prevPageBtn').disabled = state.pullsOffset <= 0;
    document.getElementById('nextPageBtn').disabled = end >= state.pullsTotal;

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">Error: ${err.message}</td></tr>`;
  }
}

// Load Unified Cross-Game Profile
async function loadUnifiedProfile(discordId) {
  const container = document.getElementById('unifiedProfileContent');
  container.innerHTML = '<p style="color: var(--text-dim); padding: 2rem;">Loading unified profile...</p>';

  try {
    const res = await fetch(`${API_BASE}/accounts/${discordId}/profile`);
    if (!res.ok) {
      container.innerHTML = '<p style="color: var(--text-dim); padding: 2rem;">No multi-game profile available for this account.</p>';
      return;
    }

    const data = await res.json();
    const prof = data.profile || {};

    container.innerHTML = `
      <div style="padding: 2rem;">
        <h3 style="margin-bottom: 1.5rem; font-size: 1.4rem;">${escapeHtml(data.player_label)}</h3>
        <div class="summary-stats-grid" style="margin-bottom: 2rem;">
          <div class="stat-box">
            <span class="stat-label">Total Pulls (All Games)</span>
            <span class="stat-value">${prof.total_pulls || 0}</span>
          </div>
          <div class="stat-box gold">
            <span class="stat-label">Total 5★ Items</span>
            <span class="stat-value">${prof.total_5star || 0}</span>
          </div>
          <div class="stat-box purple">
            <span class="stat-label">Total 4★ Items</span>
            <span class="stat-value">${prof.total_4star || 0}</span>
          </div>
        </div>

        <h4 style="margin-bottom: 1rem; color: #cbd5e1;">Active Game Accounts:</h4>
        <div class="pity-cards-grid">
          ${(prof.games || []).map(g => {
            const meta = GAME_META[g.game_id] || { name: g.game_id, icon: '🎮' };
            return `
              <div class="pity-card glass-panel">
                <div class="pity-card-header">
                  <span class="pity-banner-name">${meta.icon} ${meta.name}</span>
                </div>
                <div class="pool-stat-row">
                  <span style="color: var(--text-dim)">Pulls</span>
                  <strong>${g.total_pulls || 0}</strong>
                </div>
                <div class="pool-stat-row">
                  <span style="color: var(--gold-5star)">5★ Count</span>
                  <strong>${g.total_5star || 0}</strong>
                </div>
                <div class="pool-stat-row">
                  <span style="color: var(--purple-4star)">4★ Count</span>
                  <strong>${g.total_4star || 0}</strong>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color: var(--text-dim); padding: 2rem;">Error: ${err.message}</p>`;
  }
}

// Load Banner Schedules
window.loadScheduleForGame = async function(gameId, targetBtn) {
  if (targetBtn) {
    targetBtn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
    targetBtn.classList.add('active');
  }

  const container = document.getElementById('bannerScheduleContent');
  container.innerHTML = '<p style="color: var(--text-dim)">Loading banner schedule...</p>';

  try {
    const res = await fetch(`${API_BASE}/banners/${gameId}`);
    if (!res.ok) {
      container.innerHTML = '<p style="color: var(--text-dim)">No schedule data found.</p>';
      return;
    }

    const data = await res.json();
    container.innerHTML = '';

    const active = data.active || {};
    const upcoming = data.upcoming || {};

    const pools = new Set([...Object.keys(active), ...Object.keys(upcoming)]);
    if (pools.size === 0) {
      container.innerHTML = '<p style="color: var(--text-dim)">No active or upcoming banners listed for this game.</p>';
      return;
    }

    pools.forEach(poolKey => {
      const activeBanner = active[poolKey];
      const upcomingList = upcoming[poolKey] || [];

      const card = document.createElement('div');
      card.className = 'banner-card glass-panel active-banner';
      card.innerHTML = `
        <span class="guarantee-badge guaranteed" style="width: fit-content;">Pool: ${escapeHtml(poolKey)}</span>
        <h4 class="banner-title">${activeBanner ? escapeHtml(activeBanner.name) : 'No Active Banner'}</h4>
        ${activeBanner ? `
          <div class="banner-time">Active Window: ${activeBanner.start} ➔ ${activeBanner.end}</div>
          <div style="color: #cbd5e1; font-size: 0.9rem; margin-top: 0.5rem;">
            Featured: <strong>${(activeBanner.featured_5stars || []).join(', ') || 'Standard Pool'}</strong>
          </div>
        ` : ''}
        ${upcomingList.length > 0 ? `
          <div style="margin-top: 1rem; border-top: 1px solid var(--border-subtle); padding-top: 0.75rem;">
            <span style="font-size: 0.8rem; color: var(--text-dim); text-transform: uppercase;">Upcoming:</span>
            ${upcomingList.map(u => `
              <div style="font-size: 0.85rem; margin-top: 0.25rem;">
                <strong>${escapeHtml(u.name)}</strong> <span style="color: var(--text-dim)">(${u.start})</span>
              </div>
            `).join('')}
          </div>
        ` : ''}
      `;
      container.appendChild(card);
    });

  } catch (err) {
    container.innerHTML = `<p style="color: var(--text-dim)">Error loading schedule: ${err.message}</p>`;
  }
};

// Utilities
function showLoading(show) {
  document.getElementById('loadingSpinner').classList.toggle('hidden', !show);
}

function showAlert(msg) {
  document.getElementById('alertMessage').textContent = msg;
  document.getElementById('alertBanner').classList.remove('hidden');
}

window.closeAlert = function() {
  document.getElementById('alertBanner').classList.add('hidden');
};

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
