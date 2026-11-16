const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 700,
    center: true,
    title: 'pharmaStock - Gestão Unificada de Estoque',
    autoHideMenuBar: true, // Oculta a barra superior padrão (File, Edit, View)
    backgroundColor: '#0f172a', // Evita flash branco ao abrir a janela
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, // Isola o contexto web por segurança
      nodeIntegration: false  // Bloqueia acesso direto ao Node.js pelo HTML/JS
    }
  });

  // Carrega a tela inicial do sistema
  mainWindow.loadFile(path.join(__dirname, 'src', 'index.html'));
}

app.whenReady().then(() => {
  createWindow();

  // No macOS, recria a janela se o ícone do Dock for clicado sem janelas abertas
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Encerra a aplicação quando todas as janelas forem fechadas (Windows e Linux)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
