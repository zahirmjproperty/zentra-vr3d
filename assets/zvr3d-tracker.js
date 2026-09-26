// zentra-vr3d-tracker.js — Client-side tour analytics tracker.
// Stores data in localStorage, persists per browser.
// This is a Phase 1 tracker — real backend will replace it.

(function() {
  'use strict';

  // ── Config ──
  const STORAGE_KEY = 'zvr3d_analytics';
  const SESSION_KEY = 'zvr3d_session';

  // ── State ──
  let tourId = null;
  let sceneId = null;
  let sceneStart = null;
  let sessionId = null;

  // ── Init ──
  function init() {
    tourId = new URLSearchParams(window.location.search).get('id') || 'unknown';
    
    // Generate or reuse session ID
    sessionId = localStorage.getItem(SESSION_KEY);
    if (!sessionId) {
      sessionId = 's-' + Date.now().toString(36) + '-' + Math.random().toString(36).substr(2, 6);
      localStorage.setItem(SESSION_KEY, sessionId);
    }

    // Record visit
    track('visit', { tour: tourId });

    // Track page unload
    window.addEventListener('beforeunload', function() {
      endScene();
    });

    // Track visibility change (user leaves tab)
    document.addEventListener('visibilitychange', function() {
      if (document.hidden) {
        endScene();
      } else {
        // Resumed — don't restart scene if they navigated away
      }
    });
  }

  // ── Track event ──
  function track(event, data) {
    try {
      const store = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      if (!store[tourId]) {
        store[tourId] = { 
          created: new Date().toISOString(),
          views: 0,
          uniqueSessions: [],
          scenes: {},
          transitions: [],
          totalTime: 0
        };
      }
      const t = store[tourId];

      switch (event) {
        case 'visit':
          t.views = (t.views || 0) + 1;
          if (!t.uniqueSessions.includes(sessionId)) {
            t.uniqueSessions.push(sessionId);
          }
          t.lastVisit = new Date().toISOString();
          break;

        case 'scene':
          // End previous scene timer
          endScene();

          // Start new scene
          sceneStart = Date.now();
          sceneId = data.scene;
          if (!t.scenes[data.scene]) {
            t.scenes[data.scene] = { title: data.title || data.scene, views: 0, totalTimeMs: 0 };
          }
          t.scenes[data.scene].views = (t.scenes[data.scene].views || 0) + 1;

          // Record transition
          if (data.from) {
            t.transitions.push({
              from: data.from,
              to: data.scene,
              time: new Date().toISOString()
            });
          }
          break;

        case 'viewerReady':
          t.viewerReady = true;
          break;
      }

      localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
    } catch(e) {
      // localStorage full or disabled — silently fail
    }
  }

  // ── End scene timer ──
  function endScene() {
    if (sceneId && sceneStart) {
      const elapsed = Date.now() - sceneStart;
      try {
        const store = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        if (store[tourId] && store[tourId].scenes[sceneId]) {
          store[tourId].scenes[sceneId].totalTimeMs = (store[tourId].scenes[sceneId].totalTimeMs || 0) + elapsed;
          store[tourId].totalTime = (store[tourId].totalTime || 0) + elapsed;
        }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
      } catch(e) {}
      sceneStart = null;
      sceneId = null;
    }
  }

  // ── Public API ──
  window.ZVR3D_TRACKER = {
    init: init,
    track: track,
    endScene: endScene,
    getData: function(tid) {
      try {
        const store = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        return tid ? store[tid] : store;
      } catch(e) { return {}; }
    },
    clear: function(tid) {
      try {
        const store = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        if (tid) delete store[tid];
        else Object.keys(store).forEach(k => delete store[k]);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
      } catch(e) {}
    }
  };

  // Auto-init if on a tour page
  if (document.querySelector('#pano')) {
    init();
  }

})();