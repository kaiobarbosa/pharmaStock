const { app, BrowserWindow } = require('electron');
const path = require('path');

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
