const profile = {
  role: 'Farmacêutica',
  firstName: 'Ana Luiza',
  lastName: 'Ribeiro',
  internalCode: 'FAR-028',
  crf: 'CRF-SP 123456',
  branch: 'Filial Centro',
  email: 'ana.ribeiro@pharmastock.demo',
  demoPassword: 'SenhaDemo!2026',
};

const salesHistory = [
  { date: '20/11/2026 · 16:42', branch: 'Filial Centro', product: 'Dipirona monoidratada 500 mg' },
  { date: '20/11/2026 · 14:18', branch: 'Filial Centro', product: 'Protetor solar facial FPS 50' },
  { date: '19/11/2026 · 11:06', branch: 'Filial Jardins', product: 'Vitamina C 1 g' },
  { date: '18/11/2026 · 17:31', branch: 'Filial Centro', product: 'Termômetro digital' },
  { date: '18/11/2026 · 10:25', branch: 'Filial Jardins', product: 'Creme hidratante calmante' },
];

const profileDetailsGrid = document.querySelector('#profile-details-grid');
const profileEditForm = document.querySelector('#profile-edit-form');
const profileFeedback = document.querySelector('#profile-page-feedback');
let passwordVisible = false;

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function renderProfile() {
  const fullName = `${profile.firstName} ${profile.lastName}`;
  const initials = `${profile.firstName.charAt(0)}${profile.lastName.charAt(0)}`.toLocaleUpperCase('pt-BR');
  document.querySelector('#profile-display-name').textContent = fullName;
  document.querySelector('#profile-display-branch').textContent = profile.branch;
  document.querySelector('#profile-avatar').textContent = initials;
  document.querySelector('.profile-card-heading .section-kicker').textContent = profile.role;

  const detailItems = [
    ['Nome', profile.firstName],
    ['Sobrenome', profile.lastName],
    ['Código interno', profile.internalCode],
    ['CRF', profile.crf],
    ['Filial', profile.branch],
    ['E-mail', profile.email],
  ];

  profileDetailsGrid.innerHTML = detailItems.map(([label, value]) => `
    <div class="profile-detail">
      <span class="profile-detail__label">${escapeHtml(label)}</span>
      <span class="profile-detail__value">${escapeHtml(value)}</span>
    </div>`).join('') + `
    <div class="profile-detail profile-detail--password">
      <span class="profile-detail__label">Senha</span>
      <div class="profile-password-value">
        <span id="profile-password-value">${passwordVisible ? escapeHtml(profile.demoPassword) : '••••••••••••'}</span>
        <button class="text-button profile-password-toggle" id="toggle-profile-password" type="button">${passwordVisible ? 'Ocultar senha' : 'Exibir senha'}</button>
      </div>
    </div>`;

  document.querySelector('#profile-sales-history').innerHTML = salesHistory.map((sale) => `
    <tr>
      <td>${escapeHtml(sale.date)}</td>
      <td>${escapeHtml(sale.branch)}</td>
      <td>${escapeHtml(sale.product)}</td>
    </tr>`).join('');

  profileEditForm.elements.firstName.value = profile.firstName;
  profileEditForm.elements.lastName.value = profile.lastName;
  profileEditForm.elements.internalCode.value = profile.internalCode;
  profileEditForm.elements.branch.value = profile.branch;
  profileEditForm.elements.crf.value = profile.crf;
  profileEditForm.elements.email.value = profile.email;
  profileEditForm.elements.password.value = profile.demoPassword;
}

function cancelProfileEdit() {
  profileEditForm.hidden = true;
  profileDetailsGrid.hidden = false;
  document.querySelector('#edit-profile-button').hidden = false;
  profileEditForm.elements.firstName.value = profile.firstName;
  profileEditForm.elements.lastName.value = profile.lastName;
  profileEditForm.elements.internalCode.value = profile.internalCode;
  profileEditForm.elements.branch.value = profile.branch;
  profileEditForm.elements.crf.value = profile.crf;
  profileEditForm.elements.email.value = profile.email;
  profileEditForm.elements.password.value = profile.demoPassword;
}

document.querySelectorAll('[data-profile-tab]').forEach((tab) => {
  tab.addEventListener('click', () => {
    if (tab.dataset.profileTab === 'history' && !profileEditForm.hidden) cancelProfileEdit();

    document.querySelectorAll('[data-profile-tab]').forEach((item) => {
      const selected = item === tab;
      item.classList.toggle('is-active', selected);
      item.setAttribute('aria-selected', String(selected));
    });
    document.querySelectorAll('[data-profile-panel]').forEach((panel) => {
      panel.hidden = panel.dataset.profilePanel !== tab.dataset.profileTab;
    });
  });
});

document.querySelector('#edit-profile-button').addEventListener('click', () => {
  profileDetailsGrid.hidden = true;
  document.querySelector('#edit-profile-button').hidden = true;
  profileEditForm.hidden = false;
  profileEditForm.elements.firstName.focus();
});

document.querySelector('#cancel-profile-edit').addEventListener('click', cancelProfileEdit);

profileDetailsGrid.addEventListener('click', (event) => {
  if (!event.target.closest('#toggle-profile-password')) return;
  passwordVisible = !passwordVisible;
  const passwordValue = document.querySelector('#profile-password-value');
  passwordValue.textContent = passwordVisible ? profile.demoPassword : '••••••••••••';
  event.target.closest('#toggle-profile-password').textContent = passwordVisible ? 'Ocultar senha' : 'Exibir senha';
});

profileEditForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(profileEditForm).entries());
  profile.firstName = values.firstName.trim();
  profile.lastName = values.lastName.trim();
  profile.internalCode = values.internalCode.trim();
  profile.branch = values.branch;
  profile.crf = values.crf.trim();
  profile.email = values.email.trim();
  if (values.password.trim()) profile.demoPassword = values.password;

  passwordVisible = false;
  renderProfile();
  cancelProfileEdit();
  profileFeedback.textContent = 'As informações do perfil foram atualizadas neste protótipo.';
  profileFeedback.hidden = false;
});

renderProfile();
