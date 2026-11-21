const startupFeedback = document.querySelector('#startup-feedback');
const startupError = new URLSearchParams(window.location.search).get('startup_error');
const API_PORT = window.desktopEnv?.apiPort || '5055';
const LOGIN_API_URL = `http://127.0.0.1:${API_PORT}/api/login`;
const loginForm = document.querySelector('.login-form');
const loginButton = loginForm?.querySelector('.login-submit');
const ACCESS_TOKEN_KEY = 'pharmaStock.accessToken';

function showLoginFeedback(message) {
  startupFeedback.textContent = message;
  startupFeedback.hidden = false;
}

document.querySelectorAll('[data-password-toggle]').forEach((toggle) => {
  toggle.addEventListener('click', () => {
    const input = document.getElementById(toggle.dataset.passwordToggle);
    const shouldShow = input.type === 'password';
    input.type = shouldShow ? 'text' : 'password';
    toggle.setAttribute('aria-label', shouldShow ? 'Ocultar senha' : 'Visualizar senha');
    toggle.title = shouldShow ? 'Ocultar senha' : 'Visualizar senha';
  });
});

if (startupError === 'true') {
  startupFeedback.textContent =
    'Não foi possível verificar o primeiro acesso. Confira a conexão com o banco e reinicie o sistema.';
  startupFeedback.hidden = false;

  document.querySelectorAll('.login-form input, .login-form button').forEach((control) => {
    control.disabled = true;
  });
}

loginForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  startupFeedback.hidden = true;
  loginButton.disabled = true;

  const formData = new FormData(loginForm);

  try {
    const response = await fetch(LOGIN_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: formData.get('email'),
        password: formData.get('password'),
      }),
    });
    const result = await response.json();

    if (!response.ok || !result.ok || !result.access_token) {
      showLoginFeedback(result.message || 'Não foi possível realizar o login.');
      return;
    }

    sessionStorage.setItem(ACCESS_TOKEN_KEY, result.access_token);
    window.location.replace('../src/screens/home_screen.html');
  } catch (error) {
    if (error instanceof DOMException && error.name === 'SecurityError') {
      showLoginFeedback('Não foi possível iniciar uma sessão segura neste dispositivo.');
    } else {
      showLoginFeedback(
        'Não foi possível conectar ao servidor. Verifique se o backend Flask iniciou corretamente.',
      );
    }
  } finally {
    loginButton.disabled = false;
  }
});
