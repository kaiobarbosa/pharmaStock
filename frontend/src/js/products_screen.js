const productViews = document.querySelectorAll('[data-product-view]');
const productForm = document.querySelector('#product-form');
const productType = document.querySelector('#product-type');
const specificFields = document.querySelector('#product-specific-fields');
const specificHint = document.querySelector('#product-specific-hint');
const productFeedback = document.querySelector('#products-feedback');
const inventoryForm = document.querySelector('#inventory-filter-form');
const inventoryList = document.querySelector('#inventory-list');
const inventoryEmpty = document.querySelector('#inventory-empty');
const inventoryCount = document.querySelector('#inventory-result-count');

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
    ['relatedProductId', 'ID do produto relacionado', 'text'],
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

const inventory = [
  { id: 'PRD-001', name: 'Dipirona monoidratada 500 mg', quantity: 124, barcode: '7896004700018', branch: 'Filial Centro', type: 'medicine', brand: 'Medley', price: 8.9 },
  { id: 'PRD-002', name: 'Protetor solar facial FPS 50', quantity: 28, barcode: '7891010245823', branch: 'Filial Jardins', type: 'dermocosmetic', brand: 'Eucerin', price: 79.9 },
  { id: 'PRD-003', name: 'Termômetro digital', quantity: 16, barcode: '7898636190122', branch: 'Filial Norte', type: 'equipment', brand: 'G-Tech', price: 34.5 },
  { id: 'PRD-004', name: 'Vitamina C 1 g', quantity: 67, barcode: '7896422501107', branch: 'Filial Centro', type: 'medicine', brand: 'Cimed', price: 18.75 },
  { id: 'PRD-005', name: 'Creme hidratante calmante', quantity: 42, barcode: '7891150084521', branch: 'Filial Jardins', type: 'dermocosmetic', brand: 'Nivea', price: 29.9 },
  { id: 'PRD-006', name: 'Algodão hidrófilo 100 g', quantity: 83, barcode: '7896110001451', branch: 'Filial Norte', type: 'general', brand: 'Cremer', price: 7.2 },
];

let nextProductNumber = inventory.length + 1;

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
  if (type === 'select') {
    const optionMarkup = options.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join('');
    return `<div class="field"><label for="product-extra-${name}">${escapeHtml(label)}</label><select id="product-extra-${name}" name="${escapeHtml(name)}" required>${optionMarkup}</select></div>`;
  }
  return `<div class="field"><label for="product-extra-${name}">${escapeHtml(label)}</label><input id="product-extra-${name}" name="${escapeHtml(name)}" required /></div>`;
}

function renderSpecificFields() {
  const fields = categoryFields[productType.value] || [];
  specificFields.innerHTML = fields.map(createCategoryInput).join('');
  specificHint.hidden = fields.length > 0;
  specificFields.hidden = fields.length === 0;
}

function renderInventory() {
  const query = document.querySelector('#inventory-query').value.trim().toLocaleLowerCase('pt-BR');
  const selectedBranch = document.querySelector('#inventory-branch').value;
  const results = inventory.filter((product) => {
    const matchesQuery = !query
      || product.name.toLocaleLowerCase('pt-BR').includes(query)
      || product.barcode.includes(query)
      || product.id.toLocaleLowerCase('pt-BR').includes(query);
    const matchesBranch = selectedBranch === 'all' || product.branch === selectedBranch;
    return matchesQuery && matchesBranch;
  });

  inventoryList.innerHTML = results.map((product) => `
    <tr>
      <td><span class="product-id">${escapeHtml(product.id)}</span></td>
      <td><span class="inventory-product-name">${escapeHtml(product.name)}</span><small>${escapeHtml(product.brand)} · ${escapeHtml(categoryLabels[product.type])}</small></td>
      <td><span class="quantity-pill">${escapeHtml(product.quantity)}</span></td>
      <td>${escapeHtml(product.barcode)}</td>
    </tr>`).join('');
  inventoryCount.textContent = `${results.length} ${results.length === 1 ? 'produto' : 'produtos'}`;
  inventoryEmpty.hidden = results.length > 0;
}

document.querySelector('#start-product-create').addEventListener('click', () => {
  productForm.reset();
  productType.value = 'general';
  renderSpecificFields();
  setProductView('create');
});

document.querySelector('#open-inventory').addEventListener('click', () => {
  renderInventory();
  setProductView('stock');
});

document.querySelectorAll('[data-product-view-open]').forEach((button) => {
  button.addEventListener('click', () => setProductView(button.dataset.productViewOpen));
});

productType.addEventListener('change', renderSpecificFields);

inventoryForm.addEventListener('submit', (event) => {
  event.preventDefault();
  renderInventory();
});

document.querySelector('#inventory-query').addEventListener('input', renderInventory);
document.querySelector('#inventory-branch').addEventListener('change', renderInventory);

productForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(productForm).entries());
  const product = {
    ...values,
    id: `PRD-${String(nextProductNumber).padStart(3, '0')}`,
    quantity: Number(values.quantity),
    price: Number(values.price),
    type: values.type,
  };
  nextProductNumber += 1;
  inventory.unshift(product);
  productForm.reset();
  productType.value = 'general';
  renderSpecificFields();
  setProductView('overview');
  productFeedback.textContent = `${product.name} foi incluído no estoque demonstrativo.`;
  productFeedback.hidden = false;
});

renderSpecificFields();
