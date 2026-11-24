const roleLabels = {
  diretor: 'Diretor',
  director: 'Diretor',
  gerente: 'Gerente',
  manager: 'Gerente',
  farmaceutico: 'Farmacêutico',
  pharmacist: 'Farmacêutico',
  atendente: 'Atendente',
  attendant: 'Atendente',
};

const API_PORT = window.desktopEnv?.apiPort || '5055';
const EMPLOYEES_API_URL = `http://127.0.0.1:${API_PORT}/api/employees`;
const BRANCHES_API_URL = `http://127.0.0.1:${API_PORT}/api/branches`;
const ACCESS_TOKEN_KEY = 'pharmaStock.accessToken';
const LOGIN_SCREEN_URL = '../../public/index.html';

const employees = [];
const employeeList = document.querySelector('#employee-list');
const employeeCount = document.querySelector('#employee-count');
const employeeEmpty = document.querySelector('#employee-empty');
const employeeFormPanel = document.querySelector('#employee-form-panel');
const employeeCreateCard = document.querySelector('#employee-create-card');
const employeeForm = document.querySelector('#employee-form');
const employeeRole = document.querySelector('#employee-role');
const employeePassword = document.querySelector('#employee-password');
const employeeCpf = document.querySelector('#employee-cpf');
const employeeBranch = document.querySelector('#employee-branch');
const employeePageFeedback = document.querySelector('#employee-page-feedback');
const employeeFormFeedback = document.querySelector('#employee-form-feedback');
const saveEmployeeButton = document.querySelector('#save-employee');
const employeesSourceBadge = document.querySelector('#employees-source-badge');
const retryEmployeesButton = document.querySelector('#retry-employees');

let branches = [];
let branchesLoadState = 'loading';
let employeesLoadState = 'loading';
let employeesLoadRequest = 0;

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function normalizeRole(role) {
  return String(role ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();
}

function mapEmployee(employee) {
  const role = normalizeRole(employee.tipo_usuario);
  return {
    firstName: employee.nome,
    lastName: employee.sobrenome,
    role,
    email: employee.email,
    branch: employee.filial || 'Diretoria',
  };
}

function initials(employee) {
  const first = String(employee.firstName ?? '').trim().charAt(0);
  const last = String(employee.lastName ?? '').trim().charAt(0);
  return `${first}${last}`.toLocaleUpperCase('pt-BR') || '??';
}

function showFormFeedback(message, kind = 'error') {
  employeeFormFeedback.textContent = message;
  employeeFormFeedback.dataset.kind = kind;
  employeeFormFeedback.hidden = false;
}

function clearFormFeedback() {
  employeeFormFeedback.textContent = '';
  employeeFormFeedback.hidden = true;
  delete employeeFormFeedback.dataset.kind;
}

function showPageFeedback(message, kind = 'success') {
  employeePageFeedback.textContent = message;
  employeePageFeedback.dataset.kind = kind;
  employeePageFeedback.hidden = false;
}

function clearPageFeedback() {
  employeePageFeedback.textContent = '';
  employeePageFeedback.hidden = true;
  delete employeePageFeedback.dataset.kind;
}

function renderEmployees() {
  employeeCount.textContent = employeesLoadState === 'loading'
    ? 'Carregando...'
    : employeesLoadState === 'error'
      ? 'Indisponível'
      : `${employees.length} ${employees.length === 1 ? 'funcionário' : 'funcionários'}`;

  retryEmployeesButton.hidden = employeesLoadState !== 'error';
  employeeEmpty.hidden = employees.length > 0;
  if (employees.length === 0) {
    employeeEmpty.textContent = employeesLoadState === 'loading'
      ? 'Carregando funcionários...'
      : employeesLoadState === 'error'
        ? 'Não foi possível carregar os funcionários.'
        : 'Nenhum funcionário cadastrado.';
  }

  employeeList.innerHTML = employees.map((employee) => `
    <article class="employee-card">
      <div class="employee-card__summary">
        <span class="employee-avatar" aria-hidden="true">${escapeHtml(initials(employee))}</span>
        <span class="employee-card__identity">
          <strong>${escapeHtml(employee.firstName)} ${escapeHtml(employee.lastName)}</strong>
          <span>${escapeHtml(roleLabels[employee.role] || employee.role)} <span aria-hidden="true">·</span> ${escapeHtml(employee.branch)}</span>
        </span>
        <span class="employee-card__email">${escapeHtml(employee.email)}</span>
      </div>
    </article>`).join('');
}

function updateEmployeeFields() {
  const isDirector = employeeRole.value === 'director';
  const isPharmacist = employeeRole.value === 'pharmacist';
  const branchField = document.querySelector('#employee-branch-field');
  const crfField = document.querySelector('#employee-crf-field');
  const crfInput = document.querySelector('#employee-crf');

  branchField.hidden = isDirector;
  crfField.hidden = !isPharmacist;
  employeeBranch.required = !isDirector;
  employeeBranch.disabled = !isDirector && (branchesLoadState !== 'ready' || branches.length === 0);
  crfInput.required = isPharmacist;
}

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

async function readJsonResponse(response, fallbackMessage) {
  try {
    return await response.json();
  } catch (error) {
    throw new Error(fallbackMessage);
  }
}

async function loadEmployees() {
  const requestNumber = ++employeesLoadRequest;
  const token = getAccessToken();
  if (!token) {
    expireSession();
    return false;
  }

  employeesLoadState = 'loading';
  employeesSourceBadge.textContent = 'Carregando do banco';
  clearPageFeedback();
  renderEmployees();

  try {
    const response = await fetch(EMPLOYEES_API_URL, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const result = await readJsonResponse(response, 'O servidor retornou uma resposta inválida.');

    if (response.status === 401) {
      expireSession();
      return false;
    }
    if (!response.ok || !result.ok || !Array.isArray(result.employees)) {
      throw new Error(result.message || 'Não foi possível carregar os funcionários.');
    }
    if (requestNumber !== employeesLoadRequest) return false;

    employees.splice(0, employees.length, ...result.employees.map(mapEmployee));
    employeesLoadState = 'ready';
    employeesSourceBadge.textContent = 'Dados do banco';
    renderEmployees();
    return true;
  } catch (error) {
    if (requestNumber !== employeesLoadRequest) return false;
    employees.splice(0, employees.length);
    employeesLoadState = 'error';
    employeesSourceBadge.textContent = 'Banco indisponível';
    showPageFeedback(error.message || 'Não foi possível conectar ao servidor.', 'error');
    renderEmployees();
    return false;
  }
}

async function loadBranches() {
  employeeBranch.disabled = true;
  employeeBranch.innerHTML = '<option value="">Carregando filiais...</option>';

  try {
    const response = await fetch(BRANCHES_API_URL);
    const result = await readJsonResponse(response, 'O servidor retornou uma resposta inválida.');
    if (!response.ok || !result.ok || !Array.isArray(result.branches)) {
      throw new Error(result.message || 'Não foi possível carregar as filiais.');
    }

    branches = result.branches;
    branchesLoadState = 'ready';
    employeeBranch.innerHTML = '<option value="">Selecione uma filial</option>';
    branches.forEach((branch) => {
      const option = document.createElement('option');
      option.value = String(branch.id_filial);
      option.textContent = branch.nome_filial;
      employeeBranch.append(option);
    });
    if (branches.length === 0) {
      employeeBranch.innerHTML = '<option value="">Nenhuma filial cadastrada</option>';
    }
  } catch (error) {
    branches = [];
    branchesLoadState = 'error';
    employeeBranch.innerHTML = '<option value="">Não foi possível carregar filiais</option>';
  }

  updateEmployeeFields();
}

function closeEmployeeForm() {
  employeeFormPanel.hidden = true;
  employeeCreateCard.hidden = false;
  employeeForm.reset();
  employeeRole.value = '';
  employeePassword.required = false;
  clearFormFeedback();
  updateEmployeeFields();
}

function openNewEmployeeForm() {
  employeeForm.reset();
  employeeRole.value = '';
  employeePassword.required = true;
  document.querySelector('#employee-form-kicker').textContent = 'Novo acesso';
  document.querySelector('#employee-form-title').textContent = 'Cadastrar funcionário';
  saveEmployeeButton.textContent = 'Cadastrar funcionário';
  clearFormFeedback();
  updateEmployeeFields();
  employeeCreateCard.hidden = true;
  employeeFormPanel.hidden = false;
  employeeRole.focus();
}

async function createEmployee(values) {
  if (new TextEncoder().encode(values.password).length > 72) {
    showFormFeedback('A senha deve ter no máximo 72 bytes.');
    return;
  }

  const token = getAccessToken();
  if (!token) {
    showFormFeedback('Sua sessão expirou. Entre novamente para cadastrar funcionários.');
    return;
  }
  if (values.role !== 'director' && (branchesLoadState !== 'ready' || branches.length === 0)) {
    showFormFeedback('Não foi possível carregar uma filial. Confira a conexão e tente novamente.');
    return;
  }

  const payload = {
    role: values.role,
    first_name: values.firstName.trim(),
    last_name: values.lastName.trim(),
    cpf: values.cpf.trim(),
    email: values.email.trim(),
    password: values.password,
    internal_code: values.internalCode.trim(),
  };
  if (values.role !== 'director') payload.branch_id = values.branch;
  if (values.role === 'pharmacist') payload.crf = values.crf.trim();

  saveEmployeeButton.disabled = true;
  saveEmployeeButton.textContent = 'Cadastrando...';
  clearFormFeedback();

  try {
    const response = await fetch(EMPLOYEES_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    const result = await readJsonResponse(response, 'O servidor retornou uma resposta inválida.');

    if (response.status === 401) {
      expireSession();
      return;
    }
    if (!response.ok || !result.ok) {
      const details = result.errors ? Object.values(result.errors).join(' ') : '';
      throw new Error([result.message, details].filter(Boolean).join(' ') || 'Não foi possível cadastrar o funcionário.');
    }

    closeEmployeeForm();
    const refreshed = await loadEmployees();
    if (refreshed) {
      showPageFeedback(result.message || 'Funcionário cadastrado com sucesso.');
    } else if (employeesLoadState !== 'error') {
      showPageFeedback('Cadastro realizado. Não foi possível atualizar a lista agora.', 'error');
    }
  } catch (error) {
    showFormFeedback(error.message || 'Não foi possível conectar ao servidor. Verifique se o backend está em execução.');
  } finally {
    saveEmployeeButton.disabled = false;
    saveEmployeeButton.textContent = 'Cadastrar funcionário';
  }
}

document.querySelector('#open-employee-form').addEventListener('click', openNewEmployeeForm);
document.querySelector('#close-employee-form').addEventListener('click', closeEmployeeForm);
document.querySelector('#cancel-employee-form').addEventListener('click', closeEmployeeForm);
document.querySelector('#retry-employees').addEventListener('click', loadEmployees);
employeeRole.addEventListener('change', updateEmployeeFields);

employeeCpf.addEventListener('input', () => {
  const digits = employeeCpf.value.replace(/\D/g, '').slice(0, 11);
  employeeCpf.value = digits
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
});

employeeForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(employeeForm).entries());
  createEmployee(values);
});

renderEmployees();
updateEmployeeFields();
loadBranches();
loadEmployees();
