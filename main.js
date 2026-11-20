const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
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
      FLASK_PORT: process.env.FLASK_PORT || '5000',
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

function createWindow() {
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

  // Carrega a tela inicial do sistema
  mainWindow.loadFile(
    path.join(__dirname, 'frontend', 'src', 'screens', 'create_account_screeen.html')
  );
}

app.whenReady().then(() => {
  startBackend();
  createWindow();

  // No macOS, recria a janela se o ícone do Dock for clicado sem janelas abertas
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
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
