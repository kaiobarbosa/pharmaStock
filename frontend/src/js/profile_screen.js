const ACCESS_TOKEN_KEY = 'pharmaStock.accessToken';
const LOGIN_SCREEN_URL = '../../public/index.html';
const API_PORT = window.desktopEnv?.apiPort || '5055';
const PROFILE_API_URL = `http://127.0.0.1:${API_PORT}/api/users/me`;

const profileDetailsGrid = document.querySelector('#profile-details-grid');
const profileEditForm = document.querySelector('#profile-edit-form');
const profileFeedback = document.querySelector('#profile-page-feedback');
const editProfileButton = document.querySelector('#edit-profile-button');
const formFeedback = document.querySelector('#profile-form-feedback');
const submitButton = profileEditForm.querySelector('[type="submit"]');
const currentPasswordField = document.querySelector('#profile-current-password-field');
const currentPasswordInput = profileEditForm.elements.current_password;
let profile = null;

function redirectToLogin() {
  try {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    // Navigation still clears the in-memory page if storage is unavailable.
  }
  window.location.replace(LOGIN_SCREEN_URL);
}

function readAccessToken() {
  try {
    return sessionStorage.getItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    redirectToLogin();
    return null;
  }
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatCpf(value) {
  const digits = String(value ?? '').replace(/\D/g, '');
  if (digits.length !== 11) return value || '—';
  return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

function setPageFeedback(message, kind = 'error') {
  profileFeedback.textContent = message;
  profileFeedback.dataset.kind = kind;
  profileFeedback.hidden = !message;
}

function syncEmailReauthentication() {
  if (!profile) return;
  const emailChanged = profileEditForm.elements.email.value.trim().toLowerCase()
    !== String(profile.email).trim().toLowerCase();
  currentPasswordField.hidden = !emailChanged;
  currentPasswordInput.required = emailChanged;
  if (!emailChanged) currentPasswordInput.value = '';
}

function renderProfile() {
  const fullName = `${profile.first_name} ${profile.last_name}`.trim();
  const initials = `${profile.first_name.charAt(0)}${profile.last_name.charAt(0)}`
    .toLocaleUpperCase('pt-BR');
  document.querySelector('#profile-display-name').textContent = fullName;
  document.querySelector('#profile-display-branch').textContent = profile.branch || '—';
  document.querySelector('#profile-avatar').textContent = initials || '—';
  document.querySelector('#profile-role').textContent = profile.role || 'Usuário';

  const detailItems = [
    ['Nome', profile.first_name],
    ['Sobrenome', profile.last_name],
    ['CPF', formatCpf(profile.cpf)],
    ['Código interno', profile.internal_code],
    ['CRF', profile.crf],
    ['Filial', profile.branch],
    ['E-mail', profile.email],
  ];
  profileDetailsGrid.innerHTML = detailItems.map(([label, value]) => `
    <div class="profile-detail">
      <span class="profile-detail__label">${escapeHtml(label)}</span>
      <span class="profile-detail__value">${escapeHtml(value || '—')}</span>
    </div>`).join('');

  profileEditForm.elements.first_name.value = profile.first_name || '';
  profileEditForm.elements.last_name.value = profile.last_name || '';
  profileEditForm.elements.cpf.value = profile.cpf || '';
  profileEditForm.elements.email.value = profile.email || '';
  currentPasswordInput.value = '';
  syncEmailReauthentication();
  editProfileButton.hidden = false;
}

function closeProfileEdit() {
  profileEditForm.hidden = true;
  profileDetailsGrid.hidden = false;
  editProfileButton.hidden = false;
  formFeedback.hidden = true;
  if (profile) {
    profileEditForm.elements.first_name.value = profile.first_name || '';
    profileEditForm.elements.last_name.value = profile.last_name || '';
    profileEditForm.elements.cpf.value = profile.cpf || '';
    profileEditForm.elements.email.value = profile.email || '';
    currentPasswordInput.value = '';
    syncEmailReauthentication();
  }
}

async function loadProfile() {
  const token = readAccessToken();
  if (!token) {
    redirectToLogin();
    return;
  }

  try {
    const response = await fetch(PROFILE_API_URL, {
      headers: { Authorization: `Bearer ${token}` },
      cache: 'no-store',
    });
    const result = await response.json();
    if (response.status === 401) {
      redirectToLogin();
      return;
    }
    if (!response.ok || !result.ok || !result.user) {
      throw new Error(result.message || 'Não foi possível carregar o perfil.');
    }

    profile = result.user;
    renderProfile();
    setPageFeedback('');
  } catch (error) {
    setPageFeedback(error.message || 'Não foi possível conectar ao servidor.');
    document.querySelector('#profile-display-name').textContent = 'Perfil indisponível';
  }
}

editProfileButton.addEventListener('click', () => {
  profileDetailsGrid.hidden = true;
  editProfileButton.hidden = true;
  profileEditForm.hidden = false;
  profileEditForm.elements.first_name.focus();
});

document.querySelector('#cancel-profile-edit').addEventListener('click', closeProfileEdit);
profileEditForm.elements.email.addEventListener('input', syncEmailReauthentication);

profileEditForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const token = readAccessToken();
  if (!token || !profile) {
    redirectToLogin();
    return;
  }

  formFeedback.hidden = true;
  submitButton.disabled = true;
  const formData = new FormData(profileEditForm);
  const payload = Object.fromEntries(formData.entries());

  try {
    const response = await fetch(PROFILE_API_URL, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      cache: 'no-store',
    });
    const result = await response.json();
    if (response.status === 401) {
      redirectToLogin();
      return;
    }
    if (!response.ok || !result.ok || !result.user || !result.access_token) {
      const details = result.errors ? Object.values(result.errors).join(' ') : '';
      throw new Error([result.message, details].filter(Boolean).join(' ')
        || 'Não foi possível atualizar o perfil.');
    }

    try {
      sessionStorage.setItem(ACCESS_TOKEN_KEY, result.access_token);
    } catch (error) {
      redirectToLogin();
      return;
    }
    profile = result.user;
    renderProfile();
    closeProfileEdit();
    setPageFeedback(result.message, 'success');
  } catch (error) {
    formFeedback.textContent = error.message || 'Não foi possível conectar ao servidor.';
    formFeedback.dataset.kind = 'error';
    formFeedback.hidden = false;
  } finally {
    currentPasswordInput.value = '';
    submitButton.disabled = false;
  }
});

loadProfile();
