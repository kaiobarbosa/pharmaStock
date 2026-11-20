const API_PORT = window.desktopEnv?.apiPort || '5000';
const API_URL = `http://127.0.0.1:${API_PORT}/api/create_director_account`;

const accountForm = document.querySelector('.auth-form');
const feedback = document.querySelector('#form-feedback');
const submitButton = accountForm?.querySelector('[type="submit"]');
const passwordInput = document.querySelector('#password');
const passwordToggle = document.querySelector('.password-toggle');

function showFeedback(message, kind) {
  feedback.textContent = message;
  feedback.dataset.kind = kind;
  feedback.hidden = false;
}

passwordToggle?.addEventListener('click', () => {
  const shouldShow = passwordInput.type === 'password';
  passwordInput.type = shouldShow ? 'text' : 'password';
  passwordToggle.setAttribute('aria-label', shouldShow ? 'Ocultar senha' : 'Visualizar senha');
  passwordToggle.title = shouldShow ? 'Ocultar senha' : 'Visualizar senha';
});

accountForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  feedback.hidden = true;
  submitButton.disabled = true;
  const buttonLabel = submitButton.querySelector('.primary-button__label');
  const originalLabel = buttonLabel.textContent;
  buttonLabel.textContent = 'Enviando... ';

  const formData = new FormData(accountForm);
  const payload = {
    first_name: formData.get('first_name'),
    last_name: formData.get('last_name'),
    cpf: formData.get('cpf'),
    email: formData.get('email'),
    password: formData.get('password'),
    password_confirmation: formData.get('password_confirmation'),
    internal_code: formData.get('internal_code'),
  };

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const result = await response.json();

    if (!response.ok) {
      const fieldErrors = result.errors ? Object.values(result.errors).join(' ') : '';
      showFeedback(fieldErrors || result.message || 'Não foi possível criar a conta.', 'error');
      return;
    }

    accountForm.reset();
    if (passwordInput.type === 'text') {
      passwordInput.type = 'password';
      passwordToggle.setAttribute('aria-label', 'Visualizar senha');
      passwordToggle.title = 'Visualizar senha';
    }
    showFeedback(result.message || 'Conta criada com sucesso.', 'success');
  } catch (error) {
    showFeedback(
      'Não foi possível conectar ao servidor. Verifique se o backend Flask iniciou corretamente.',
      'error',
    );
  } finally {
    submitButton.disabled = false;
    buttonLabel.textContent = originalLabel;
  }
});
