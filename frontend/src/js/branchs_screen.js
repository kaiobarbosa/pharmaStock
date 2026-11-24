const branches = [];

const branchList = document.querySelector('#branch-list');
const branchCount = document.querySelector('#branch-count');
const branchEmpty = document.querySelector('#branch-empty');
const branchForm = document.querySelector('#branch-form');
const branchFormPanel = document.querySelector('#branch-form-panel');
const branchCreateCard = document.querySelector('#branch-create-card');
const branchPageFeedback = document.querySelector('#branch-page-feedback');
const branchDialog = document.querySelector('#branch-confirm-dialog');
const branchIdDisplayField = document.querySelector('#branch-id-display-field');
const branchFormFeedback = document.querySelector('#branch-form-feedback');
const saveBranchButton = document.querySelector('#save-branch');
const retryBranchesButton = document.querySelector('#retry-branches');
const branchesSourceBadge = document.querySelector('#branches-source-badge');

const API_PORT = window.desktopEnv?.apiPort || '5055';
const BRANCHES_API_URL = `http://127.0.0.1:${API_PORT}/api/branches`;
const CREATE_BRANCH_URL = `http://127.0.0.1:${API_PORT}/api/create_branch`;

let activeBranchId = null;
let editingBranchId = null;
let pendingInactiveBranchId = null;
let branchesLoadState = 'loading';
let branchesLoadRequest = 0;

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function mapBranch(branchData) {
  return {
    id: String(branchData.id_filial),
    addressId: String(branchData.id_endereco),
    name: branchData.nome_filial,
    cep: branchData.cep,
    street: branchData.logradouro,
    number: String(branchData.numero),
    complement: branchData.complemento || '',
    neighborhood: branchData.bairro,
    city: branchData.cidade,
    state: branchData.estado,
    active: true,
  };
}

function formatCep(cep) {
  const digits = String(cep ?? '').replace(/\D/g, '');
  return digits.length === 8 ? `${digits.slice(0, 5)}-${digits.slice(5)}` : cep;
}

function addressSummary(branch) {
  const complement = branch.complement ? ` · ${branch.complement}` : '';
  return `${branch.street}, ${branch.number}${complement} · ${branch.neighborhood} · ${branch.city}/${branch.state}`;
}

function renderBranches() {
  const activeCount = branches.filter((branch) => branch.active).length;
  branchCount.textContent = branchesLoadState === 'loading'
    ? 'Carregando...'
    : branchesLoadState === 'error'
      ? 'Indisponível'
      : `${activeCount} ${activeCount === 1 ? 'ativa' : 'ativas'} · ${branches.length} no total`;
  branchEmpty.hidden = branches.length > 0;
  retryBranchesButton.hidden = branchesLoadState !== 'error';

  if (branches.length === 0) {
    branchEmpty.textContent = branchesLoadState === 'loading'
      ? 'Carregando filiais...'
      : branchesLoadState === 'error'
        ? 'Não foi possível obter a lista de filiais.'
        : 'Nenhuma filial cadastrada.';
  }

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
          <span class="branch-card__cep">CEP ${escapeHtml(formatCep(branch.cep))}</span>
          <span class="status-badge ${branch.active ? 'is-active' : 'is-inactive'}">${branch.active ? 'Ativa' : 'Inativa'}</span>
          <span class="branch-card__chevron" aria-hidden="true">${expanded ? '−' : '+'}</span>
        </button>
        ${expanded ? `
          <div class="branch-card__actions">
            <span class="branch-card__code">ID ${escapeHtml(branch.id)}</span>
            <div>
              <button class="text-button" type="button" data-branch-edit="${escapeHtml(branch.id)}">Editar filial</button>
              ${branch.active
                ? `<button class="text-button text-button--danger" type="button" data-branch-inactivate="${escapeHtml(branch.id)}">Inativar filial</button>`
                : `<button class="text-button" type="button" data-branch-reactivate="${escapeHtml(branch.id)}">Reativar filial</button>`}
            </div>
          </div>` : ''}
      </article>`;
  }).join('');
}

function showBranchFormError(message) {
  branchFormFeedback.textContent = message;
  branchFormFeedback.dataset.kind = 'error';
  branchFormFeedback.hidden = false;
}

function branchPayload(address) {
  return {
    nome: address.name,
    cep: address.cep,
    logradouro: address.street,
    numero: address.number,
    complemento: address.complement,
    bairro: address.neighborhood,
    cidade: address.city,
    estado: address.state,
  };
}

async function sendBranchRequest(url, method, address) {
  let response;
  try {
    response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(branchPayload(address)),
    });
  } catch (error) {
    throw new Error('Não foi possível conectar ao servidor. Confira se o backend Flask está em execução.');
  }

  let result;
  try {
    result = await response.json();
  } catch (error) {
    throw new Error('O servidor retornou uma resposta inválida. Tente novamente.');
  }

  if (!response.ok || !result.ok) {
    const details = result.errors ? Object.values(result.errors).join(' ') : '';
    throw new Error([result.message, details].filter(Boolean).join(' ') || 'Não foi possível salvar a filial.');
  }
  if (!result.branch?.id_filial || !result.branch?.id_endereco) {
    throw new Error('O servidor não retornou os identificadores da filial e do endereço.');
  }
  return result;
}

async function loadBranches() {
  const requestNumber = ++branchesLoadRequest;
  branchesLoadState = 'loading';
  branchesSourceBadge.textContent = 'Carregando do banco';
  branchPageFeedback.hidden = true;
  renderBranches();

  try {
    const response = await fetch(BRANCHES_API_URL);
    const result = await response.json();
    if (!response.ok || !result.ok || !Array.isArray(result.branches)) {
      throw new Error(result.message || 'Não foi possível carregar as filiais.');
    }
    if (requestNumber !== branchesLoadRequest) return;

    branches.splice(0, branches.length, ...result.branches.map(mapBranch));
    branchesLoadState = 'ready';
    branchesSourceBadge.textContent = 'Dados do banco';
    renderBranches();
  } catch (error) {
    if (requestNumber !== branchesLoadRequest) return;
    branchesLoadState = 'error';
    branchesSourceBadge.textContent = 'Banco indisponível';
    branchPageFeedback.textContent = error.message || 'Não foi possível carregar as filiais.';
    branchPageFeedback.dataset.kind = 'error';
    branchPageFeedback.hidden = false;
    renderBranches();
  }
}

function closeBranchForm() {
  branchFormPanel.hidden = true;
  branchCreateCard.hidden = false;
  branchForm.reset();
  editingBranchId = null;
  branchIdDisplayField.hidden = true;
  branchFormFeedback.hidden = true;
  branchFormFeedback.textContent = '';
  delete branchFormFeedback.dataset.kind;
}

function openNewBranchForm() {
  editingBranchId = null;
  branchForm.reset();
  document.querySelector('#branch-id').value = '';
  branchIdDisplayField.hidden = true;
  document.querySelector('#branch-form-kicker').textContent = 'Novo endereço';
  document.querySelector('#branch-form-title').textContent = 'Cadastrar filial';
  saveBranchButton.textContent = 'Cadastrar filial';
  branchFormFeedback.hidden = true;
  branchFormFeedback.textContent = '';
  branchCreateCard.hidden = true;
  branchFormPanel.hidden = false;
  document.querySelector('#branch-cep').focus();
}

function openEditBranchForm(branch) {
  editingBranchId = branch.id;
  branchForm.reset();
  branchForm.elements.id.value = branch.id;
  branchForm.elements.name.value = branch.name;
  branchForm.elements.cep.value = formatCep(branch.cep);
  branchForm.elements.street.value = branch.street;
  branchForm.elements.number.value = branch.number;
  branchForm.elements.complement.value = branch.complement;
  branchForm.elements.neighborhood.value = branch.neighborhood;
  branchForm.elements.city.value = branch.city;
  branchForm.elements.state.value = branch.state;
  document.querySelector('#branch-id-display').value = branch.id;
  branchIdDisplayField.hidden = false;
  document.querySelector('#branch-form-kicker').textContent = 'Editar filial';
  document.querySelector('#branch-form-title').textContent = `Editar ${branch.name}`;
  saveBranchButton.textContent = 'Salvar alterações';
  branchFormFeedback.hidden = true;
  branchFormFeedback.textContent = '';
  branchCreateCard.hidden = true;
  branchFormPanel.hidden = false;
  branchFormPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  document.querySelector('#branch-cep').focus();
}

document.querySelector('#open-branch-form').addEventListener('click', openNewBranchForm);
document.querySelector('#close-branch-form').addEventListener('click', closeBranchForm);
document.querySelector('#cancel-branch-form').addEventListener('click', closeBranchForm);
retryBranchesButton.addEventListener('click', loadBranches);

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

branchForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(branchForm).entries());
  const address = {
    name: values.name.trim(),
    cep: values.cep.trim(),
    street: values.street.trim(),
    number: values.number.trim(),
    complement: values.complement.trim(),
    neighborhood: values.neighborhood.trim(),
    city: values.city.trim(),
    state: values.state,
  };
  const branchIdBeingEdited = editingBranchId;

  saveBranchButton.disabled = true;
  saveBranchButton.textContent = branchIdBeingEdited ? 'Salvando...' : 'Cadastrando...';
  branchFormFeedback.hidden = true;

  try {
    const result = branchIdBeingEdited
      ? await sendBranchRequest(
        `${BRANCHES_API_URL}/${encodeURIComponent(branchIdBeingEdited)}`,
        'PUT',
        address,
      )
      : await sendBranchRequest(CREATE_BRANCH_URL, 'POST', address);
    const savedBranch = mapBranch(result.branch);

    if (branchIdBeingEdited) {
      const index = branches.findIndex((branch) => branch.id === branchIdBeingEdited);
      if (index !== -1) {
        savedBranch.active = branches[index].active;
        branches.splice(index, 1, savedBranch);
      }
    } else {
      branchesLoadRequest += 1;
      branches.unshift(savedBranch);
      branchesLoadState = 'ready';
      branchesSourceBadge.textContent = 'Dados do banco';
    }

    activeBranchId = savedBranch.id;
    branchPageFeedback.textContent = result.message;
    branchPageFeedback.hidden = false;
    branchPageFeedback.dataset.kind = 'success';
    closeBranchForm();
    renderBranches();
  } catch (error) {
    showBranchFormError(error.message);
  } finally {
    saveBranchButton.disabled = false;
    saveBranchButton.textContent = editingBranchId ? 'Salvar alterações' : 'Cadastrar filial';
  }
});

document.querySelector('#branch-confirm-cancel').addEventListener('click', () => branchDialog.close());
document.querySelector('#branch-confirm-accept').addEventListener('click', () => {
  const branch = branches.find((item) => item.id === pendingInactiveBranchId);
  if (branch) {
    branch.active = false;
    activeBranchId = branch.id;
    branchPageFeedback.textContent = `${branch.name} foi marcada como inativa neste protótipo.`;
    branchPageFeedback.dataset.kind = 'success';
    branchPageFeedback.hidden = false;
  }
  pendingInactiveBranchId = null;
  branchDialog.close();
  renderBranches();
});

renderBranches();
loadBranches();
