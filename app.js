/**
 * FLUXMEDIA LAN SHARE PORTAL - APPLICATION CONTROLLER
 * Vanilla JS logic for Material 3 responsive SPA.
 */

// Safe storage helper to prevent crash in sandboxed/cookies-disabled environments
const safeStorage = {
  getItem(key, isSession = false) {
    try {
      const store = isSession ? window.sessionStorage : window.localStorage;
      return store.getItem(key);
    } catch (e) {
      console.warn("Storage read blocked:", e);
      return null;
    }
  },
  setItem(key, value, isSession = false) {
    try {
      const store = isSession ? window.sessionStorage : window.localStorage;
      store.setItem(key, value);
    } catch (e) {
      console.warn("Storage write blocked:", e);
    }
  },
  removeItem(key, isSession = false) {
    try {
      const store = isSession ? window.sessionStorage : window.localStorage;
      store.removeItem(key);
    } catch (e) {
      console.warn("Storage remove blocked:", e);
    }
  }
};

// Application State
const state = {
  files: [],
  meta: null,
  activeFilter: 'all',
  searchQuery: '',
  sortOption: 'added-desc',
  viewMode: safeStorage.getItem('viewMode') || 'grid',
  selectedFiles: new Set(),
  sessionToken: safeStorage.getItem('fluxToken', true) || '',
  activeFileIndex: -1,
  currentPlayingAudioId: null,
  isMockMode: new URLSearchParams(window.location.search).get('mock') === 'true',
  zoomScale: 1,
  zoomTranslate: { x: 0, y: 0 },
  isDraggingImage: false,
  dragStart: { x: 0, y: 0 },
  playlist: JSON.parse(safeStorage.getItem('flux-playlist')) || [],
  syncPlay: {
    active: false,
    file_idx: null,
    media_type: null,
    file_name: null,
    state: "PAUSED",
    time: 0.0,
    clientId: window.crypto && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 15),
    last_update: 0.0,
    isSynced: false,
    clients: [],
    panelMode: safeStorage.getItem('wpPanelMode') || 'fab',
    lockMode: safeStorage.getItem('wpLockMode') || 'loose',
    deviceName: safeStorage.getItem('wpDeviceName') || detectDeviceName()
  }
};

// Global DOM references
let globalAudio = null;
let searchDebounceTimer = null;

// Mock data (loaded if backend is not running or returns errors)
const MOCK_META = {
  profile_name: "Rohan's FluxMedia Share",
  profile_image_url: "",
  theme_tone: "Royal Purple",
  password_protected: true
};

const MOCK_FILES = [
  {
    id: "vid-1",
    name: "Summer Surf & Beach Vlog 2026.mp4",
    type: "video",
    size: 154857600,
    duration: 184,
    thumbnail_url: "",
    added_at: "2026-07-03T12:00:00Z"
  },
  {
    id: "vid-2",
    name: "System Architecture Presentation.mp4",
    type: "video",
    size: 45298483,
    duration: 312,
    thumbnail_url: "",
    added_at: "2026-07-02T15:30:00Z"
  },
  {
    id: "aud-1",
    name: "FluxMedia Podcast Ep 42 - Local Sharing.mp3",
    type: "audio",
    size: 24859200,
    duration: 1240,
    thumbnail_url: "",
    added_at: "2026-06-30T10:15:00Z"
  },
  {
    id: "aud-2",
    name: "Lofi Chill Beats for Coding.mp3",
    type: "audio",
    size: 8493022,
    duration: 215,
    thumbnail_url: "",
    added_at: "2026-07-03T20:00:00Z"
  },
  {
    id: "doc-1",
    name: "FluxMedia Offline Setup Guide.pdf",
    type: "document",
    size: 1420584,
    duration: null,
    thumbnail_url: "",
    added_at: "2026-07-04T08:00:00Z"
  },
  {
    id: "doc-2",
    name: "Design Requirements Document.docx",
    type: "document",
    size: 45293,
    duration: null,
    thumbnail_url: "",
    added_at: "2026-07-02T09:00:00Z"
  },
  {
    id: "img-1",
    name: "Vibrant UI Mockup Dark Theme.png",
    type: "image",
    size: 3482049,
    duration: null,
    thumbnail_url: "",
    added_at: "2026-07-03T11:45:00Z"
  },
  {
    id: "img-2",
    name: "FluxMedia Vector Logo.jpg",
    type: "image",
    size: 852033,
    duration: null,
    thumbnail_url: "",
    added_at: "2026-07-04T02:30:00Z"
  },
  {
    id: "oth-1",
    name: "Firmware_Update_Release_Package.zip",
    type: "other",
    size: 859302834,
    duration: null,
    thumbnail_url: "",
    added_at: "2026-06-25T17:00:00Z"
  }
];

// Initialize on DOM Load
document.addEventListener('DOMContentLoaded', () => {
  initGlobalAudio();
  detectSystemTheme();
  setupEventListeners();
  loadPortalData();
  initSyncPlay();
  initWatchPartySettings();
});

// Create invisible global audio elements
function initGlobalAudio() {
  globalAudio = document.createElement('audio');
  globalAudio.id = 'global-audio-el';
  globalAudio.preload = 'auto';
  document.body.appendChild(globalAudio);
}

/* ===========================================================================
   WATCH PARTY — SYNC PLAY
   ===========================================================================*/

/** Auto-detect a friendly device name from User-Agent */
function detectDeviceName() {
  const ua = navigator.userAgent || '';
  if (/iPhone/i.test(ua)) return '📱 iPhone';
  if (/iPad/i.test(ua)) return '📱 iPad';
  if (/Android.*Mobile/i.test(ua)) return '📱 Android Phone';
  if (/Android/i.test(ua)) return '📱 Android Tablet';
  if (/Macintosh/i.test(ua)) return '🖥 Mac';
  if (/Windows/i.test(ua)) return '💻 Windows PC';
  if (/Linux/i.test(ua)) return '🖥 Linux';
  return '🌐 Browser';
}

function initSyncPlay() {
  applyWatchPartyPanelMode(state.syncPlay.panelMode);

  // Register client on page load
  apiFetch('/api/sync/ping', {
    method: 'POST',
    body: JSON.stringify({
      client_id: state.syncPlay.clientId,
      device_name: state.syncPlay.deviceName,
      player_state: getPlayerState()
    })
  }).catch(() => {});

  // Poll every 1 second
  setInterval(async () => {
    try {
      const res = await apiFetch('/api/sync/state');
      if (res && res.active !== undefined) handleSyncState(res);
    } catch (e) { /* ignore polling errors */ }

    // Heartbeat ping
    apiFetch('/api/sync/ping', {
      method: 'POST',
      body: JSON.stringify({
        client_id: state.syncPlay.clientId,
        device_name: state.syncPlay.deviceName,
        player_state: getPlayerState()
      })
    }).catch(() => {});
  }, 1000);
}

function getPlayerState() {
  if (!state.syncPlay.active) return 'IDLE';
  
  let media = null;
  if (state.syncPlay.media_type === 'video') {
    media = document.getElementById('native-video-el');
  } else if (state.syncPlay.media_type === 'audio') {
    media = globalAudio;
  }
  
  if (!media || !media.src) return 'IDLE';

  const overlay = document.getElementById('autoplay-overlay');
  if (overlay && !overlay.classList.contains('hidden')) return 'BLOCKED';
  
  if (media.readyState < 3) return 'BUFFERING';
  
  return media.paused ? 'PAUSED' : 'PLAYING';
}

function handleSyncState(newState) {
  const wasActive = state.syncPlay.active;
  const oldFileIdx = state.syncPlay.file_idx;

  state.syncPlay.active    = newState.active;
  state.syncPlay.file_idx  = newState.file_idx;
  state.syncPlay.media_type= newState.media_type;
  state.syncPlay.file_name = newState.file_name;
  state.syncPlay.state     = newState.state;
  state.syncPlay.time      = newState.time;
  state.syncPlay.last_update = newState.last_update;
  state.syncPlay.clients   = newState.clients || [];

  const isSynced = state.syncPlay.clients.some(
    c => c.id === state.syncPlay.clientId && c.synced
  );
  const wasSync = state.syncPlay.isSynced;
  state.syncPlay.isSynced = isSynced;

  // Update device panel
  renderWatchPartyPanel(newState);

  if (newState.active) {
    // Auto-open file if newly synced and file changed
    if (isSynced && newState.file_idx !== null && newState.file_idx !== oldFileIdx) {
      if (state.files && state.files.length > newState.file_idx) {
        const fileToPlay = state.files[newState.file_idx];
        openPreviewModal(fileToPlay, state.files);
      }
    }

    // Apply playback sync
    if (isSynced) {
      const mediaType = newState.media_type;
      if (mediaType === 'video') {
        const video = document.getElementById('native-video-el');
        const container = document.getElementById('viewer-video-container');
        if (video && video.src && container && !container.classList.contains('hidden')) {
          applySyncToMedia(video, newState);
          applyLockMode(document.getElementById('custom-video-player'), state.syncPlay.lockMode);
        }
      } else if (mediaType === 'audio') {
        if (globalAudio && globalAudio.src) {
          applySyncToMedia(globalAudio, newState);
        }
      }
    }
  }

  // Sync banner
  const videoBanner = document.getElementById('video-sync-banner');
  const audioBanner = document.getElementById('audio-sync-banner');
  const lockIcon = document.getElementById('video-sync-lock-icon');
  const audioLockIcon = document.getElementById('audio-sync-lock-icon');

  if (videoBanner) videoBanner.classList.toggle('hidden', !(isSynced && newState.active && newState.media_type === 'video'));
  if (audioBanner) audioBanner.classList.toggle('hidden', !(isSynced && newState.active && newState.media_type === 'audio'));

  const lockText = state.syncPlay.lockMode === 'strict' ? '🔒' : '🔓';
  if (lockIcon) lockIcon.textContent = lockText;
  if (audioLockIcon) audioLockIcon.textContent = lockText;

  if (!isSynced || !newState.active) {
    // Unlock player if no longer synced
    const vp = document.getElementById('custom-video-player');
    if (vp) { vp.classList.remove('controls-locked', 'controls-locked-loose'); }
  }

  if (wasActive && !newState.active) {
    showToast('Watch Party has ended.');
  }
  if (!wasSync && isSynced && newState.active) {
    showToast('🎬 Watch Party sync active!');
  }
}

function applySyncToMedia(media, syncState) {
  const expectedTime = syncState.state === 'PLAYING'
    ? syncState.time + (Date.now() / 1000 - syncState.last_update)
    : syncState.time;

  if (Math.abs(media.currentTime - expectedTime) > 1.5) {
    media.currentTime = expectedTime;
  }
  if (syncState.state === 'PLAYING' && media.paused) {
    const p = media.play();
    if (p !== undefined) {
      p.catch((err) => {
        if (err.name === 'NotAllowedError') {
          showAutoplayOverlay(media);
        }
      });
    }
  } else if ((syncState.state === 'PAUSED' || syncState.state === 'WAITING') && !media.paused) {
    media.pause();
  }
}

function showAutoplayOverlay(media) {
  if (document.getElementById('autoplay-overlay')) return;
  const overlay = document.createElement('div');
  overlay.id = 'autoplay-overlay';
  overlay.style.position = 'fixed';
  overlay.style.top = '0';
  overlay.style.left = '0';
  overlay.style.width = '100vw';
  overlay.style.height = '100vh';
  overlay.style.background = 'rgba(0,0,0,0.85)';
  overlay.style.zIndex = '9999';
  overlay.style.display = 'flex';
  overlay.style.flexDirection = 'column';
  overlay.style.alignItems = 'center';
  overlay.style.justifyContent = 'center';
  overlay.style.color = '#fff';
  overlay.style.cursor = 'pointer';
  overlay.innerHTML = `
    <div style="font-size: 64px; margin-bottom: 16px;">▶️</div>
    <h2 style="font-family: sans-serif; margin: 0 0 8px;">Tap to Start Watch Party</h2>
    <p style="opacity: 0.7; font-family: sans-serif; margin: 0;">Browser requires interaction to play media.</p>
  `;
  overlay.onclick = () => {
    media.play().catch(()=>{});
    overlay.remove();
  };
  document.body.appendChild(overlay);
}

function applyLockMode(playerEl, mode) {
  if (!playerEl) return;
  playerEl.classList.remove('controls-locked', 'controls-locked-loose');
  if (mode === 'strict') playerEl.classList.add('controls-locked');
  else if (mode === 'loose') playerEl.classList.add('controls-locked-loose');
}

function renderWatchPartyPanel(syncData) {
  const clients = syncData.clients || [];
  const totalClients = clients.length;
  const isLive = syncData.active;

  // Update FAB badge
  const fabBadge = document.getElementById('watch-party-fab-badge');
  const tabBadge = document.getElementById('watch-party-tab-badge');
  const fabBtn = document.getElementById('watch-party-fab-btn');
  const fabContainer = document.getElementById('watch-party-fab-container');
  const tabBtn = document.getElementById('watch-party-tab-btn');

  if (totalClients > 0 || isLive) {
    if (fabContainer && state.syncPlay.panelMode === 'fab') fabContainer.classList.remove('hidden');
    if (tabBtn && state.syncPlay.panelMode === 'tab') tabBtn.classList.remove('hidden');

    if (fabBadge) {
      fabBadge.textContent = totalClients;
      fabBadge.classList.toggle('hidden', totalClients === 0);
    }
    if (tabBadge) {
      tabBadge.textContent = totalClients;
      tabBadge.classList.toggle('hidden', totalClients === 0);
    }
  }

  // Live dot on FAB
  if (fabBtn) fabBtn.classList.toggle('is-live', isLive);

  // LIVE badge
  const liveBadge = document.getElementById('wp-live-badge');
  if (liveBadge) liveBadge.classList.toggle('hidden', !isLive);

  // Now Playing
  const npEl = document.getElementById('wp-now-playing');
  const npTitle = document.getElementById('wp-np-title');
  const npIcon = document.getElementById('wp-np-icon');
  if (npEl) {
    if (isLive && syncData.file_name) {
      npEl.classList.remove('hidden');
      if (npTitle) npTitle.textContent = syncData.file_name;
      if (npIcon) npIcon.textContent = syncData.media_type === 'audio' ? '🎵' : '🎬';
    } else {
      npEl.classList.add('hidden');
    }
  }

  // Device list
  const listEl = document.getElementById('wp-device-list');
  if (!listEl) return;
  listEl.innerHTML = '';

  if (clients.length === 0) {
    listEl.innerHTML = '<div class="wp-no-devices">No devices connected</div>';
    return;
  }

  clients.forEach(client => {
    const row = document.createElement('div');
    row.className = 'wp-device-row';
    const isMe = client.id === state.syncPlay.clientId;
    const dotClass = client.synced ? 'synced' : 'connected';
    const tag = client.synced ? '<span class="wp-device-tag synced">SYNCED</span>' : '<span class="wp-device-tag watching">WATCHING</span>';
    row.innerHTML = `
      <span class="wp-device-dot ${dotClass}"></span>
      <span class="wp-device-name">${escapeHtml(client.name)}${isMe ? ' <span style="opacity:0.5;font-size:10px">(you)</span>' : ''}</span>
      ${tag}
    `;
    listEl.appendChild(row);
  });
}

function escapeHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function applyWatchPartyPanelMode(mode) {
  const fab = document.getElementById('watch-party-fab-container');
  const tab = document.getElementById('watch-party-tab-btn');
  if (fab) fab.classList.toggle('hidden', mode !== 'fab');
  if (tab) tab.classList.toggle('hidden', mode !== 'tab');
}

function initWatchPartySettings() {
  const nameInput = document.getElementById('wp-device-name-input');
  const panelSelect = document.getElementById('wp-panel-mode-select');
  const lockSelect = document.getElementById('wp-lock-mode-select');

  if (nameInput) {
    nameInput.value = state.syncPlay.deviceName;
    nameInput.addEventListener('change', () => {
      const val = nameInput.value.trim() || detectDeviceName();
      state.syncPlay.deviceName = val;
      safeStorage.setItem('wpDeviceName', val);
    });
  }
  if (panelSelect) {
    panelSelect.value = state.syncPlay.panelMode;
    panelSelect.addEventListener('change', () => {
      state.syncPlay.panelMode = panelSelect.value;
      safeStorage.setItem('wpPanelMode', panelSelect.value);
      applyWatchPartyPanelMode(panelSelect.value);
    });
  }
  if (lockSelect) {
    lockSelect.value = state.syncPlay.lockMode;
    lockSelect.addEventListener('change', () => {
      state.syncPlay.lockMode = lockSelect.value;
      safeStorage.setItem('wpLockMode', lockSelect.value);
    });
  }

  // Watch Party FAB toggle panel
  const fabBtn = document.getElementById('watch-party-fab-btn');
  const fabPanel = document.getElementById('watch-party-fab-panel');
  if (fabBtn && fabPanel) {
    fabBtn.addEventListener('click', () => {
      fabPanel.classList.toggle('hidden');
    });
    document.addEventListener('click', (e) => {
      if (!fabBtn.contains(e.target) && !fabPanel.contains(e.target)) {
        fabPanel.classList.add('hidden');
      }
    });
  }

  // Watch Party tab button → toggle FAB panel or scroll to it
  const tabBtn = document.getElementById('watch-party-tab-btn');
  if (tabBtn && fabPanel) {
    tabBtn.addEventListener('click', () => {
      fabPanel.classList.toggle('hidden');
      if (!fabPanel.classList.contains('hidden')) {
        // Temporarily show fab container without positioning constraint
        const fab = document.getElementById('watch-party-fab-container');
        if (fab) fab.classList.remove('hidden');
      }
    });
  }
}

// Detect and apply dark/light modes
function detectSystemTheme() {
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const storedTheme = safeStorage.getItem('themeMode');
  
  if (storedTheme) {
    document.body.classList.toggle('dark', storedTheme === 'dark');
    document.body.classList.toggle('light', storedTheme === 'light');
  } else {
    document.body.classList.toggle('dark', prefersDark);
    document.body.classList.toggle('light', !prefersDark);
  }
  updateThemeIcon();
}

function updateThemeIcon() {
  const icon = document.querySelector('#theme-toggle-icon use');
  if (icon) {
    if (document.body.classList.contains('dark')) {
      icon.setAttribute('href', '#icon-light-mode');
    } else {
      icon.setAttribute('href', '#icon-dark-mode');
    }
  }
}

// Custom API Fetch Helper
async function apiFetch(url, options = {}) {
  // If in mock mode, bypass backend call
  if (state.isMockMode) {
    return handleMockRequest(url, options);
  }

  // Set default authorization header
  const headers = { ...options.headers };
  if (state.sessionToken) {
    headers['Authorization'] = `Bearer ${state.sessionToken}`;
  }
  options.headers = headers;

  try {
    const res = await fetch(url, options);
    
    // Handle auth failure
    if (res.status === 401) {
      safeStorage.removeItem('fluxToken', true);
      state.sessionToken = '';
      showPasswordGate();
      throw new Error("Unauthorized access");
    }

    if (!res.ok) {
      throw new Error(`HTTP error: ${res.status}`);
    }

    return await res.json();
  } catch (err) {
    console.warn("API request failed:", err);
    // If it's a connection drop/failure to fetch (not auth/http status), check connection screen
    if (err.message.includes('Failed to fetch') || err.message.includes('network')) {
      showConnectionError();
    }
    throw err;
  }
}

// Mock Request Router (Fallback)
function handleMockRequest(url, options) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (url.includes('/api/meta')) {
        resolve(MOCK_META);
      } else if (url.includes('/api/files')) {
        resolve(MOCK_FILES);
      } else if (url.includes('/api/auth')) {
        const body = JSON.parse(options.body);
        if (body.password === 'flux') {
          resolve({ token: 'mock-session-token-abc-123' });
        } else {
          reject(new Error("Invalid password"));
        }
      } else {
        reject(new Error("Endpoint not found in mock router"));
      }
    }, 400); // Shimmer simulator
  });
}

// Start loading configuration
async function loadPortalData() {
  try {
    // Try hitting API to check backend availability
    const meta = await apiFetch('/api/meta').catch(err => {
      // Fallback to mock mode if connection fails on start
      console.log("Unable to reach backend. Enabling client-side Mock Mode.");
      state.isMockMode = true;
      hideConnectionError();
      return handleMockRequest('/api/meta');
    });

    state.meta = meta;
    applyThemeTone(meta.theme_tone);

    if (meta.password_protected && !state.sessionToken) {
      showPasswordGate();
    } else {
      hidePasswordGate();
      await fetchFiles();
    }
  } catch (err) {
    console.error("Initialization failed:", err);
  }
}

// Apply theme custom properties
function applyThemeTone(tone) {
  // Clear any theme class first
  document.body.classList.remove('theme-purple', 'theme-rose', 'theme-orange', 'theme-breeze');
  
  let themeClass = 'theme-purple';
  if (tone) {
    const cleanTone = tone.toLowerCase();
    if (cleanTone.includes('purple')) themeClass = 'theme-purple';
    else if (cleanTone.includes('rose') || cleanTone.includes('crimson')) themeClass = 'theme-rose';
    else if (cleanTone.includes('orange') || cleanTone.includes('sunset')) themeClass = 'theme-orange';
    else if (cleanTone.includes('breeze') || cleanTone.includes('indigo')) themeClass = 'theme-breeze';
  }
  document.body.classList.add(themeClass);
  
  // Set UI elements in Header
  if (state.meta) {
    document.getElementById('profile-name').textContent = state.meta.profile_name || "FluxMedia Share";
    if (state.meta.profile_image_url) {
      document.getElementById('profile-avatar').src = state.meta.profile_image_url;
    }
  }
}

function applyCustomHue(hexColor) {
  let r = 0, g = 0, b = 0;
  if (hexColor.length == 4) {
    r = parseInt(hexColor[1] + hexColor[1], 16);
    g = parseInt(hexColor[2] + hexColor[2], 16);
    b = parseInt(hexColor[3] + hexColor[3], 16);
  } else if (hexColor.length == 7) {
    r = parseInt(hexColor[1] + hexColor[2], 16);
    g = parseInt(hexColor[3] + hexColor[4], 16);
    b = parseInt(hexColor[5] + hexColor[6], 16);
  }
  r /= 255; g /= 255; b /= 255;
  let cmin = Math.min(r,g,b), cmax = Math.max(r,g,b), delta = cmax - cmin, h = 0;
  if (delta == 0) h = 0;
  else if (cmax == r) h = ((g - b) / delta) % 6;
  else if (cmax == g) h = (b - r) / delta + 2;
  else h = (r - g) / delta + 4;
  h = Math.round(h * 60);
  if (h < 0) h += 360;

  let styleEl = document.getElementById('custom-theme-style');
  if (!styleEl) {
    styleEl = document.createElement('style');
    styleEl.id = 'custom-theme-style';
    document.head.appendChild(styleEl);
  }

  styleEl.textContent = `
    body.theme-custom.light {
      --md-sys-color-primary: hsl(${h}, 50%, 40%);
      --md-sys-color-on-primary: hsl(0, 0%, 100%);
      --md-sys-color-primary-container: hsl(${h}, 70%, 90%);
      --md-sys-color-on-primary-container: hsl(${h}, 90%, 15%);
      --md-sys-color-secondary: hsl(${h}, 15%, 45%);
      --md-sys-color-on-secondary: hsl(0, 0%, 100%);
      --md-sys-color-secondary-container: hsl(${h}, 20%, 90%);
      --md-sys-color-on-secondary-container: hsl(${h}, 40%, 15%);
      --md-sys-color-background: hsl(${h}, 20%, 98%);
      --md-sys-color-on-background: hsl(${h}, 30%, 10%);
      --md-sys-color-surface: hsl(${h}, 15%, 98%);
      --md-sys-color-on-surface: hsl(${h}, 30%, 10%);
      --md-sys-color-surface-variant: hsl(${h}, 15%, 92%);
      --md-sys-color-on-surface-variant: hsl(${h}, 20%, 30%);
      --md-sys-color-outline: hsl(${h}, 10%, 50%);
      --md-sys-color-outline-variant: hsl(${h}, 15%, 85%);
      --md-sys-color-surface-container-lowest: hsl(0, 0%, 100%);
      --md-sys-color-surface-container-low: hsl(${h}, 15%, 96%);
      --md-sys-color-surface-container: hsl(${h}, 15%, 94%);
      --md-sys-color-surface-container-high: hsl(${h}, 15%, 92%);
      --md-sys-color-surface-container-highest: hsl(${h}, 15%, 90%);
    }
    body.theme-custom.dark {
      --md-sys-color-primary: hsl(${h}, 70%, 75%);
      --md-sys-color-on-primary: hsl(${h}, 100%, 20%);
      --md-sys-color-primary-container: hsl(${h}, 50%, 30%);
      --md-sys-color-on-primary-container: hsl(${h}, 80%, 90%);
      --md-sys-color-secondary: hsl(${h}, 20%, 75%);
      --md-sys-color-on-secondary: hsl(${h}, 30%, 20%);
      --md-sys-color-secondary-container: hsl(${h}, 20%, 30%);
      --md-sys-color-on-secondary-container: hsl(${h}, 30%, 90%);
      --md-sys-color-background: hsl(${h}, 15%, 10%);
      --md-sys-color-on-background: hsl(${h}, 20%, 90%);
      --md-sys-color-surface: hsl(${h}, 10%, 12%);
      --md-sys-color-on-surface: hsl(${h}, 20%, 90%);
      --md-sys-color-surface-variant: hsl(${h}, 15%, 25%);
      --md-sys-color-on-surface-variant: hsl(${h}, 20%, 80%);
      --md-sys-color-outline: hsl(${h}, 10%, 60%);
      --md-sys-color-outline-variant: hsl(${h}, 15%, 30%);
      --md-sys-color-surface-container-lowest: hsl(${h}, 10%, 5%);
      --md-sys-color-surface-container-low: hsl(${h}, 10%, 10%);
      --md-sys-color-surface-container: hsl(${h}, 10%, 15%);
      --md-sys-color-surface-container-high: hsl(${h}, 10%, 20%);
      --md-sys-color-surface-container-highest: hsl(${h}, 10%, 25%);
    }
  `;

  document.body.classList.remove('theme-purple', 'theme-rose', 'theme-orange', 'theme-breeze');
  document.body.classList.add('theme-custom');
  safeStorage.setItem('customThemeColor', hexColor);
}

// Handle Password Gate UI
function showPasswordGate() {
  document.getElementById('password-gate').classList.remove('hidden');
  document.getElementById('app-container').classList.add('hidden');
}

function hidePasswordGate() {
  document.getElementById('password-gate').classList.add('hidden');
  document.getElementById('app-container').classList.remove('hidden');
}

// Fetch Files and metadata
async function fetchFiles() {
  showSkeletons();
  try {
    const files = await apiFetch('/api/files');
    state.files = files;
    renderFileDisplay();
    calculateStats();
  } catch (err) {
    console.error("Failed to fetch files:", err);
  } finally {
    hideSkeletons();
  }
}

function showSkeletons() {
  document.getElementById('skeleton-grid').classList.remove('hidden');
  document.getElementById('files-grid-container').classList.add('hidden');
  document.getElementById('empty-state').classList.add('hidden');
}

function hideSkeletons() {
  document.getElementById('skeleton-grid').classList.add('hidden');
}

// Render dynamic stats pill
function calculateStats() {
  const count = state.files.length;
  let totalBytes = 0;
  state.files.forEach(f => totalBytes += f.size || 0);

  let sizeStr = '';
  if (totalBytes < 1024 * 1024) {
    sizeStr = (totalBytes / 1024).toFixed(1) + ' KB';
  } else if (totalBytes < 1024 * 1024 * 1024) {
    sizeStr = (totalBytes / (1024 * 1024)).toFixed(1) + ' MB';
  } else {
    sizeStr = (totalBytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  }

  document.getElementById('status-pill').textContent = `${count} files · ${sizeStr}`;
}

// Formatting helpers
function formatSize(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDuration(sec) {
  if (!sec) return '';
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  } else {
    return `${m}:${s.toString().padStart(2, '0')}`;
  }
}

// URL builder including authentication token query param
function getStreamUrl(fileId) {
  if (state.isMockMode) {
    // Generate dummy preview files for native player checking
    if (fileId.startsWith('vid-')) return "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4";
    if (fileId.startsWith('aud-')) return "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3";
    if (fileId === 'doc-1') return "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf";
    return "";
  }
  const base = `/api/file/${fileId}`;
  return state.sessionToken ? `${base}?token=${encodeURIComponent(state.sessionToken)}` : base;
}

function getThumbnailUrl(file) {
  if (state.isMockMode || !file.thumbnail_url) {
    // Return empty to invoke fallback SVG layout
    return "";
  }
  const base = `/api/thumbnail/${file.id}`;
  return state.sessionToken ? `${base}?token=${encodeURIComponent(state.sessionToken)}` : base;
}

// ==========================================================================
// RENDER CONTROLLER (GRID & LIST VIEWPORTS)
// ==========================================================================
function renderFileDisplay() {
  const container = document.getElementById('files-grid-container');
  container.innerHTML = '';

  // Apply visual layout structure
  container.className = `files-grid ${state.viewMode === 'list' ? 'list-view-mode' : ''}`;

  // Apply Filter
  let filtered = state.files.filter(f => {
    if (state.activeFilter === 'all') return true;
    return f.type.toLowerCase() === state.activeFilter;
  });

  // Apply Search (Case insensitive matching)
  if (state.searchQuery.trim()) {
    const q = state.searchQuery.toLowerCase();
    filtered = filtered.filter(f => {
      const searchStr = `${f.name} ${f.type} ${formatSize(f.size)} ${f.duration ? formatDuration(f.duration) : ''} ${new Date(f.added_at).toLocaleString()}`.toLowerCase();
      return searchStr.includes(q);
    });
  }

  // Sort logic
  filtered.sort((a, b) => {
    let comp = 0;
    const [field, dir] = state.sortOption.split('-');
    
    if (field === 'name') {
      comp = a.name.localeCompare(b.name);
    } else if (field === 'added') {
      comp = new Date(a.added_at) - new Date(b.added_at);
    } else if (field === 'size') {
      comp = a.size - b.size;
    }
    return dir === 'desc' ? -comp : comp;
  });

  // Show Empty State if no hits
  if (filtered.length === 0) {
    container.classList.add('hidden');
    document.getElementById('empty-state').classList.remove('hidden');
    return;
  }

  document.getElementById('empty-state').classList.add('hidden');
  container.classList.remove('hidden');

  // Render cards
  filtered.forEach((file, index) => {
    const card = createFileCard(file, index, filtered);
    container.appendChild(card);
  });
}

function createFileCard(file, index, currentSet) {
  const card = document.createElement('div');
  card.className = `file-card ${state.selectedFiles.has(file.id) ? 'selected' : ''}`;
  card.dataset.id = file.id;

  // Choose file icon identifier
  let iconId = '#icon-other';
  if (file.type === 'video') iconId = '#icon-video';
  else if (file.type === 'audio') iconId = '#icon-audio';
  else if (file.type === 'image') iconId = '#icon-image';
  else if (file.type === 'document') iconId = '#icon-document';

  // Thumbnail markup
  const thumbUrl = getThumbnailUrl(file);
  const thumbContent = thumbUrl 
    ? `<img class="file-card-thumb" src="${thumbUrl}" alt="${file.name}" loading="lazy">`
    : `<svg class="file-card-placeholder-icon"><use href="${iconId}"></use></svg>`;

  const durationBadge = file.duration 
    ? `<span class="file-card-duration-badge">${formatDuration(file.duration)}</span>` 
    : '';

  card.innerHTML = `
    <div class="file-card-checkbox">
      <svg viewBox="0 0 24 24"><use href="#icon-check"></use></svg>
    </div>
    <div class="file-card-thumb-container">
      ${thumbContent}
      ${durationBadge}
    </div>
    <div class="file-card-details">
      <div class="file-card-info">
        <h3 class="file-card-name m3-title-small text-ellipsis" title="${file.name}">${file.name}</h3>
        <div class="file-card-subinfo m3-label-medium">
          <span class="file-card-type-badge">${file.type}</span>
          <span>·</span>
          <span>${formatSize(file.size)}</span>
        </div>
      </div>
      <button class="file-card-download-btn" aria-label="Download ${file.name}" data-action="download">
        <svg><use href="#icon-download"></use></svg>
      </button>
    </div>
  `;

  // --- Click Events ---
  
  // Mobile Long Press Setup
  let pressTimer;
  const startPress = () => {
    pressTimer = setTimeout(() => {
      toggleSelection(file.id);
    }, 600);
  };
  const endPress = () => {
    clearTimeout(pressTimer);
  };

  card.addEventListener('mousedown', startPress);
  card.addEventListener('touchstart', startPress, { passive: true });
  card.addEventListener('touchmove', endPress, { passive: true });
  card.addEventListener('mouseup', endPress);
  card.addEventListener('mouseleave', endPress);
  card.addEventListener('touchend', endPress);
  card.addEventListener('touchcancel', endPress);

  card.addEventListener('click', (e) => {
    // Prevent trigger when clicking inner actions
    if (e.target.closest('[data-action="download"]')) {
      e.stopPropagation();
      downloadSingleFile(file);
      return;
    }
    if (e.target.closest('.file-card-checkbox')) {
      e.stopPropagation();
      toggleSelection(file.id);
      return;
    }

    // In Multi-select mode, clicks toggle selection instead of previewing
    if (state.selectedFiles.size > 0) {
      toggleSelection(file.id);
    } else {
      openPreviewModal(file, currentSet);
    }
  });

  return card;
}

// ==========================================================================
// SELECTION & DOWNLOAD STATE ACTIONS
// ==========================================================================
function toggleSelection(fileId) {
  if (state.selectedFiles.has(fileId)) {
    state.selectedFiles.delete(fileId);
  } else {
    state.selectedFiles.add(fileId);
  }

  updateSelectionBar();
  renderFileDisplay();
}

function updateSelectionBar() {
  const bar = document.getElementById('selection-bar');
  const header = document.getElementById('selection-header');
  const count = state.selectedFiles.size;

  if (count > 0) {
    document.body.classList.add('select-mode');
    bar.classList.remove('hidden');
    header.classList.remove('hidden');
    document.getElementById('selection-count').textContent = `${count} selected`;
    document.getElementById('selection-bar-count').textContent = `${count} files selected`;
  } else {
    document.body.classList.remove('select-mode');
    bar.classList.add('hidden');
    header.classList.add('hidden');
  }
}

function selectAllFiltered() {
  let filtered = state.files.filter(f => {
    if (state.activeFilter === 'all') return true;
    return f.type.toLowerCase() === state.activeFilter;
  });
  if (state.searchQuery.trim()) {
    const q = state.searchQuery.toLowerCase();
    filtered = filtered.filter(f => f.name.toLowerCase().includes(q));
  }

  filtered.forEach(f => state.selectedFiles.add(f.id));
  updateSelectionBar();
  renderFileDisplay();
}

function clearSelection() {
  state.selectedFiles.clear();
  updateSelectionBar();
  renderFileDisplay();
}

// Download Trigger Helpers
function downloadSingleFile(file) {
  showToast(`Downloading: ${file.name}`);
  const url = getStreamUrl(file.id);
  const a = document.createElement('a');
  a.href = url;
  a.download = file.name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// Batch Sequential Downloads
async function downloadSelected() {
  const fileIds = Array.from(state.selectedFiles);
  showToast(`Starting sequential download of ${fileIds.length} files...`);
  
  for (let i = 0; i < fileIds.length; i++) {
    const file = state.files.find(f => f.id === fileIds[i]);
    if (file) {
      downloadSingleFile(file);
      // Small cooling timeout to avoid browser blockages
      await new Promise(r => setTimeout(r, 600));
    }
  }
  clearSelection();
}

// ==========================================================================
// VLC / EXTERNAL PLAYER INTEGRATION
// ==========================================================================

/**
 * Open a file stream in VLC by downloading an M3U playlist.
 * Also copies the direct stream URL to clipboard for manual use.
 */
function openInVLC(file) {
  const streamPath = getStreamUrl(file.id);
  const fullUrl = window.location.origin + streamPath;
  const vlcUrl = "vlc://" + window.location.host + streamPath;

  // Attempt to launch VLC directly via deep link
  window.location.href = vlcUrl;

  // Build M3U playlist text
  const m3uContent = `#EXTM3U\n#EXTINF:-1,${file.name}\n${fullUrl}\n`;
  const blob = new Blob([m3uContent], { type: 'audio/x-mpegurl' });
  const blobUrl = URL.createObjectURL(blob);

  // Trigger download of the .m3u file
  const anchor = document.createElement('a');
  anchor.href = blobUrl;
  anchor.download = file.name.replace(/\.[^.]+$/, '') + '.m3u';
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(blobUrl);

  // Also copy URL to clipboard so user can paste in VLC if needed
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(fullUrl)
      .then(() => showToast('Opening VLC... Playlist downloaded & URL copied as fallback!'))
      .catch(() => showToast('Opening VLC... Playlist downloaded as fallback.'));
  } else {
    showToast('Opening VLC... Playlist downloaded as fallback.');
  }
}

// ==========================================================================
// TEXT FILE VIEWER
// ==========================================================================

/** File extensions that can be rendered as plain text inline */
const TEXT_VIEWABLE_EXTS = new Set([
  'txt','log','md','csv','json','xml','yaml','yml',
  'ini','cfg','conf','py','js','ts','jsx','tsx',
  'html','htm','css','scss','sh','bat','cmd',
  'sql','toml','gitignore','env','nfo','srt','vtt'
]);

function isTextViewable(filename) {
  const ext = (filename.split('.').pop() || '').toLowerCase();
  return TEXT_VIEWABLE_EXTS.has(ext);
}

function setupTextViewer(file) {
  const container = document.getElementById('viewer-document-container');
  container.classList.remove('hidden');

  const frameContainer = document.getElementById('document-frame-container');

  // Show loading state
  frameContainer.innerHTML = `
    <div class="text-viewer-loading">
      <span>Loading ${file.name}…</span>
    </div>
  `;

  const streamUrl = getStreamUrl(file.id);

  fetch(streamUrl)
    .then(resp => {
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return resp.text();
    })
    .then(text => {
      frameContainer.innerHTML = '';
      const wrapper = document.createElement('div');
      wrapper.className = 'text-viewer-container';
      const pre = document.createElement('pre');
      pre.className = 'text-viewer-pre';
      pre.textContent = text;
      wrapper.appendChild(pre);
      frameContainer.appendChild(wrapper);
    })
    .catch(err => {
      console.error('Text viewer fetch failed:', err);
      container.classList.add('hidden');
      setupFallbackViewer(file);
    });
}

// ==========================================================================
// PREVIEW MODAL VIEWER SYSTEM
// ==========================================================================
let activeSetForModal = [];

function openPreviewModal(file, currentSet) {
  activeSetForModal = currentSet || state.files;
  state.activeFileIndex = activeSetForModal.findIndex(f => f.id === file.id);

  const modal = document.getElementById('viewer-modal');
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden'; // Lock scrolling

  // Setup Header Details
  document.getElementById('modal-title').textContent = file.name;
  document.getElementById('modal-meta').textContent = `${file.type.toUpperCase()} · ${formatSize(file.size)}`;

  // Bind top download button
  document.getElementById('modal-download-btn').onclick = () => downloadSingleFile(file);

  // Clear previous previews
  const containers = document.querySelectorAll('.viewer-container');
  containers.forEach(c => c.classList.add('hidden'));

  // Reset image transforms
  resetImageZoom();

  // Route file types
  switch (file.type) {
    case 'video':
      setupVideoPlayer(file);
      break;
    case 'audio':
      setupAudioPlayer(file);
      break;
    case 'image':
      setupImageLightbox(file);
      break;
    case 'document':
      setupDocumentViewer(file);
      break;
    default:
      // Check if it's a text-renderable file even if categorized as "other"
      if (isTextViewable(file.name)) {
        setupTextViewer(file);
      } else {
        setupFallbackViewer(file);
      }
  }

  // Show/hide VLC button — only for video and audio
  const vlcBtn = document.getElementById('modal-vlc-btn');
  if (vlcBtn) {
    if (file.type === 'video' || file.type === 'audio') {
      vlcBtn.classList.remove('hidden');
      vlcBtn.onclick = () => openInVLC(file);
    } else {
      vlcBtn.classList.add('hidden');
      vlcBtn.onclick = null;
    }
  }
}

function closePreviewModal() {
  const modal = document.getElementById('viewer-modal');
  modal.classList.add('hidden');
  document.body.style.overflow = ''; // Unlock scrolling

  // Pause video element
  const video = document.getElementById('native-video-el');
  video.pause();
  video.src = '';
  video.load();

  // If audio is playing inside the modal, continue in bottom mini-player!
  if (state.currentPlayingAudioId && !globalAudio.paused) {
    showMiniAudioPlayer();
  } else {
    // If not playing, ensure hidden
    hideMiniAudioPlayer();
  }
}

// Next / Previous Navigation (Keyboard & Button support)
function navigateModal(offset) {
  if (activeSetForModal.length <= 1) return;
  
  // Pause current players
  const video = document.getElementById('native-video-el');
  video.pause();

  let nextIndex = state.activeFileIndex + offset;
  if (nextIndex >= activeSetForModal.length) nextIndex = 0;
  if (nextIndex < 0) nextIndex = activeSetForModal.length - 1;

  openPreviewModal(activeSetForModal[nextIndex], activeSetForModal);
}

// ==========================================================================
// CUSTOM MEDIA PLAYER LOGIC (VIDEO)
// ==========================================================================
function setupVideoPlayer(file) {
  const container = document.getElementById('viewer-video-container');
  container.classList.remove('hidden');

  const video = document.getElementById('native-video-el');
  const streamUrl = getStreamUrl(file.id);
  video.src = streamUrl;

  // Setup Subtitles
  Array.from(video.querySelectorAll('track')).forEach(t => t.remove()); // Clear previous tracks
  const ccBtn = document.getElementById('video-cc-btn');
  if (ccBtn) {
    ccBtn.classList.add('hidden'); // Default hidden
    ccBtn.style.color = '';
    // Reset click handler
    ccBtn.onclick = null;
  }
  
  fetch(`/api/subtitles/${file.id}`, { method: 'HEAD' })
    .then(res => {
      if (res.ok && ccBtn) {
        ccBtn.classList.remove('hidden');
        const track = document.createElement('track');
        track.src = `/api/subtitles/${file.id}`;
        track.kind = 'subtitles';
        track.srclang = 'en';
        track.label = 'English';
        track.default = false; 
        video.appendChild(track);
        
        let subtitlesOn = false;
        ccBtn.onclick = () => {
          subtitlesOn = !subtitlesOn;
          if (video.textTracks && video.textTracks[0]) {
             video.textTracks[0].mode = subtitlesOn ? 'showing' : 'hidden';
          }
          ccBtn.style.color = subtitlesOn ? 'var(--primary)' : '';
        };
      }
    })
    .catch(err => console.log('No subtitles found'));


  const playBtn = document.getElementById('video-play-btn');
  const centerPlay = document.getElementById('video-center-play');
  const volumeBtn = document.getElementById('video-volume-btn');
  const volumeSlider = document.getElementById('video-volume-slider');
  const progressFill = document.getElementById('video-timeline-progress');
  const bufferFill = document.getElementById('video-timeline-buffer');
  const handle = document.getElementById('video-timeline-handle');
  const curTimeText = document.getElementById('video-current-time');
  const durTimeText = document.getElementById('video-duration');
  const customPlayer = document.getElementById('custom-video-player');

  video.load();
  video.play().catch(() => {
    // Autoplay blocked fallback
    updatePlayIcon(true);
  });

  // Time Updates
  video.ontimeupdate = () => {
    const cur = video.currentTime;
    const dur = video.duration || 0;
    
    // Save watch history
    safeStorage.setItem(`video-progress-${file.id}`, cur);

    curTimeText.textContent = formatDuration(cur) || '0:00';
    durTimeText.textContent = formatDuration(dur) || '0:00';

    if (dur > 0) {
      const pct = (cur / dur) * 100;
      progressFill.style.width = `${pct}%`;
      handle.style.left = `${pct}%`;
    }

    // Update buffer progress bar
    if (video.buffered.length > 0) {
      const bufferedEnd = video.buffered.end(video.buffered.length - 1);
      if (dur > 0) {
        bufferFill.style.width = `${(bufferedEnd / dur) * 100}%`;
      }
    }
  };

  video.onloadedmetadata = () => {
    durTimeText.textContent = formatDuration(video.duration);
    
    // Restore watch history
    const savedTime = parseFloat(safeStorage.getItem(`video-progress-${file.id}`));
    if (!isNaN(savedTime) && savedTime > 0 && savedTime < video.duration) {
      video.currentTime = savedTime;
    }
  };

  // Play controls
  const togglePlay = () => {
    if (video.paused) {
      // Pause any background audio
      globalAudio.pause();
      hideMiniAudioPlayer();
      
      video.play();
      updatePlayIcon(false);
    } else {
      video.pause();
      updatePlayIcon(true);
    }
  };

  const updatePlayIcon = (isPaused) => {
    const playSvg = `<svg><use href="#icon-play"></use></svg>`;
    const pauseSvg = `<svg><use href="#icon-pause"></use></svg>`;
    playBtn.innerHTML = isPaused ? playSvg : pauseSvg;
    centerPlay.innerHTML = isPaused ? `<svg class="center-play-icon"><use href="#icon-play"></use></svg>` : `<svg class="center-play-icon"><use href="#icon-pause"></use></svg>`;
    
    // Hide center button visual quickly if playing
    if (!isPaused) {
      centerPlay.style.opacity = '0';
      setTimeout(() => centerPlay.removeAttribute('style'), 1000);
    }
  };

  playBtn.onclick = togglePlay;
  centerPlay.onclick = togglePlay;
  video.onclick = togglePlay;
  
  video.ondblclick = (e) => {
    const rect = video.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    if (clickX > rect.width / 2) {
      video.currentTime += 10;
    } else {
      video.currentTime -= 10;
    }
  };

  // Video ended handling
  video.onended = () => {
    updatePlayIcon(true);
    
    // Auto-play Next logic
    if (state.playlist && state.playlist.length > 0) {
      const currentIdx = state.playlist.findIndex(item => item.id === file.id);
      if (currentIdx !== -1 && currentIdx < state.playlist.length - 1) {
        const nextItem = state.playlist[currentIdx + 1];
        const nextFileIdx = state.files.findIndex(f => f.id === nextItem.id);
        if (nextFileIdx !== -1) {
          openPreviewModal(nextItem.id, nextFileIdx);
        }
      }
    } else {
      // Auto-play next in current view
      if (state.activeFileIndex !== -1 && state.activeFileIndex < state.files.length - 1) {
        const nextFile = state.files[state.activeFileIndex + 1];
        if (nextFile.type === 'video' || nextFile.type === 'audio') {
          openPreviewModal(nextFile.id, state.activeFileIndex + 1);
        }
      }
    }
  };

  // Volume
  const updateVolume = () => {
    video.volume = volumeSlider.value;
    video.muted = (video.volume === 0);
    safeStorage.setItem('flux-vol', video.volume);
    
    if (video.muted) {
      volumeBtn.innerHTML = `<svg><use href="#icon-volume-off"></use></svg>`;
    } else {
      volumeBtn.innerHTML = `<svg><use href="#icon-volume-up"></use></svg>`;
    }
  };

  // Restore volume
  const savedVol = parseFloat(safeStorage.getItem('flux-vol'));
  if (!isNaN(savedVol)) {
    video.volume = savedVol;
    volumeSlider.value = savedVol;
  }
  updateVolume();

  volumeSlider.oninput = updateVolume;
  volumeBtn.onclick = () => {
    video.muted = !video.muted;
    if (video.muted) {
      volumeBtn.innerHTML = `<svg><use href="#icon-volume-off"></use></svg>`;
      volumeSlider.value = 0;
    } else {
      volumeBtn.innerHTML = `<svg><use href="#icon-volume-up"></use></svg>`;
      volumeSlider.value = video.volume || 1;
    }
  };

  // Scrubber seeking
  const timeline = document.getElementById('video-timeline-container');
  const hoverTime = document.getElementById('video-hover-time');

  timeline.onmousemove = (e) => {
    const rect = timeline.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const hoverSec = pct * (video.duration || 0);
    
    hoverTime.textContent = formatDuration(hoverSec);
    hoverTime.style.left = `${pct * 100}%`;
  };

  timeline.onclick = (e) => {
    const rect = timeline.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    video.currentTime = pct * video.duration;
  };

  // Fullscreen support
  const fsBtn = document.getElementById('video-fullscreen-btn');
  fsBtn.onclick = () => {
    if (!document.fullscreenElement) {
      customPlayer.requestFullscreen().catch(err => {
        showToast("Fullscreen not supported");
      });
      fsBtn.innerHTML = `<svg><use href="#icon-fullscreen-exit"></use></svg>`;
    } else {
      document.exitFullscreen();
      fsBtn.innerHTML = `<svg><use href="#icon-fullscreen"></use></svg>`;
    }
  };

  // Picture in Picture
  const pipBtn = document.getElementById('video-pip-btn');
  if (document.pictureInPictureEnabled) {
    pipBtn.classList.remove('hidden');
    pipBtn.onclick = () => {
      if (document.pictureInPictureElement) {
        document.exitPictureInPicture();
      } else {
        video.requestPictureInPicture();
      }
    };
  } else {
    pipBtn.classList.add('hidden');
  }

  // Casting (Remote Playback API)
  const castBtn = document.getElementById('video-cast-btn');
  if (video.remote && video.remote.state !== 'disconnected') {
    // If it's supported, we show it (note: some browsers only populate 'remote' when devices are found)
    castBtn.classList.remove('hidden');
    
    const updateCastIcon = () => {
      if (video.remote.state === 'connected') {
        castBtn.style.color = 'var(--primary)'; // highlight when connected
      } else {
        castBtn.style.color = ''; 
      }
    };
    
    video.remote.addEventListener('connect', updateCastIcon);
    video.remote.addEventListener('disconnect', updateCastIcon);
    
    castBtn.onclick = () => {
      video.remote.prompt().catch(err => {
        showToast("Casting prompt failed or cancelled");
      });
    };
  } else if (video.remote) {
      // In many cases, state is 'disconnected' initially, but we can still prompt
      castBtn.classList.remove('hidden');
      castBtn.onclick = () => {
          video.remote.prompt().catch(err => {
              showToast("No cast devices found or prompt cancelled");
          });
      };
  } else {
    castBtn.classList.add('hidden'); // Not supported
  }

  // Speed selection
  const speedBtn = document.getElementById('video-speed-btn');
  const speedMenu = document.getElementById('video-speed-menu');
  speedBtn.onclick = (e) => {
    e.stopPropagation();
    speedMenu.classList.toggle('hidden');
  };
  
  // Speed scrolling (0.1x to 8x)
  speedBtn.onwheel = (e) => {
    e.preventDefault();
    let currentSpeed = video.playbackRate;
    if (e.deltaY < 0) {
      currentSpeed += 0.1;
    } else {
      currentSpeed -= 0.1;
    }
    // Clamp between 0.1x and 8.0x
    currentSpeed = Math.max(0.1, Math.min(8.0, currentSpeed));
    // Round to 1 decimal place to avoid float precision issues
    currentSpeed = Math.round(currentSpeed * 10) / 10;
    
    video.playbackRate = currentSpeed;
    safeStorage.setItem('flux-speed', currentSpeed);
    
    // Update tooltip or indicator if desired
    speedBtn.title = `${currentSpeed}x`;
    showToast(`Playback speed: ${currentSpeed}x`);
  };

  speedMenu.onclick = (e) => {
    if (e.target.tagName === 'LI') {
      const speed = parseFloat(e.target.dataset.speed);
      video.playbackRate = speed;
      safeStorage.setItem('flux-speed', speed);
      speedBtn.title = `${speed}x`;
      
      Array.from(speedMenu.children).forEach(el => el.classList.remove('active'));
      e.target.classList.add('active');
      speedMenu.classList.add('hidden');
      showToast(`Playback speed: ${speed}x`);
    }
  };

  // Restore speed
  let savedSpeed = parseFloat(safeStorage.getItem('flux-speed'));
  if (isNaN(savedSpeed)) {
    savedSpeed = 1.0;
  }
  video.playbackRate = savedSpeed;
  speedBtn.title = `${savedSpeed}x`;
  // Update menu active state if it matches a preset
  Array.from(speedMenu.children).forEach(el => {
    if (parseFloat(el.dataset.speed) === savedSpeed) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });

  document.addEventListener('click', () => {
    speedMenu.classList.add('hidden');
  });

  // Touch controls reveal overlay
  let overlayTimer;
  const showControls = () => {
    customPlayer.classList.add('controls-active');
    clearTimeout(overlayTimer);
    overlayTimer = setTimeout(() => {
      customPlayer.classList.remove('controls-active');
    }, 2500);
  };

  video.addEventListener('mousemove', showControls);
  video.addEventListener('touchstart', showControls, { passive: true });
}

// ==========================================================================
// PERSISTENT DOCKED AUDIO PLAYER LOGIC
// ==========================================================================
function setupAudioPlayer(file) {
  const container = document.getElementById('viewer-audio-container');
  container.classList.remove('hidden');

  const modalPlayer = document.querySelector('.custom-audio-player-modal');
  modalPlayer.classList.remove('playing');

  // Sync state metadata
  const streamUrl = getStreamUrl(file.id);
  
  // If this audio track is not already loaded in the global player, load it!
  if (state.currentPlayingAudioId !== file.id) {
    globalAudio.src = streamUrl;
    globalAudio.load();
    state.currentPlayingAudioId = file.id;
  }

  // Update Cover
  const coverUrl = getThumbnailUrl(file);
  const defaultArt = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236750A4'%3E%3Cpath d='M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z'/%3E%3C/svg%3E`;
  document.getElementById('audio-large-cover').src = coverUrl || defaultArt;

  // Bind control nodes
  const playBtn = document.getElementById('audio-play-btn');
  const playIcon = document.getElementById('audio-play-icon');
  const progressFill = document.getElementById('audio-timeline-progress');
  const handle = document.getElementById('audio-timeline-handle');
  const curText = document.getElementById('audio-current-time');
  const durText = document.getElementById('audio-duration');
  const volSlider = document.getElementById('audio-volume-slider');
  const volBtn = document.getElementById('audio-volume-btn');

  // Load Metadata triggers
  durText.textContent = formatDuration(file.duration) || '--:--';

  const updatePlayStateUI = () => {
    const isPaused = globalAudio.paused;
    modalPlayer.classList.toggle('playing', !isPaused);
    playIcon.setAttribute('href', isPaused ? '#icon-play' : '#icon-pause');
    
    // Sync mini-player UI if active
    syncMiniAudioPlayerUI();
  };

  globalAudio.onplay = updatePlayStateUI;
  globalAudio.onpause = updatePlayStateUI;
  globalAudio.onended = () => {
    updatePlayStateUI();
    // Play next song in active playlist automatically if available
    navigateModal(1);
  };

  // Immediate Play
  globalAudio.play().catch(() => {
    updatePlayStateUI();
  });

  // Timeline tracking
  globalAudio.ontimeupdate = () => {
    const cur = globalAudio.currentTime;
    const dur = globalAudio.duration || file.duration || 0;
    
    curText.textContent = formatDuration(cur);
    durText.textContent = formatDuration(dur);

    if (dur > 0) {
      const pct = (cur / dur) * 100;
      progressFill.style.width = `${pct}%`;
      handle.style.left = `${pct}%`;
    }
  };

  playBtn.onclick = () => {
    if (globalAudio.paused) {
      globalAudio.play();
    } else {
      globalAudio.pause();
    }
  };

  // Skip buttons
  document.getElementById('audio-prev-btn').onclick = () => navigateModal(-1);
  document.getElementById('audio-next-btn').onclick = () => navigateModal(1);

  // Seeking Scrubber click
  const scrubber = document.getElementById('audio-timeline-slider');
  scrubber.onclick = (e) => {
    const rect = scrubber.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const targetTime = pct * (globalAudio.duration || file.duration || 0);
    globalAudio.currentTime = targetTime;
  };

  // Volume
  volSlider.value = globalAudio.volume;
  volSlider.oninput = () => {
    globalAudio.volume = volSlider.value;
    globalAudio.muted = (globalAudio.volume === 0);
    volBtn.querySelector('use').setAttribute('href', globalAudio.muted ? '#icon-volume-off' : '#icon-volume-up');
  };

  volBtn.onclick = () => {
    globalAudio.muted = !globalAudio.muted;
    if (globalAudio.muted) {
      volSlider.value = 0;
      volBtn.querySelector('use').setAttribute('href', '#icon-volume-off');
    } else {
      volSlider.value = globalAudio.volume || 1;
      volBtn.querySelector('use').setAttribute('href', '#icon-volume-up');
    }
  };
}

// --- MINI PLAYER INTEGRATION ---
function showMiniAudioPlayer() {
  const mini = document.getElementById('audio-mini-player');
  mini.classList.remove('hidden');

  // Fill current track stats
  const curFile = state.files.find(f => f.id === state.currentPlayingAudioId);
  if (!curFile) return;

  document.getElementById('mini-audio-title').textContent = curFile.name;
  
  const coverUrl = getThumbnailUrl(curFile);
  const defaultArt = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236750A4'%3E%3Cpath d='M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z'/%3E%3C/svg%3E`;
  document.getElementById('mini-audio-cover').src = coverUrl || defaultArt;

  // Mini-player timeline scrubber track
  globalAudio.addEventListener('timeupdate', syncMiniTimeline);

  // Play/Pause Action Toggle
  document.getElementById('mini-play-btn').onclick = (e) => {
    e.stopPropagation();
    if (globalAudio.paused) {
      globalAudio.play();
    } else {
      globalAudio.pause();
    }
  };

  // Nav buttons
  document.getElementById('mini-prev-btn').onclick = (e) => {
    e.stopPropagation();
    navigatePlaylist(-1);
  };
  document.getElementById('mini-next-btn').onclick = (e) => {
    e.stopPropagation();
    navigatePlaylist(1);
  };

  // Expand modal
  document.getElementById('mini-expand-btn').onclick = () => {
    openPreviewModal(curFile, activeSetForModal.length > 0 ? activeSetForModal : state.files);
  };

  // Click on main body of mini-player also expands it
  mini.onclick = (e) => {
    if (!e.target.closest('button') && !e.target.closest('.mini-player-progress-bar')) {
      openPreviewModal(curFile, activeSetForModal.length > 0 ? activeSetForModal : state.files);
    }
  };

  // Close player completely
  document.getElementById('mini-close-btn').onclick = (e) => {
    e.stopPropagation();
    globalAudio.pause();
    hideMiniAudioPlayer();
  };

  // Mini bar scrubber logic
  const miniScrub = document.getElementById('mini-progress-bar');
  miniScrub.onclick = (e) => {
    e.stopPropagation();
    const rect = miniScrub.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    globalAudio.currentTime = pct * globalAudio.duration;
  };
}

function navigatePlaylist(offset) {
  const currentList = activeSetForModal.length > 0 ? activeSetForModal : state.files;
  const audios = currentList.filter(f => f.type === 'audio');
  if (audios.length <= 1) return;

  let index = audios.findIndex(f => f.id === state.currentPlayingAudioId);
  index += offset;
  if (index >= audios.length) index = 0;
  if (index < 0) index = audios.length - 1;

  const nextTrack = audios[index];
  state.currentPlayingAudioId = nextTrack.id;

  // Sync source and play
  globalAudio.src = getStreamUrl(nextTrack.id);
  globalAudio.load();
  globalAudio.play().then(() => {
    showMiniAudioPlayer();
  });
}

function syncMiniTimeline() {
  const pct = (globalAudio.currentTime / globalAudio.duration) * 100 || 0;
  document.getElementById('mini-progress-fill').style.width = `${pct}%`;
}

function syncMiniAudioPlayerUI() {
  const miniPlayIcon = document.getElementById('mini-play-icon');
  if (!miniPlayIcon) return;
  
  if (globalAudio.paused) {
    miniPlayIcon.setAttribute('href', '#icon-play');
  } else {
    miniPlayIcon.setAttribute('href', '#icon-pause');
  }
}

function hideMiniAudioPlayer() {
  const mini = document.getElementById('audio-mini-player');
  mini.classList.add('hidden');
  globalAudio.removeEventListener('timeupdate', syncMiniTimeline);
  state.currentPlayingAudioId = null;
}

// ==========================================================================
// IMAGE LIGHTBOX PREVIEW & GESTURE ZOOM
// ==========================================================================
function setupImageLightbox(file) {
  const container = document.getElementById('viewer-image-container');
  container.classList.remove('hidden');

  const img = document.getElementById('lightbox-image-el');
  
  // Set placeholder loading states
  img.style.opacity = '0.3';
  img.src = getStreamUrl(file.id);

  img.onload = () => {
    img.style.opacity = '1';
  };

  // Zoom Button event binds
  document.getElementById('zoom-in-btn').onclick = () => changeZoom(0.25);
  document.getElementById('zoom-out-btn').onclick = () => changeZoom(-0.25);
  document.getElementById('zoom-reset-btn').onclick = () => resetImageZoom();

  // Wire mobile touch gestures (Pinch-Zoom / Drag Panning)
  const wrapper = document.getElementById('lightbox-image-wrapper');
  setupTouchGestures(wrapper, img);
}

function changeZoom(factor) {
  const img = document.getElementById('lightbox-image-el');
  state.zoomScale = Math.max(1, Math.min(4, state.zoomScale + factor));
  
  if (state.zoomScale === 1) {
    state.zoomTranslate = { x: 0, y: 0 };
  }
  updateImageTransform(img);
}

function resetImageZoom() {
  const img = document.getElementById('lightbox-image-el');
  state.zoomScale = 1;
  state.zoomTranslate = { x: 0, y: 0 };
  updateImageTransform(img);
}

function updateImageTransform(img) {
  if (img) {
    img.style.transform = `scale(${state.zoomScale}) translate(${state.zoomTranslate.x}px, ${state.zoomTranslate.y}px)`;
  }
}

// Pointer events coordinate tracker for mobile pinch/panning
function setupTouchGestures(wrapper, img) {
  let evCache = [];
  let prevDiff = -1;

  wrapper.onpointerdown = (e) => {
    evCache.push(e);
    state.isDraggingImage = true;
    state.dragStart = { x: e.clientX - state.zoomTranslate.x * state.zoomScale, y: e.clientY - state.zoomTranslate.y * state.zoomScale };
    wrapper.setPointerCapture(e.pointerId);
  };

  wrapper.onpointermove = (e) => {
    // Locate target pointer inside register
    for (let i = 0; i < evCache.length; i++) {
      if (e.pointerId === evCache[i].pointerId) {
        evCache[i] = e;
        break;
      }
    }

    // --- Pinch-zoom Gesture (Two active fingers) ---
    if (evCache.length === 2) {
      const diffX = Math.abs(evCache[0].clientX - evCache[1].clientX);
      const diffY = Math.abs(evCache[0].clientY - evCache[1].clientY);
      const curDiff = Math.hypot(diffX, diffY);

      if (prevDiff > 0) {
        if (curDiff > prevDiff) {
          changeZoom(0.04);
        } else if (curDiff < prevDiff) {
          changeZoom(-0.04);
        }
      }
      prevDiff = curDiff;
    }
    
    // --- Panning Image (Single finger pointer drag) ---
    else if (evCache.length === 1 && state.isDraggingImage && state.zoomScale > 1) {
      state.zoomTranslate.x = (e.clientX - state.dragStart.x) / state.zoomScale;
      state.zoomTranslate.y = (e.clientY - state.dragStart.y) / state.zoomScale;
      updateImageTransform(img);
    }
  };

  const endPointer = (e) => {
    evCache = evCache.filter(ev => ev.pointerId !== e.pointerId);
    if (evCache.length < 2) prevDiff = -1;
    if (evCache.length === 0) {
      state.isDraggingImage = false;
    }
  };

  wrapper.onpointerup = endPointer;
  wrapper.onpointercancel = endPointer;
  wrapper.onpointerleave = endPointer;
}

// ==========================================================================
// DOCUMENT & FALLBACK RENDER WRAPPERS
// ==========================================================================
function setupDocumentViewer(file) {
  const container = document.getElementById('viewer-document-container');
  container.classList.remove('hidden');

  const frameContainer = document.getElementById('document-frame-container');
  frameContainer.innerHTML = '';

  const streamUrl = getStreamUrl(file.id);
  const nameLower = file.name.toLowerCase();

  // PDF: embed in iframe — browsers render these natively
  if (nameLower.endsWith('.pdf')) {
    const iframe = document.createElement('iframe');
    iframe.src = streamUrl;
    iframe.title = file.name;
    frameContainer.appendChild(iframe);
  }
  // Plain-text viewable files — fetch and render in <pre>
  else if (isTextViewable(file.name)) {
    container.classList.add('hidden');
    setupTextViewer(file);
  }
  // Office / other docs — show fallback with download button
  else {
    container.classList.add('hidden');
    setupFallbackViewer(file);
  }
}

function setupFallbackViewer(file) {
  const container = document.getElementById('viewer-fallback-container');
  container.classList.remove('hidden');

  document.getElementById('fallback-card-name').textContent = file.name;
  document.getElementById('fallback-card-size').textContent = `Size: ${formatSize(file.size)}`;

  let iconId = '#icon-other';
  if (file.type === 'document') iconId = '#icon-document';
  document.querySelector('#fallback-card-icon use').setAttribute('href', iconId);

  document.getElementById('fallback-download-btn').onclick = () => downloadSingleFile(file);
}

// ==========================================================================
// TOAST NOTIFICATION ALERTS (M3 SPEC SNACKBAR)
// ==========================================================================
function showToast(text, duration = 3000) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'm3-snackbar';
  toast.innerHTML = `
    <span class="m3-snackbar-text">${text}</span>
    <button class="m3-snackbar-action-btn" aria-label="Dismiss">OK</button>
  `;

  // Bind close action
  toast.querySelector('.m3-snackbar-action-btn').onclick = () => {
    toast.remove();
  };

  container.appendChild(toast);

  // Auto expiry
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.animation = 'slide-up-fade var(--transition-medium) reverse forwards';
      setTimeout(() => toast.remove(), 350);
    }
  }, duration);
}

// Connection lost warning overlays
function showConnectionError() {
  document.getElementById('connection-error').classList.remove('hidden');
}

function hideConnectionError() {
  document.getElementById('connection-error').classList.add('hidden');
}

// ==========================================================================
// LISTENERS & EVENT REGISTRATION
// ==========================================================================
function setupEventListeners() {
  
  // Theme toggle
  document.getElementById('theme-toggle-btn').addEventListener('click', () => {
    const isDark = document.body.classList.toggle('dark');
    document.body.classList.toggle('light', !isDark);
    safeStorage.setItem('themeMode', isDark ? 'dark' : 'light');
    updateThemeIcon();
  });

  // Color picker listener
  const colorPicker = document.getElementById('theme-color-picker');
  if (colorPicker) {
    const savedColor = safeStorage.getItem('customThemeColor');
    if (savedColor) {
      colorPicker.value = savedColor;
      applyCustomHue(savedColor);
    }
    colorPicker.addEventListener('input', (e) => {
      applyCustomHue(e.target.value);
    });
  }

  // Settings Modal logic
  const settingsBtn = document.getElementById('settings-btn');
  const settingsModal = document.getElementById('settings-modal');
  const settingsCloseBtn = document.getElementById('settings-close-btn');

  if (settingsBtn && settingsModal) {
    settingsBtn.addEventListener('click', () => {
      settingsModal.classList.remove('hidden');
    });

    settingsCloseBtn.addEventListener('click', () => {
      settingsModal.classList.add('hidden');
    });

    settingsModal.addEventListener('click', (e) => {
      if (e.target === settingsModal) {
        settingsModal.classList.add('hidden');
      }
    });
  }

  // Password Submit Gate handler
  document.getElementById('password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('gate-password-input');
    const pwd = input.value;
    const card = document.querySelector('.gate-card');
    const errText = document.getElementById('password-error-text');

    card.classList.remove('shake');
    errText.classList.add('hidden');

    try {
      const url = state.isMockMode ? '/api/auth' : '/api/auth';
      const response = await apiFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: pwd })
      });

      if (response && response.token) {
        state.sessionToken = response.token;
        safeStorage.setItem('fluxToken', response.token, true);
        hidePasswordGate();
        await fetchFiles();
        showToast("Access Granted");
      }
    } catch (err) {
      console.warn("Auth check failed:", err);
      // Play invalid password shake animations
      card.classList.add('shake');
      errText.classList.remove('hidden');
      input.focus();
    }
  });

  // Password Show / Hide input toggle
  document.getElementById('password-toggle-btn').addEventListener('click', () => {
    const input = document.getElementById('gate-password-input');
    const iconUse = document.querySelector('#password-toggle-btn use');
    if (input.type === 'password') {
      input.type = 'text';
      iconUse.setAttribute('href', '#icon-visibility-off');
    } else {
      input.type = 'password';
      iconUse.setAttribute('href', '#icon-visibility');
    }
  });

  // Debounced search text updates
  const searchInput = document.getElementById('search-input');
  const searchClear = document.getElementById('search-clear-btn');
  searchInput.addEventListener('input', (e) => {
    const val = e.target.value;
    searchClear.classList.toggle('hidden', val.length === 0);

    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      state.searchQuery = val;
      renderFileDisplay();
    }, 250);
  });

  searchClear.addEventListener('click', () => {
    searchInput.value = '';
    searchClear.classList.add('hidden');
    state.searchQuery = '';
    renderFileDisplay();
    searchInput.focus();
  });

  // Filter selection chips
  const chips = document.querySelectorAll('.m3-chip');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => {
        c.classList.remove('active');
        c.setAttribute('aria-selected', 'false');
      });
      chip.classList.add('active');
      chip.setAttribute('aria-selected', 'true');

      state.activeFilter = chip.dataset.filter;
      renderFileDisplay();
    });
  });

  // Grid/List toggle action
  const viewToggle = document.getElementById('view-toggle-btn');
  const viewIcon = document.getElementById('view-toggle-icon');
  viewToggle.addEventListener('click', () => {
    state.viewMode = state.viewMode === 'grid' ? 'list' : 'grid';
    safeStorage.setItem('viewMode', state.viewMode);
    
    // Toggle active icons
    viewIcon.setAttribute('href', state.viewMode === 'grid' ? '#icon-list' : '#icon-grid');
    viewToggle.setAttribute('aria-label', state.viewMode === 'grid' ? 'Switch to list view' : 'Switch to grid view');
    
    renderFileDisplay();
  });

  // Sort Dropdown open/close
  const sortBtn = document.getElementById('sort-menu-btn');
  const sortDropdown = document.getElementById('sort-dropdown-menu');
  sortBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const expanded = sortBtn.getAttribute('aria-expanded') === 'true';
    sortBtn.setAttribute('aria-expanded', !expanded);
    sortDropdown.classList.toggle('hidden');
  });

  // Dropdown list click option
  sortDropdown.addEventListener('click', (e) => {
    const item = e.target.closest('.m3-dropdown-item');
    if (item) {
      state.sortOption = item.dataset.value;
      
      // Update visual check
      sortDropdown.querySelectorAll('.m3-dropdown-item').forEach(el => {
        el.removeAttribute('aria-selected');
      });
      item.setAttribute('aria-selected', 'true');
      
      document.getElementById('current-sort-label').textContent = `Sort: ${item.textContent}`;
      sortDropdown.classList.add('hidden');
      sortBtn.setAttribute('aria-expanded', 'false');
      
      renderFileDisplay();
    }
  });

  document.addEventListener('click', () => {
    sortDropdown.classList.add('hidden');
    sortBtn.setAttribute('aria-expanded', 'false');
  });

  // Selection Bar Actions
  document.getElementById('selection-download-btn').addEventListener('click', downloadSelected);
  document.getElementById('selection-clear-btn').addEventListener('click', clearSelection);
  document.getElementById('selection-cancel-btn').addEventListener('click', clearSelection);
  document.getElementById('selection-select-all-btn').addEventListener('click', selectAllFiltered);
  
  // Custom Playlist logic
  const playlistBtn = document.getElementById('selection-playlist-btn');
  const playlistToggleBtn = document.getElementById('playlist-toggle-btn');
  const playlistSidebar = document.getElementById('playlist-sidebar');
  const playlistCloseBtn = document.getElementById('playlist-close-btn');
  const playlistClearBtn = document.getElementById('playlist-clear-btn');
  
  const renderPlaylist = () => {
    const container = document.getElementById('playlist-items-container');
    if (state.playlist.length === 0) {
      container.innerHTML = '<div class="empty-playlist m3-body-medium">Your playlist is empty. Select files to add them here.</div>';
      return;
    }
    
    container.innerHTML = '';
    state.playlist.forEach((item, idx) => {
      const div = document.createElement('div');
      div.className = `playlist-item ${state.activeFileIndex !== -1 && state.files[state.activeFileIndex]?.id === item.id ? 'playing' : ''}`;
      div.innerHTML = `
        <svg style="width:24px;height:24px" viewBox="0 0 24 24"><use href="#icon-${item.type === 'video' ? 'video' : item.type === 'audio' ? 'audio' : 'other'}"></use></svg>
        <div class="playlist-item-text m3-body-medium">${item.name}</div>
      `;
      div.onclick = () => {
        const fileIdx = state.files.findIndex(f => f.id === item.id);
        if (fileIdx !== -1) {
          openPreviewModal(item.id, fileIdx);
        }
      };
      container.appendChild(div);
    });
  };

  playlistToggleBtn.addEventListener('click', () => {
    playlistSidebar.classList.toggle('hidden');
    renderPlaylist();
  });

  playlistCloseBtn.addEventListener('click', () => {
    playlistSidebar.classList.add('hidden');
  });

  playlistClearBtn.addEventListener('click', () => {
    state.playlist = [];
    safeStorage.setItem('flux-playlist', JSON.stringify(state.playlist));
    renderPlaylist();
    showToast('Queue cleared');
  });

  if (playlistBtn) {
    playlistBtn.addEventListener('click', () => {
      const selected = Array.from(state.selectedFiles);
      const toAdd = state.files.filter(f => selected.includes(f.id));
      state.playlist = state.playlist.concat(toAdd);
      safeStorage.setItem('flux-playlist', JSON.stringify(state.playlist));
      clearSelection();
      showToast(`Added ${toAdd.length} items to playlist`);
      renderPlaylist();
      if (playlistSidebar.classList.contains('hidden')) {
        playlistSidebar.classList.remove('hidden');
      }
    });
  }

  // Close modals
  document.getElementById('modal-close-btn').onclick = closePreviewModal;
  document.getElementById('modal-backdrop').onclick = closePreviewModal;

  // Keyboard navigation hooks
  document.addEventListener('keydown', (e) => {
    const modal = document.getElementById('viewer-modal');
    if (!modal.classList.contains('hidden')) {
      const videoContainer = document.getElementById('viewer-video-container');
      const isVideo = !videoContainer.classList.contains('hidden');
      const video = document.getElementById('native-video-el');

      if (e.key === 'Escape') {
        closePreviewModal();
      } else if (isVideo && !e.altKey && !e.ctrlKey && !e.metaKey) {
        const key = e.key.toLowerCase();
        if (e.key === 'ArrowRight' || key === 'l') {
          video.currentTime += 10;
        } else if (e.key === 'ArrowLeft' || key === 'j') {
          video.currentTime -= 10;
        } else if (e.key === ' ' || e.code === 'Space' || key === 'k') {
          e.preventDefault();
          if (video.paused) video.play();
          else video.pause();
        } else if (e.key === '>' || (e.key === '.' && e.shiftKey)) {
          video.playbackRate = Math.min(video.playbackRate + 0.25, 2.0);
          if (typeof showToast !== 'undefined') showToast(`Playback speed: ${video.playbackRate}x`);
        } else if (e.key === '<' || (e.key === ',' && e.shiftKey)) {
          video.playbackRate = Math.max(video.playbackRate - 0.25, 0.25);
          if (typeof showToast !== 'undefined') showToast(`Playback speed: ${video.playbackRate}x`);
        } else if (key === 'f') {
          document.getElementById('video-fullscreen-btn')?.click();
        } else if (key === 'm') {
          document.getElementById('video-volume-btn')?.click();
        } else if (e.key >= '0' && e.key <= '9') {
          const percent = parseInt(e.key) * 10;
          if (video.duration) {
            video.currentTime = (video.duration * percent) / 100;
          }
        }
      } else {
        if (e.key === 'ArrowRight') navigateModal(1);
        else if (e.key === 'ArrowLeft') navigateModal(-1);
      }
    }
  });

  // Re-establish connection check
  document.getElementById('retry-connection-btn').onclick = () => {
    hideConnectionError();
    loadPortalData();
  };

  // Swipe-to-close handler on mobile viewport lightbox cards
  const modalWindow = document.getElementById('modal-window');
  let startY = 0;
  let distY = 0;

  modalWindow.addEventListener('touchstart', (e) => {
    // Only permit swipe close if image is not zoomed
    if (state.zoomScale > 1) return;
    startY = e.touches[0].clientY;
  }, { passive: true });

  modalWindow.addEventListener('touchmove', (e) => {
    if (state.zoomScale > 1) return;
    distY = e.touches[0].clientY - startY;

    // Apply visual sliding effect downward
    if (distY > 0) {
      modalWindow.style.transform = `translateY(${distY}px)`;
    }
  }, { passive: true });

  modalWindow.addEventListener('touchend', () => {
    if (state.zoomScale > 1) return;
    if (distY > 150) {
      closePreviewModal();
    }
    // Snap back into shape
    modalWindow.style.transform = '';
    distY = 0;
  });
}
