const ACCESS_TOKEN_KEY = 'pharmaStock.accessToken';
const LOGIN_SCREEN_URL = '../../public/index.html';
const API_PORT = window.desktopEnv?.apiPort || '5055';
const VERIFY_SESSION_URL = `http://127.0.0.1:${API_PORT}/api/auth/session`;
const PRODUCT_SEARCH_API_URL = `http://127.0.0.1:${API_PORT}/api/products/search`;
let expirationTimer;
let productSearchRequest = 0;

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

const productSearchForm = document.querySelector('#product-search-form');
const productSearchInput = document.querySelector('#product-search-input');
const productSearchFeedback = document.querySelector('#product-search-feedback');
const productSearchResults = document.querySelector('#product-search-results');
const productSearchResultList = document.querySelector('#product-search-result-list');
const productSearchResultCount = document.querySelector('#product-search-result-count');
const productSearchEmpty = document.querySelector('#product-search-empty');
const productSearchButton = productSearchForm?.querySelector('[type="submit"]');

const productTypeLabels = {
  general: 'Produto geral',
  medicine: 'Medicamento',
  dermocosmetic: 'Dermocosmético',
  equipment: 'Equipamento',
};

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatProductPrice(price) {
  const value = Number(price);
  return Number.isFinite(value)
    ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
    : String(price ?? '—');
}

function productSearchDetails(product) {
  const details = product.detalhes || {};
  if (product.tipo === 'medicine' && details.principio_ativo) {
    return `Princípio ativo: ${details.principio_ativo}`;
  }
  if (product.tipo === 'dermocosmetic' && details.indicacao) {
    return `Indicação: ${details.indicacao}`;
  }
  if (product.tipo === 'equipment' && details.modelo) {
    return `Modelo: ${details.modelo}`;
  }
  return product.descricao || '';
}

function renderProductSearchResults(products) {
  productSearchResultList.innerHTML = products.map((product) => `
    <li class="product-search-result">
      <div>
        <strong class="product-search-result__name">${escapeHtml(product.nome_produto)}</strong>
        <p class="product-search-result__meta">${escapeHtml(product.marca)} · ${escapeHtml(productTypeLabels[product.tipo] || 'Produto')}</p>
        <p class="product-search-result__details">${escapeHtml(productSearchDetails(product))}</p>
      </div>
      <div>
        <p class="product-search-result__price">${escapeHtml(formatProductPrice(product.preco))}</p>
        <p class="product-search-result__code">Código ${escapeHtml(product.id_produto)}</p>
      </div>
    </li>`).join('');
  productSearchResultCount.textContent = `${products.length} ${products.length === 1 ? 'produto encontrado' : 'produtos encontrados'}`;
  productSearchEmpty.textContent = 'Nenhum produto corresponde à pesquisa.';
  productSearchEmpty.hidden = products.length > 0;
  productSearchResults.hidden = false;
}

async function searchProducts(query) {
  let token;
  try {
    token = sessionStorage.getItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    redirectToLogin();
    return;
  }
  if (!token) {
    redirectToLogin();
    return;
  }

  const requestNumber = ++productSearchRequest;
  const url = new URL(PRODUCT_SEARCH_API_URL);
  url.searchParams.set('query', query);
  productSearchButton.disabled = true;
  productSearchButton.textContent = 'Buscando...';
  productSearchResults.hidden = true;
  productSearchFeedback.textContent = 'Buscando no catálogo...';
  productSearchFeedback.hidden = false;

  try {
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    let result;
    try {
      result = await response.json();
    } catch (error) {
      throw new Error('O servidor retornou uma resposta inválida. Tente novamente.');
    }

    if (response.status === 401) {
      redirectToLogin();
      return;
    }
    if (!response.ok || !result.ok || !Array.isArray(result.products)) {
      const details = result.errors ? Object.values(result.errors).join(' ') : '';
      throw new Error([result.message, details].filter(Boolean).join(' ') || 'Não foi possível pesquisar produtos.');
    }
    if (requestNumber !== productSearchRequest) return;

    productSearchFeedback.hidden = true;
    renderProductSearchResults(result.products);
  } catch (error) {
    if (requestNumber !== productSearchRequest) return;
    productSearchFeedback.textContent = error.message || 'Não foi possível conectar ao servidor.';
    productSearchFeedback.dataset.kind = 'error';
    productSearchFeedback.hidden = false;
  } finally {
    if (requestNumber === productSearchRequest) {
      productSearchButton.disabled = false;
      productSearchButton.textContent = 'Buscar';
    }
  }
}

productSearchForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  const query = productSearchInput.value.trim();

  if (!query) {
    productSearchResults.hidden = true;
    productSearchFeedback.textContent = 'Digite o nome, princípio ativo ou código do produto.';
    productSearchFeedback.dataset.kind = 'error';
    productSearchFeedback.hidden = false;
    return;
  }
  if (query.length > 100) {
    productSearchFeedback.textContent = 'A pesquisa deve ter no máximo 100 caracteres.';
    productSearchFeedback.dataset.kind = 'error';
    productSearchFeedback.hidden = false;
    return;
  }

  delete productSearchFeedback.dataset.kind;
  searchProducts(query);
});
