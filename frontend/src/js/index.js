const startupFeedback = document.querySelector('#startup-feedback');
const startupError = new URLSearchParams(window.location.search).get('startup_error');

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
