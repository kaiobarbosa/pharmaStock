const employees = [
  { id: 'FUN-001', firstName: 'Marina', lastName: 'Costa', role: 'director', internalCode: 'DIR-001', email: 'marina.costa@pharmastock.demo', password: 'SenhaDemo!2026', branch: '', crf: '', active: true },
  { id: 'FUN-002', firstName: 'Roberto', lastName: 'Alves', role: 'manager', internalCode: 'GER-014', email: 'roberto.alves@pharmastock.demo', password: 'SenhaDemo!2026', branch: 'Filial Centro', crf: '', active: true },
  { id: 'FUN-003', firstName: 'Ana Luiza', lastName: 'Ribeiro', role: 'pharmacist', internalCode: 'FAR-028', email: 'ana.ribeiro@pharmastock.demo', password: 'SenhaDemo!2026', branch: 'Filial Centro', crf: 'CRF-SP 123456', active: true },
  { id: 'FUN-004', firstName: 'Lucas', lastName: 'Mendes', role: 'attendant', internalCode: 'ATE-037', email: 'lucas.mendes@pharmastock.demo', password: 'SenhaDemo!2026', branch: 'Filial Jardins', crf: '', active: true },
];

const roleLabels = {
  director: 'Diretor',
  manager: 'Gerente',
  pharmacist: 'Farmacêutico',
  attendant: 'Atendente',
};

const employeeList = document.querySelector('#employee-list');
const employeeCount = document.querySelector('#employee-count');
const employeeEmpty = document.querySelector('#employee-empty');
const employeeFormPanel = document.querySelector('#employee-form-panel');
const employeeCreateCard = document.querySelector('#employee-create-card');
const employeeForm = document.querySelector('#employee-form');
const employeeRole = document.querySelector('#employee-role');
const employeePassword = document.querySelector('#employee-password');
const employeePageFeedback = document.querySelector('#employee-page-feedback');
const employeeDialog = document.querySelector('#employee-confirm-dialog');

let activeEmployeeId = null;
let editingEmployeeId = null;
let pendingInactiveEmployeeId = null;
let nextEmployeeNumber = employees.length + 1;

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function initials(employee) {
  return `${employee.firstName.charAt(0)}${employee.lastName.charAt(0)}`.toLocaleUpperCase('pt-BR');
}

function renderEmployees() {
  const activeCount = employees.filter((employee) => employee.active).length;
  employeeCount.textContent = `${activeCount} ativos · ${employees.length} no total`;
  employeeEmpty.hidden = employees.length > 0;

  employeeList.innerHTML = employees.map((employee) => {
    const expanded = activeEmployeeId === employee.id;
    const status = employee.active ? 'Ativo' : 'Inativo';
    const branch = employee.branch || 'Toda a rede';
    return `
      <article class="employee-card${employee.active ? '' : ' is-inactive'}">
        <button class="employee-card__summary" type="button" data-employee-toggle="${escapeHtml(employee.id)}" aria-expanded="${expanded}">
          <span class="employee-avatar" aria-hidden="true">${escapeHtml(initials(employee))}</span>
          <span class="employee-card__identity">
            <strong>${escapeHtml(employee.firstName)} ${escapeHtml(employee.lastName)}</strong>
            <span>${escapeHtml(roleLabels[employee.role])} <span aria-hidden="true">·</span> ${escapeHtml(branch)}</span>
          </span>
          <span class="employee-card__email">${escapeHtml(employee.email)}</span>
          <span class="status-badge ${employee.active ? 'is-active' : 'is-inactive'}">${status}</span>
          <span class="employee-card__chevron" aria-hidden="true">${expanded ? '−' : '+'}</span>
        </button>
        ${expanded ? `
          <div class="employee-card__actions">
            <span class="employee-card__code">Código ${escapeHtml(employee.internalCode)}</span>
            <div>
              <button class="text-button" type="button" data-employee-edit="${escapeHtml(employee.id)}">Editar</button>
              ${employee.active
                ? `<button class="text-button text-button--danger" type="button" data-employee-inactivate="${escapeHtml(employee.id)}">Inativar</button>`
                : `<button class="text-button" type="button" data-employee-reactivate="${escapeHtml(employee.id)}">Reativar</button>`}
            </div>
          </div>` : ''}
      </article>`;
  }).join('');
}

function updateEmployeeFields() {
  const isDirector = employeeRole.value === 'director';
  const isPharmacist = employeeRole.value === 'pharmacist';
  const branchField = document.querySelector('#employee-branch-field');
  const crfField = document.querySelector('#employee-crf-field');
  const branchSelect = document.querySelector('#employee-branch');
  const crfInput = document.querySelector('#employee-crf');

  branchField.hidden = isDirector;
  crfField.hidden = !isPharmacist;
  branchSelect.required = !isDirector;
  crfInput.required = isPharmacist;
}

function closeEmployeeForm() {
  employeeFormPanel.hidden = true;
  employeeCreateCard.hidden = false;
  employeeForm.reset();
  editingEmployeeId = null;
  employeePassword.required = false;
  employeePassword.placeholder = '';
  document.querySelector('#inactivate-employee-from-form').hidden = true;
  updateEmployeeFields();
}

function openNewEmployeeForm() {
  editingEmployeeId = null;
  employeeForm.reset();
  employeeRole.value = 'director';
  employeePassword.required = true;
  employeePassword.placeholder = '';
  document.querySelector('#employee-form-kicker').textContent = 'Novo acesso';
  document.querySelector('#employee-form-title').textContent = 'Cadastrar funcionário';
  document.querySelector('#save-employee').textContent = 'Cadastrar funcionário';
  document.querySelector('#inactivate-employee-from-form').hidden = true;
  updateEmployeeFields();
  employeeCreateCard.hidden = true;
  employeeFormPanel.hidden = false;
  document.querySelector('#employee-first-name').focus();
}

function openEditEmployeeForm(employee) {
  editingEmployeeId = employee.id;
  employeeForm.reset();
  employeeRole.value = employee.role;
  employeeForm.elements.firstName.value = employee.firstName;
  employeeForm.elements.lastName.value = employee.lastName;
  employeeForm.elements.internalCode.value = employee.internalCode;
  employeeForm.elements.branch.value = employee.branch || 'Filial Centro';
  employeeForm.elements.crf.value = employee.crf;
  employeeForm.elements.email.value = employee.email;
  employeePassword.value = employee.password;
  employeePassword.required = true;
  employeePassword.placeholder = '';
  document.querySelector('#employee-form-kicker').textContent = 'Editar acesso';
  document.querySelector('#employee-form-title').textContent = `Editar ${employee.firstName} ${employee.lastName}`;
  document.querySelector('#save-employee').textContent = 'Salvar alterações';
  document.querySelector('#inactivate-employee-from-form').hidden = !employee.active;
  updateEmployeeFields();
  employeeCreateCard.hidden = true;
  employeeFormPanel.hidden = false;
  document.querySelector('#employee-first-name').focus();
  employeeFormPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.querySelector('#open-employee-form').addEventListener('click', openNewEmployeeForm);
document.querySelector('#close-employee-form').addEventListener('click', closeEmployeeForm);
document.querySelector('#cancel-employee-form').addEventListener('click', closeEmployeeForm);
document.querySelector('#inactivate-employee-from-form').addEventListener('click', () => {
  if (!editingEmployeeId) return;
  const employee = employees.find((item) => item.id === editingEmployeeId);
  if (!employee) return;
  pendingInactiveEmployeeId = employee.id;
  document.querySelector('#employee-confirm-message').textContent = `Deseja inativar o acesso de ${employee.firstName} ${employee.lastName}?`;
  employeeDialog.showModal();
});
employeeRole.addEventListener('change', updateEmployeeFields);

employeeList.addEventListener('click', (event) => {
  const toggle = event.target.closest('[data-employee-toggle]');
  if (toggle) {
    activeEmployeeId = activeEmployeeId === toggle.dataset.employeeToggle ? null : toggle.dataset.employeeToggle;
    renderEmployees();
    return;
  }

  const editButton = event.target.closest('[data-employee-edit]');
  if (editButton) {
    const employee = employees.find((item) => item.id === editButton.dataset.employeeEdit);
    if (employee) openEditEmployeeForm(employee);
    return;
  }

  const inactivateButton = event.target.closest('[data-employee-inactivate]');
  if (inactivateButton) {
    pendingInactiveEmployeeId = inactivateButton.dataset.employeeInactivate;
    const employee = employees.find((item) => item.id === pendingInactiveEmployeeId);
    document.querySelector('#employee-confirm-message').textContent = `Deseja inativar o acesso de ${employee.firstName} ${employee.lastName}?`;
    employeeDialog.showModal();
    return;
  }

  const reactivateButton = event.target.closest('[data-employee-reactivate]');
  if (reactivateButton) {
    const employee = employees.find((item) => item.id === reactivateButton.dataset.employeeReactivate);
    if (employee) {
      employee.active = true;
      activeEmployeeId = employee.id;
      renderEmployees();
    }
  }
});

employeeForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(employeeForm).entries());
  const employeeData = {
    firstName: values.firstName.trim(),
    lastName: values.lastName.trim(),
    role: values.role,
    internalCode: values.internalCode.trim(),
    email: values.email.trim(),
    password: values.password,
    branch: values.role === 'director' ? '' : values.branch,
    crf: values.role === 'pharmacist' ? values.crf.trim() : '',
    active: true,
  };

  if (editingEmployeeId) {
    const employee = employees.find((item) => item.id === editingEmployeeId);
    employeeData.active = employee.active;
    Object.assign(employee, employeeData);
    employeePageFeedback.textContent = 'As informações do funcionário foram atualizadas neste protótipo.';
    activeEmployeeId = employee.id;
  } else {
    employeeData.id = `FUN-${String(nextEmployeeNumber).padStart(3, '0')}`;
    nextEmployeeNumber += 1;
    employees.unshift(employeeData);
    employeePageFeedback.textContent = 'O funcionário foi adicionado à lista demonstrativa.';
    activeEmployeeId = employeeData.id;
  }

  employeePageFeedback.hidden = false;
  closeEmployeeForm();
  renderEmployees();
});

document.querySelector('#employee-confirm-cancel').addEventListener('click', () => employeeDialog.close());
document.querySelector('#employee-confirm-accept').addEventListener('click', () => {
  const employee = employees.find((item) => item.id === pendingInactiveEmployeeId);
  if (employee) {
    employee.active = false;
    activeEmployeeId = employee.id;
    employeePageFeedback.textContent = `${employee.firstName} ${employee.lastName} foi marcado como inativo neste protótipo.`;
    employeePageFeedback.hidden = false;
  }
  pendingInactiveEmployeeId = null;
  employeeDialog.close();
  closeEmployeeForm();
  renderEmployees();
});

renderEmployees();
updateEmployeeFields();
