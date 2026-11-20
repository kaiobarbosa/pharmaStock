const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('desktopEnv', {
  platform: process.platform,
  apiPort: process.env.FLASK_PORT || '5000',
  versions: {
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node
  }
});
