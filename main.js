const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

let backendProcess = null;

function getPythonExecutable() {
  if (process.env.PHARMASTOCK_PYTHON) {
    return process.env.PHARMASTOCK_PYTHON;
  }

  const localPython = process.platform === 'win32'
    ? path.join(__dirname, 'venv', 'Scripts', 'python.exe')
    : path.join(__dirname, 'venv', 'bin', 'python');

  if (fs.existsSync(localPython)) {
    return localPython;
  }

  return process.platform === 'win32' ? 'python' : 'python3';
}

function startBackend() {
  if (backendProcess) return;

  const pythonExecutable = getPythonExecutable();
  backendProcess = spawn(pythonExecutable, ['-m', 'backend.app'], {
    cwd: __dirname,
    env: {
      ...process.env,
      FLASK_PORT: process.env.FLASK_PORT || '5055',
      PYTHONUNBUFFERED: '1',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Flask] ${data.toString().trimEnd()}`);
  });
  backendProcess.stderr.on('data', (data) => {
    console.error(`[Flask] ${data.toString().trimEnd()}`);
  });
  backendProcess.on('error', (error) => {
    console.error(`Não foi possível iniciar o backend Flask: ${error.message}`);
    backendProcess = null;
  });
  backendProcess.on('exit', (code, signal) => {
    if (code !== 0 && code !== null) {
      console.error(`O backend Flask encerrou com código ${code}.`);
    } else if (signal) {
      console.log(`O backend Flask foi encerrado (${signal}).`);
    }
    backendProcess = null;
  });
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
    backendProcess = null;
  }
}

function requestFirstAccess() {
  const port = Number(process.env.FLASK_PORT || 5055);

  return new Promise((resolve, reject) => {
    const request = http.get({
      hostname: '127.0.0.1',
      port,
      path: '/api/check_director_exists',
      timeout: 2000,
    }, (response) => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { body += chunk; });
      response.on('end', () => {
        if (response.statusCode !== 200) {
          const error = new Error(`A checagem de primeiro acesso retornou HTTP ${response.statusCode}.`);
          error.statusCode = response.statusCode;
          reject(error);
          return;
        }

        try {
          const result = JSON.parse(body);
          if (typeof result.requires_initial_setup !== 'boolean') {
            throw new Error('Resposta inválida da checagem de primeiro acesso.');
          }
          resolve(result.requires_initial_setup);
        } catch (error) {
          reject(error);
        }
      });
    });

    request.on('timeout', () => request.destroy(new Error('Tempo limite aguardando o Flask.')));
    request.on('error', reject);
  });
}

const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function getInitialScreen() {
  let lastError;
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      const requiresSetup = await requestFirstAccess();
      return {
        path: requiresSetup
          ? path.join(__dirname, 'frontend', 'src', 'screens', 'create_account_screeen.html')
          : path.join(__dirname, 'frontend', 'public', 'index.html'),
        startupError: false,
      };
    } catch (error) {
      lastError = error;
      if (error.statusCode) break;
      await wait(300);
    }
  }

  console.error(`Não foi possível verificar o primeiro acesso: ${lastError?.message}`);
  return {
    path: path.join(__dirname, 'frontend', 'public', 'index.html'),
    startupError: true,
  };
}

function createWindow(initialScreen) {
  const mainWindow = new BrowserWindow({
    fullscreen: true,
    center: true,
    title: 'PharmaStock | Gestão Unificada de Estoque',
    autoHideMenuBar: true, // Oculta a barra superior padrão (File, Edit, View)
    backgroundColor: '#10110f', // Mantém o tema grafite durante a abertura
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, // Isola o contexto web por segurança
      nodeIntegration: false  // Bloqueia acesso direto ao Node.js pelo HTML/JS
    }
  });

  mainWindow.loadFile(initialScreen.path, {
    query: initialScreen.startupError ? { startup_error: 'true' } : {},
  });
}

app.whenReady().then(async () => {
  startBackend();
  const initialScreen = await getInitialScreen();
  createWindow(initialScreen);

  // No macOS, recria a janela se o ícone do Dock for clicado sem janelas abertas
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      getInitialScreen().then(createWindow);
    }
  });
});

app.on('before-quit', stopBackend);

// Encerra a aplicação quando todas as janelas forem fechadas (Windows e Linux)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
