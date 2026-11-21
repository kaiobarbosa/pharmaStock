const ACCESS_TOKEN_KEY = 'pharmaStock.accessToken';
const LOGIN_SCREEN_URL = '../../public/index.html';
const API_PORT = window.desktopEnv?.apiPort || '5055';
const VERIFY_SESSION_URL = `http://127.0.0.1:${API_PORT}/api/auth/session`;
let expirationTimer;

function redirectToLogin() {
  window.clearTimeout(expirationTimer);
  try {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    // Navigation still clears the in-memory page even if storage is unavailable.
  }
  window.location.replace(LOGIN_SCREEN_URL);
}

function readTokenExpiration(token) {
  try {
    const payloadPart = token.split('.')[1];
    if (!payloadPart) return null;

    const base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
    const paddedBase64 = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
    const bytes = Uint8Array.from(atob(paddedBase64), (character) => character.charCodeAt(0));
    const payload = JSON.parse(new TextDecoder().decode(bytes));
    return Number.isFinite(payload.exp) ? payload.exp * 1000 : null;
  } catch (error) {
    return null;
  }
}

async function enforceSessionExpiration() {
  let token;
  try {
    token = sessionStorage.getItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    redirectToLogin();
    return;
  }
  const expiresAt = token ? readTokenExpiration(token) : null;

  if (!expiresAt || Date.now() >= expiresAt) {
    redirectToLogin();
    return;
  }

  try {
    const response = await fetch(VERIFY_SESSION_URL, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      redirectToLogin();
      return;
    }
  } catch (error) {
    redirectToLogin();
    return;
  }

  window.clearTimeout(expirationTimer);
  expirationTimer = window.setTimeout(redirectToLogin, expiresAt - Date.now());
}

enforceSessionExpiration();
window.addEventListener('focus', enforceSessionExpiration);
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') enforceSessionExpiration();
});
