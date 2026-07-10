/**
 * main.js  –  AI Startup Incubator Agent
 * Global UI interactions: sidebar toggle, loading overlay helpers.
 */

(function () {
  'use strict';

  // ────────────────────────────────────────────────────────────
  // Sidebar toggle (mobile + desktop collapse)
  // ────────────────────────────────────────────────────────────
  const sidebar       = document.getElementById('sidebar');
  const mainWrapper   = document.getElementById('mainWrapper');
  const sidebarToggle = document.getElementById('sidebarToggle');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      // On larger screens collapse the sidebar by narrowing main wrapper
      if (window.innerWidth >= 992) {
        sidebar.classList.toggle('collapsed');
        mainWrapper.classList.toggle('sidebar-collapsed');
      }
    });

    // Close sidebar on outside click (mobile)
    document.addEventListener('click', function (e) {
      if (
        window.innerWidth < 992 &&
        sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        !sidebarToggle.contains(e.target)
      ) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ────────────────────────────────────────────────────────────
  // Global loading overlay helpers
  // ────────────────────────────────────────────────────────────
  window.showLoading = function (msg) {
    const overlay = document.getElementById('loadingOverlay');
    const text    = document.getElementById('loadingText');
    if (!overlay) return;
    if (text && msg) text.textContent = msg;
    overlay.classList.add('active');
  };

  window.hideLoading = function () {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('active');
  };

  // ────────────────────────────────────────────────────────────
  // Auto-dismiss flash alerts after 6 seconds
  // ────────────────────────────────────────────────────────────
  document.querySelectorAll('.flash-container .alert').forEach(function (el) {
    setTimeout(function () {
      const bsAlert = window.bootstrap && bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    }, 6000);
  });

  // ────────────────────────────────────────────────────────────
  // Animate stat numbers on dashboard load (count-up effect)
  // ────────────────────────────────────────────────────────────
  function animateCount(el, target, duration) {
    const start = performance.now();
    function step(now) {
      const elapsed  = now - start;
      const progress = Math.min(elapsed / duration, 1);
      el.textContent = Math.floor(progress * target);
      if (progress < 1) requestAnimationFrame(step);
      else el.textContent = target;
    }
    requestAnimationFrame(step);
  }

  document.querySelectorAll('.stat-value').forEach(function (el) {
    const raw = parseInt(el.textContent, 10);
    if (!isNaN(raw) && raw > 0) {
      el.textContent = '0';
      animateCount(el, raw, 800);
    }
  });

  // ────────────────────────────────────────────────────────────
  // Animated progress bars on page load
  // ────────────────────────────────────────────────────────────
  document.querySelectorAll('.progress-bar').forEach(function (bar) {
    const target = bar.style.width;
    bar.style.width = '0';
    setTimeout(function () {
      bar.style.transition = 'width 0.8s ease';
      bar.style.width = target;
    }, 200);
  });

  // ────────────────────────────────────────────────────────────
  // Bootstrap tooltip initialisation
  // ────────────────────────────────────────────────────────────
  if (window.bootstrap) {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
      new bootstrap.Tooltip(el);
    });
  }

}());
