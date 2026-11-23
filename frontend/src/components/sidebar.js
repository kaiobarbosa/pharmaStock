(() => {
  const screenUrl = (fileName) => new URL(`../screens/${fileName}`, document.currentScript.src).href;

  const escapeHtml = (value) => String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

  const icons = {
    home: '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m3.5 10 8.5-7 8.5 7v10.5h-6v-6h-5v6h-6V10Z" /></svg>',
    products: '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m12 3 8.5 4.5v9L12 21l-8.5-4.5v-9L12 3Z" /><path d="m3.8 7.7 8.2 4.5 8.2-4.5M12 12.2V21" /></svg>',
    employees: '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="9" cy="8" r="3.5" /><path d="M2.8 20v-1.5a6.2 6.2 0 0 1 12.4 0V20H2.8Zm13-15a3.5 3.5 0 0 1 0 6.8m1.4 2.1a5.6 5.6 0 0 1 4 5.4V20h-3" /></svg>',
    branches: '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 21V5l8-2v18M12 9h8v12M2 21h20M7 8h2m-2 4h2m-2 4h2m8-1h1m-1 3h1" /></svg>',
    profile: '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="8" r="3.5" /><path d="M4 21a8 8 0 0 1 16 0" /></svg>',
  };

  const navigationItems = [
    { id: 'home', label: 'Home', file: 'home_screen.html' },
    { id: 'products', label: 'Produtos', file: 'products_screen.html' },
    { id: 'employees', label: 'Funcionários', file: 'employees_screen.html' },
    { id: 'branches', label: 'Filiais', file: 'branchs_screen.html' },
    { id: 'profile', label: 'Perfil', file: 'profile_screen.html' },
  ];

  function renderBrand(isLinked) {
    const contents = `
      <span class="brand-mark" aria-hidden="true">P</span>
      <span class="brand-copy">
        <span class="brand-kicker">gestão farmacêutica</span>
        <span class="brand-name">PharmaStock</span>
      </span>`;

    if (!isLinked) return `<div class="brand-row">${contents}</div>`;
    return `<a class="brand-row" href="${screenUrl('home_screen.html')}" aria-label="PharmaStock — Home">${contents}</a>`;
  }

  function renderAuthSidebar(sidebar) {
    const title = escapeHtml(sidebar.dataset.noteTitle || 'Acesso seguro');
    const detail = escapeHtml(sidebar.dataset.noteDetail || 'Gestão unificada da rede');
    const footer = escapeHtml(sidebar.dataset.footer || 'Ambiente corporativo');

    sidebar.classList.add('sidebar--auth');
    sidebar.setAttribute('aria-label', 'Identidade do PharmaStock');
    sidebar.innerHTML = `
      ${renderBrand(false)}
      <div class="sidebar-note">
        <span class="sidebar-note__rule" aria-hidden="true"></span>
        <p>${title}</p>
        <span class="sidebar-note__detail">${detail}</span>
      </div>
      <div class="sidebar-footer">
        <span class="status-dot" aria-hidden="true"></span>
        <span>${footer}</span>
      </div>`;
  }

  function renderAppSidebar(sidebar) {
    const activeItem = sidebar.dataset.active || 'home';
    const links = navigationItems.map(({ id, label, file }) => {
      const active = id === activeItem;
      const current = active ? ' aria-current="page"' : '';
      return `
        <a class="sidebar__link${active ? ' is-active' : ''}" href="${screenUrl(file)}" title="${label}"${current}>
          ${icons[id]}
          <span class="sidebar__link-label">${label}</span>
        </a>`;
    }).join('');

    sidebar.classList.add('sidebar--app');
    sidebar.setAttribute('aria-label', 'Navegação do PharmaStock');
    sidebar.innerHTML = `
      ${renderBrand(true)}
      <nav class="sidebar-nav" aria-label="Menu principal">${links}</nav>
      <div class="sidebar-footer">
        <span class="status-dot" aria-hidden="true"></span>
        <span>Ambiente corporativo</span>
      </div>`;
  }

  document.querySelectorAll('[data-sidebar]').forEach((sidebar) => {
    if (sidebar.dataset.sidebarMode === 'app') {
      renderAppSidebar(sidebar);
    } else {
      renderAuthSidebar(sidebar);
    }
  });
})();
