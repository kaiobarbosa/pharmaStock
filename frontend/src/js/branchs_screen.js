const branches = [
  { id: 'FIL-001', name: 'Filial Centro', cep: '01001-000', street: 'Praça da Sé', number: '120', complement: 'Loja 02', neighborhood: 'Sé', city: 'São Paulo', state: 'SP', active: true },
  { id: 'FIL-002', name: 'Filial Jardins', cep: '01415-001', street: 'Rua Augusta', number: '845', complement: '', neighborhood: 'Cerqueira César', city: 'São Paulo', state: 'SP', active: true },
  { id: 'FIL-003', name: 'Filial Norte', cep: '02011-000', street: 'Rua Voluntários da Pátria', number: '2100', complement: 'Térreo', neighborhood: 'Santana', city: 'São Paulo', state: 'SP', active: true },
];

const branchList = document.querySelector('#branch-list');
const branchCount = document.querySelector('#branch-count');
const branchEmpty = document.querySelector('#branch-empty');
const branchForm = document.querySelector('#branch-form');
const branchFormPanel = document.querySelector('#branch-form-panel');
const branchCreateCard = document.querySelector('#branch-create-card');
const branchPageFeedback = document.querySelector('#branch-page-feedback');
const branchDialog = document.querySelector('#branch-confirm-dialog');
const branchIdDisplayField = document.querySelector('#branch-id-display-field');

let activeBranchId = null;
let editingBranchId = null;
let pendingInactiveBranchId = null;
let nextBranchNumber = branches.length + 1;

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function addressSummary(branch) {
  const complement = branch.complement ? ` · ${branch.complement}` : '';
  return `${branch.street}, ${branch.number}${complement} · ${branch.neighborhood} · ${branch.city}/${branch.state}`;
}

function renderBranches() {
  const activeCount = branches.filter((branch) => branch.active).length;
  branchCount.textContent = `${activeCount} ativas · ${branches.length} no total`;
  branchEmpty.hidden = branches.length > 0;

  branchList.innerHTML = branches.map((branch) => {
    const expanded = activeBranchId === branch.id;
    return `
      <article class="branch-card${branch.active ? '' : ' is-inactive'}">
        <button class="branch-card__summary" type="button" data-branch-toggle="${escapeHtml(branch.id)}" aria-expanded="${expanded}">
          <span class="branch-card__icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 21V5l8-2v18M12 9h8v12M2 21h20M7 8h2m-2 4h2m-2 4h2m8-1h1m-1 3h1" /></svg></span>
          <span class="branch-card__identity">
            <strong>${escapeHtml(branch.name)}</strong>
            <span>${escapeHtml(addressSummary(branch))}</span>
          </span>
          <span class="branch-card__cep">CEP ${escapeHtml(branch.cep)}</span>
          <span class="status-badge ${branch.active ? 'is-active' : 'is-inactive'}">${branch.active ? 'Ativa' : 'Inativa'}</span>
          <span class="branch-card__chevron" aria-hidden="true">${expanded ? '−' : '+'}</span>
        </button>
        ${expanded ? `
          <div class="branch-card__actions">
            <span class="branch-card__code">ID ${escapeHtml(branch.id)}</span>
            <div>
              <button class="text-button" type="button" data-branch-edit="${escapeHtml(branch.id)}">Editar endereço</button>
              ${branch.active
                ? `<button class="text-button text-button--danger" type="button" data-branch-inactivate="${escapeHtml(branch.id)}">Inativar filial</button>`
                : `<button class="text-button" type="button" data-branch-reactivate="${escapeHtml(branch.id)}">Reativar filial</button>`}
            </div>
          </div>` : ''}
      </article>`;
  }).join('');
}

function closeBranchForm() {
  branchFormPanel.hidden = true;
  branchCreateCard.hidden = false;
  branchForm.reset();
  editingBranchId = null;
  branchIdDisplayField.hidden = true;
}

function openNewBranchForm() {
  editingBranchId = null;
  branchForm.reset();
  document.querySelector('#branch-id').value = '';
  branchIdDisplayField.hidden = true;
  document.querySelector('#branch-form-kicker').textContent = 'Novo endereço';
  document.querySelector('#branch-form-title').textContent = 'Cadastrar filial';
  document.querySelector('#save-branch').textContent = 'Cadastrar filial';
  branchCreateCard.hidden = true;
  branchFormPanel.hidden = false;
  document.querySelector('#branch-cep').focus();
}

function openEditBranchForm(branch) {
  editingBranchId = branch.id;
  branchForm.reset();
  branchForm.elements.id.value = branch.id;
  branchForm.elements.cep.value = branch.cep;
  branchForm.elements.street.value = branch.street;
  branchForm.elements.number.value = branch.number;
  branchForm.elements.complement.value = branch.complement;
  branchForm.elements.neighborhood.value = branch.neighborhood;
  branchForm.elements.city.value = branch.city;
  branchForm.elements.state.value = branch.state;
  document.querySelector('#branch-id-display').value = branch.id;
  branchIdDisplayField.hidden = false;
  document.querySelector('#branch-form-kicker').textContent = 'Editar endereço';
  document.querySelector('#branch-form-title').textContent = `Editar ${branch.name}`;
  document.querySelector('#save-branch').textContent = 'Salvar alterações';
  branchCreateCard.hidden = true;
  branchFormPanel.hidden = false;
  branchFormPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  document.querySelector('#branch-cep').focus();
}

document.querySelector('#open-branch-form').addEventListener('click', openNewBranchForm);
document.querySelector('#close-branch-form').addEventListener('click', closeBranchForm);
document.querySelector('#cancel-branch-form').addEventListener('click', closeBranchForm);

branchList.addEventListener('click', (event) => {
  const toggle = event.target.closest('[data-branch-toggle]');
  if (toggle) {
    activeBranchId = activeBranchId === toggle.dataset.branchToggle ? null : toggle.dataset.branchToggle;
    renderBranches();
    return;
  }

  const editButton = event.target.closest('[data-branch-edit]');
  if (editButton) {
    const branch = branches.find((item) => item.id === editButton.dataset.branchEdit);
    if (branch) openEditBranchForm(branch);
    return;
  }

  const inactivateButton = event.target.closest('[data-branch-inactivate]');
  if (inactivateButton) {
    pendingInactiveBranchId = inactivateButton.dataset.branchInactivate;
    const branch = branches.find((item) => item.id === pendingInactiveBranchId);
    document.querySelector('#branch-confirm-message').textContent = `Deseja inativar ${branch.name}?`;
    branchDialog.showModal();
    return;
  }

  const reactivateButton = event.target.closest('[data-branch-reactivate]');
  if (reactivateButton) {
    const branch = branches.find((item) => item.id === reactivateButton.dataset.branchReactivate);
    if (branch) {
      branch.active = true;
      activeBranchId = branch.id;
      renderBranches();
    }
  }
});

branchForm.elements.cep.addEventListener('input', (event) => {
  const digits = event.target.value.replace(/\D/g, '').slice(0, 8);
  event.target.value = digits.length > 5 ? `${digits.slice(0, 5)}-${digits.slice(5)}` : digits;
});

branchForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(branchForm).entries());
  const address = {
    cep: values.cep.trim(),
    street: values.street.trim(),
    number: values.number.trim(),
    complement: values.complement.trim(),
    neighborhood: values.neighborhood.trim(),
    city: values.city.trim(),
    state: values.state,
    active: true,
  };

  if (editingBranchId) {
    const branch = branches.find((item) => item.id === editingBranchId);
    Object.assign(branch, address);
    branchPageFeedback.textContent = `O endereço de ${branch.name} foi atualizado neste protótipo.`;
    activeBranchId = branch.id;
  } else {
    const branch = {
      ...address,
      id: `FIL-${String(nextBranchNumber).padStart(3, '0')}`,
      name: `Filial ${address.neighborhood}`,
    };
    nextBranchNumber += 1;
    branches.unshift(branch);
    branchPageFeedback.textContent = `${branch.name} foi adicionada à lista demonstrativa.`;
    activeBranchId = branch.id;
  }

  branchPageFeedback.hidden = false;
  closeBranchForm();
  renderBranches();
});

document.querySelector('#branch-confirm-cancel').addEventListener('click', () => branchDialog.close());
document.querySelector('#branch-confirm-accept').addEventListener('click', () => {
  const branch = branches.find((item) => item.id === pendingInactiveBranchId);
  if (branch) {
    branch.active = false;
    activeBranchId = branch.id;
    branchPageFeedback.textContent = `${branch.name} foi marcada como inativa neste protótipo.`;
    branchPageFeedback.hidden = false;
  }
  pendingInactiveBranchId = null;
  branchDialog.close();
  renderBranches();
});

renderBranches();
