const productViews = document.querySelectorAll('[data-product-view]');
const productForm = document.querySelector('#product-form');
const productType = document.querySelector('#product-type');
const specificFields = document.querySelector('#product-specific-fields');
const specificHint = document.querySelector('#product-specific-hint');
const productFeedback = document.querySelector('#products-feedback');
const productFormFeedback = document.querySelector('#product-form-feedback');
const productBranch = document.querySelector('#product-branch');
const saveProductButton = productForm.querySelector('[type="submit"]');
const inventoryForm = document.querySelector('#inventory-filter-form');
const inventoryList = document.querySelector('#inventory-list');
const inventoryEmpty = document.querySelector('#inventory-empty');
const inventoryCount = document.querySelector('#inventory-result-count');
const inventoryQuery = document.querySelector('#inventory-query');
const inventoryBranch = document.querySelector('#inventory-branch');
const productsSource = document.querySelector('#products-source');
const retryProductsButton = document.querySelector('#retry-products');
const API_PORT = window.desktopEnv?.apiPort || '5055';
const PRODUCTS_API_URL = `http://127.0.0.1:${API_PORT}/api/products`;
const PRODUCTS_FILTER_API_URL = `http://127.0.0.1:${API_PORT}/api/products/filter`;
const BRANCHES_API_URL = `http://127.0.0.1:${API_PORT}/api/branches`;
const ACCESS_TOKEN_KEY = 'pharmaStock.accessToken';
const LOGIN_SCREEN_URL = '../../public/index.html';

const categoryFields = {
  general: [],
  medicine: [
    ['activeIngredient', 'Princípio ativo', 'text'],
    ['pharmaceuticalForm', 'Forma farmacêutica', 'text'],
    ['concentration', 'Concentração', 'text'],
    ['prescriptionBand', 'Tarja', 'select', ['Sem tarja', 'Tarja vermelha', 'Tarja preta']],
    ['prescriptionRequired', 'Receita', 'select', ['Não', 'Sim']],
    ['classification', 'Tipagem', 'text'],
  ],
  dermocosmetic: [
    ['skinType', 'Tipo de pele', 'text'],
    ['volume', 'Volume', 'text'],
    ['sunProtectionFactor', 'Fator de proteção', 'text'],
    ['indication', 'Indicação', 'text'],
  ],
  equipment: [
    ['model', 'Modelo', 'text'],
    ['manufacturer', 'Fabricante', 'text'],
    ['specifications', 'Especificações', 'text'],
    ['warranty', 'Garantia', 'text'],
  ],
};

const categoryLabels = {
  general: 'Geral',
  dermocosmetic: 'Dermocosméticos',
  medicine: 'Medicamentos',
  equipment: 'Equipamentos',
};

let branchesLoadState = 'loading';
let products = [];
let productsLoadState = 'idle';
let productsLoadRequest = 0;
let productsLoadMessage = '';
let branches = [];
let activeProductFilters = { query: '', branchId: 'all' };

function getAccessToken() {
  try {
    return sessionStorage.getItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    return null;
  }
}

function expireSession() {
  try {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    // A navegação ainda encerra a sessão atual se o armazenamento estiver indisponível.
  }
  window.location.replace(LOGIN_SCREEN_URL);
}

function showProductFormFeedback(message, kind = 'error') {
  productFormFeedback.textContent = message;
  productFormFeedback.dataset.kind = kind;
  productFormFeedback.hidden = false;
}

function clearProductFormFeedback() {
  productFormFeedback.textContent = '';
  productFormFeedback.hidden = true;
  delete productFormFeedback.dataset.kind;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function setProductView(viewName) {
  productViews.forEach((view) => {
    view.hidden = view.dataset.productView !== viewName;
  });
  productFeedback.hidden = true;
  document.querySelector('.products-content').scrollTop = 0;
}

function createCategoryInput([name, label, type, options]) {
  const maxLengths = {
    activeIngredient: 50,
    pharmaceuticalForm: 50,
    concentration: 50,
    classification: 50,
    skinType: 100,
    volume: 50,
    sunProtectionFactor: 50,
    indication: 20,
    model: 50,
    manufacturer: 50,
    specifications: 100,
    warranty: 50,
  };
  const maxLength = maxLengths[name];
  if (type === 'select') {
    const optionMarkup = options.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join('');
    return `<div class="field"><label for="product-extra-${name}">${escapeHtml(label)}</label><select id="product-extra-${name}" name="${escapeHtml(name)}" required><option value="" selected disabled>Selecione uma opção</option>${optionMarkup}</select></div>`;
  }
  return `<div class="field"><label for="product-extra-${name}">${escapeHtml(label)}</label><input id="product-extra-${name}" name="${escapeHtml(name)}"${maxLength ? ` maxlength="${maxLength}"` : ''} required /></div>`;
}

async function loadProductBranches() {
  productBranch.disabled = true;
  productBranch.innerHTML = '<option value="">Carregando filiais...</option>';

  try {
    const response = await fetch(BRANCHES_API_URL);
    const result = await response.json();
    if (!response.ok || !result.ok || !Array.isArray(result.branches)) {
      throw new Error(result.message || 'Não foi possível carregar as filiais.');
    }

    branches = result.branches;
    productBranch.innerHTML = '<option value="">Selecione uma filial</option>';
    branches.forEach((branch) => {
      const option = document.createElement('option');
      option.value = String(branch.id_filial);
      option.textContent = branch.nome_filial;
      productBranch.append(option);
    });
    if (branches.length === 0) {
      productBranch.innerHTML = '<option value="">Nenhuma filial cadastrada</option>';
    }
    branchesLoadState = 'ready';
    productBranch.disabled = branches.length === 0;
    populateProductBranchFilter();
  } catch (error) {
    branches = [];
    branchesLoadState = 'error';
    productBranch.innerHTML = '<option value="">Não foi possível carregar filiais</option>';
    productBranch.disabled = true;
  }
}

async function readJsonResponse(response) {
  try {
    return await response.json();
  } catch (error) {
    throw new Error('O servidor retornou uma resposta inválida. Tente novamente.');
  }
}

async function createProduct(values) {
  const token = getAccessToken();
  if (!token) {
    expireSession();
    return;
  }
  if (branchesLoadState !== 'ready' || !productBranch.value) {
    showProductFormFeedback('Carregue e selecione uma filial antes de cadastrar o produto.');
    return;
  }

  saveProductButton.disabled = true;
  saveProductButton.textContent = 'Cadastrando...';
  clearProductFormFeedback();

  try {
    const response = await fetch(PRODUCTS_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(values),
    });
    const result = await readJsonResponse(response);

    if (response.status === 401) {
      expireSession();
      return;
    }
    if (!response.ok || !result.ok) {
      const details = result.errors ? Object.values(result.errors).join(' ') : '';
      throw new Error([result.message, details].filter(Boolean).join(' ') || 'Não foi possível cadastrar o produto.');
    }

    productForm.reset();
    productType.value = 'general';
    inventoryQuery.value = '';
    inventoryBranch.value = 'all';
    renderSpecificFields();
    products = [];
    productsLoadState = 'idle';
    activeProductFilters = { query: '', branchId: 'all' };
    setProductView('overview');
    productFeedback.textContent = `${result.product.nome} foi cadastrado com sucesso.`;
    productFeedback.hidden = false;
  } catch (error) {
    showProductFormFeedback(error.message || 'Não foi possível conectar ao servidor. Confira se o backend está em execução.');
  } finally {
    saveProductButton.disabled = false;
    saveProductButton.textContent = 'Cadastrar produto';
  }
}

function renderSpecificFields() {
  const fields = categoryFields[productType.value] || [];
  specificFields.innerHTML = fields.map(createCategoryInput).join('');
  specificHint.hidden = fields.length > 0;
  specificFields.hidden = fields.length === 0;
}

function populateProductBranchFilter() {
  const selectedBranch = inventoryBranch.value;
  inventoryBranch.innerHTML = '<option value="all">Todas as filiais</option>';
  [...branches]
    .sort((left, right) => left.nome_filial.localeCompare(right.nome_filial, 'pt-BR'))
    .forEach((branch) => {
      const option = document.createElement('option');
      option.value = String(branch.id_filial);
      option.textContent = branch.nome_filial;
      inventoryBranch.append(option);
    });

  if (branches.some((branch) => String(branch.id_filial) === selectedBranch)) {
    inventoryBranch.value = selectedBranch;
  }
}

function productCategoryDetails(product) {
  const details = product.detalhes || {};
  const valuesByType = {
    medicine: [
      ['Princípio ativo', details.principio_ativo],
      ['Forma', details.forma_farmaceutica],
      ['Concentração', details.concentracao],
      ['Tarja', details.tarja],
      ['Receita', details.receita === null || details.receita === undefined ? null : details.receita ? 'Sim' : 'Não'],
      ['Tipagem', details.tipagem],
    ],
    dermocosmetic: [
      ['Tipo de pele', details.tipo_pele],
      ['Volume', details.volume],
      ['Fator de proteção', details.fator_protecao],
      ['Indicação', details.indicacao],
    ],
    equipment: [
      ['Modelo', details.modelo],
      ['Fabricante', details.fabricante],
      ['Especificações', details.especificacoes],
      ['Garantia', details.garantia],
    ],
  };
  const fields = valuesByType[product.tipo] || [];
  const text = fields
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .map(([label, value]) => `${label}: ${value}`)
    .join(' · ');
  return text || 'Produto geral';
}

function formatProductPrice(price) {
  const value = Number(price);
  return Number.isFinite(value)
    ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
    : String(price ?? '—');
}

function renderProducts() {
  retryProductsButton.hidden = productsLoadState !== 'error';
  if (productsLoadState !== 'ready') {
    inventoryList.innerHTML = '';
    inventoryCount.textContent = productsLoadState === 'loading' ? 'Carregando...' : '';
    productsSource.textContent = productsLoadState === 'error' ? 'Banco indisponível' : 'Carregando produtos do banco...';
    inventoryEmpty.textContent = productsLoadState === 'error'
      ? productsLoadMessage || 'Não foi possível carregar os produtos cadastrados.'
      : 'Carregando produtos...';
    inventoryEmpty.hidden = false;
    return;
  }

  inventoryList.innerHTML = products.map((product) => {
    const name = escapeHtml(product.nome_produto);
    const branches = (product.filiais || []).map((branch) => branch.nome_filial).join(', ');
    const category = categoryLabels[product.tipo] || 'Produto';
    return `
      <tr>
        <td><span class="product-id">${escapeHtml(product.id_produto)}</span></td>
        <td><span class="inventory-product-name">${name}</span><small>${escapeHtml(product.marca)}</small><small>${escapeHtml(product.descricao)}</small></td>
        <td>${escapeHtml(category)}</td>
        <td class="product-details-cell">${escapeHtml(productCategoryDetails(product))}</td>
        <td>${escapeHtml(formatProductPrice(product.preco))}</td>
        <td><span class="quantity-pill">${escapeHtml(product.quantidade)}</span></td>
        <td>${escapeHtml(branches || 'Sem filial vinculada')}</td>
        <td>${escapeHtml(product.codigo_de_barras)}</td>
        <td><div class="catalog-actions"><button class="catalog-action-button" type="button" disabled title="Disponível em uma etapa futura" aria-label="Editar ${name}">Editar</button><button class="catalog-action-button catalog-action-button--danger" type="button" disabled title="Disponível em uma etapa futura" aria-label="Inativar ${name}">Inativar</button></div></td>
      </tr>`;
  }).join('');

  inventoryCount.textContent = `${products.length} ${products.length === 1 ? 'produto' : 'produtos'}`;
  const selectedBranch = branches.find(
    (branch) => String(branch.id_filial) === activeProductFilters.branchId,
  );
  const appliedFilters = [
    activeProductFilters.query ? `Texto: ${activeProductFilters.query}` : '',
    selectedBranch ? `Filial: ${selectedBranch.nome_filial}` : '',
  ].filter(Boolean).join(' · ');
  productsSource.textContent = `${products.length} ${products.length === 1 ? 'resultado' : 'resultados'} do banco de dados${appliedFilters ? ` · ${appliedFilters}` : ''}.`;
  inventoryEmpty.textContent = products.length === 0
    ? 'Nenhum produto cadastrado.'
    : 'Nenhum produto corresponde aos filtros selecionados.';
  inventoryEmpty.hidden = products.length > 0;
}

async function loadProducts(filters = activeProductFilters) {
  const requestNumber = ++productsLoadRequest;
  const token = getAccessToken();
  if (!token) {
    expireSession();
    return false;
  }

  const normalizedFilters = {
    query: String(filters.query || '').trim(),
    branchId: filters.branchId || 'all',
  };
  activeProductFilters = normalizedFilters;
  productsLoadMessage = '';

  productsLoadState = 'loading';
  products = [];
  renderProducts();

  try {
    const hasTextFilter = Boolean(normalizedFilters.query);
    const hasBranchFilter = normalizedFilters.branchId !== 'all';
    const url = hasTextFilter || hasBranchFilter
      ? new URL(PRODUCTS_FILTER_API_URL)
      : new URL(PRODUCTS_API_URL);
    if (hasTextFilter) url.searchParams.set('query', normalizedFilters.query);
    if (hasBranchFilter) url.searchParams.set('branch_id', normalizedFilters.branchId);

    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const result = await readJsonResponse(response);

    if (response.status === 401) {
      expireSession();
      return false;
    }
    if (!response.ok || !result.ok || !Array.isArray(result.products)) {
      throw new Error(result.message || 'Não foi possível carregar os produtos.');
    }
    if (requestNumber !== productsLoadRequest) return false;

    products = result.products;
    productsLoadState = 'ready';
    renderProducts();
    return true;
  } catch (error) {
    if (requestNumber !== productsLoadRequest) return false;
    productsLoadState = 'error';
    productsLoadMessage = error.message || 'Não foi possível pesquisar os produtos.';
    renderProducts();
    return false;
  }
}

function applyProductFilters() {
  loadProducts({
    query: inventoryQuery.value,
    branchId: inventoryBranch.value,
  });
}

document.querySelector('#start-product-create').addEventListener('click', () => {
  productForm.reset();
  productType.value = 'general';
  clearProductFormFeedback();
  renderSpecificFields();
  if (branchesLoadState === 'error') {
    showProductFormFeedback('Não foi possível carregar filiais. Confira a conexão e atualize a tela.');
  }
  setProductView('create');
});

document.querySelector('#open-inventory').addEventListener('click', () => {
  setProductView('stock');
  if (productsLoadState === 'ready') renderProducts();
  else loadProducts();
});

retryProductsButton.addEventListener('click', () => loadProducts(activeProductFilters));

document.querySelectorAll('[data-product-view-open]').forEach((button) => {
  button.addEventListener('click', () => setProductView(button.dataset.productViewOpen));
});

productType.addEventListener('change', renderSpecificFields);

inventoryForm.addEventListener('submit', (event) => {
  event.preventDefault();
  applyProductFilters();
});

inventoryBranch.addEventListener('change', applyProductFilters);

productForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(productForm).entries());
  createProduct(values);
});

renderSpecificFields();
loadProductBranches();
