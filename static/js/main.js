/**
 * main.js – AI Startup Incubator Agent
 * Global UI interactions, search, toast notifications, loading helpers.
 */

(function () {
  'use strict';

  // ────────────────────────────────────────────────────────────
  // Sidebar toggle
  // ────────────────────────────────────────────────────────────
  const sidebar       = document.getElementById('sidebar');
  const mainWrapper   = document.getElementById('mainWrapper');
  const sidebarToggle = document.getElementById('sidebarToggle');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      if (window.innerWidth >= 992) {
        sidebar.classList.toggle('collapsed');
        mainWrapper.classList.toggle('sidebar-collapsed');
      }
    });

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
  // Loading overlay helpers
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
  // Toast notification helper
  // ────────────────────────────────────────────────────────────
  window.showToast = function (message, type) {
    type = type || 'info';
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const iconMap = {
      success: 'check-circle-fill',
      danger:  'x-circle-fill',
      warning: 'exclamation-triangle-fill',
      info:    'info-circle-fill',
    };
    const colorMap = {
      success: 'text-success',
      danger:  'text-danger',
      warning: 'text-warning',
      info:    'text-info',
    };

    const id   = 'toast-' + Date.now();
    const html = `
      <div id="${id}" class="toast align-items-center border-0 glass" role="alert" aria-live="assertive">
        <div class="d-flex align-items-center p-3 gap-2">
          <i class="bi bi-${iconMap[type] || 'info-circle-fill'} ${colorMap[type] || 'text-info'} fs-5 flex-shrink-0"></i>
          <div class="toast-body p-0 flex-grow-1">${message}</div>
          <button type="button" class="btn-close btn-close-white ms-2" data-bs-dismiss="toast"></button>
        </div>
      </div>`;
    container.insertAdjacentHTML('beforeend', html);
    const el = document.getElementById(id);
    if (window.bootstrap) {
      const t = new bootstrap.Toast(el, { delay: 4000 });
      t.show();
      el.addEventListener('hidden.bs.toast', () => el.remove());
    }
  };

  // ────────────────────────────────────────────────────────────
  // Auto-dismiss flash alerts after 6 seconds
  // ────────────────────────────────────────────────────────────
  document.querySelectorAll('.flash-alert').forEach(function (el) {
    setTimeout(function () {
      const bsAlert = window.bootstrap && bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    }, 6000);
  });

  // ────────────────────────────────────────────────────────────
  // Count-up animation for stat numbers
  // ────────────────────────────────────────────────────────────
  function animateCount(el, target, duration) {
    const start = performance.now();
    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
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
      bar.style.transition = 'width 0.9s cubic-bezier(0.4, 0, 0.2, 1)';
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

  // ────────────────────────────────────────────────────────────
  // Global search bar
  // ────────────────────────────────────────────────────────────
  (function () {
    const input   = document.getElementById('globalSearch');
    const results = document.getElementById('searchResults');
    if (!input || !results) return;

    let debounceTimer;

    function renderResults(items) {
      if (!items.length) {
        results.innerHTML = '<div class="search-no-result p-3 text-muted small">No startups found.</div>';
        results.classList.add('visible');
        return;
      }
      results.innerHTML = items.map(function (r) {
        return `
          <a href="/startup/${r.id}" class="search-result-item d-flex gap-2 align-items-center p-2 text-decoration-none">
            <i class="bi bi-rocket-takeoff text-primary"></i>
            <div class="min-w-0">
              <div class="small fw-600 text-truncate">${escapeHtml(r.startup_name)}</div>
              <div class="text-muted" style="font-size:0.75rem">${escapeHtml(r.industry)} · ${escapeHtml(r.country)}</div>
            </div>
            <span class="badge badge-status-${r.status} ms-auto">${r.status}</span>
          </a>`;
      }).join('');
      results.classList.add('visible');
    }

    function escapeHtml(str) {
      return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    input.addEventListener('input', function () {
      clearTimeout(debounceTimer);
      const q = input.value.trim();
      if (!q) { results.innerHTML = ''; results.classList.remove('visible'); return; }
      debounceTimer = setTimeout(function () {
        fetch('/api/search?q=' + encodeURIComponent(q))
          .then(function (r) { return r.json(); })
          .then(function (data) { renderResults(data.results || []); })
          .catch(function () { results.classList.remove('visible'); });
      }, 280);
    });

    document.addEventListener('click', function (e) {
      if (!input.contains(e.target) && !results.contains(e.target)) {
        results.innerHTML = '';
        results.classList.remove('visible');
      }
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        results.innerHTML = '';
        results.classList.remove('visible');
        input.value = '';
      }
    });
  }());

  // ────────────────────────────────────────────────────────────
  // Client-side form validation feedback
  // ────────────────────────────────────────────────────────────
  document.querySelectorAll('form[novalidate]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!form.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
        form.querySelectorAll(':invalid').forEach(function (field) {
          field.classList.add('is-invalid');
        });
      }
      form.classList.add('was-validated');
    });

    form.querySelectorAll('input,select,textarea').forEach(function (field) {
      field.addEventListener('input', function () {
        if (field.validity.valid) {
          field.classList.remove('is-invalid');
          field.classList.add('is-valid');
        } else {
          field.classList.add('is-invalid');
          field.classList.remove('is-valid');
        }
      });
    });
  });

  // ────────────────────────────────────────────────────────────
  // Confirm delete modals
  // ────────────────────────────────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.dataset.confirm)) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  });

}());
