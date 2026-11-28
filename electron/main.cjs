const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

// Chromium renderer and GPU sandboxing remain strictly enabled by default.
const IS_SMOKE = process.argv.includes('--smoke-test');
const TOOL_ID = 'neuro-memory-daemon';
const TOOL_NAME = 'Neuro-Memory Daemon';
const BACKEND_PORT = Number(process.env.PORT || 8094);
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const ALLOWED_ORIGINS = new Set([
  `http://127.0.0.1:${BACKEND_PORT}`,
  `http://localhost:${BACKEND_PORT}`,
]);

let mainWindow = null;
let backendProcess = null;
let startedOwnedBackend = false;
const consoleErrors = [];

function isAllowedLoopbackUrl(rawUrl) {
  try {
    const parsed = new URL(rawUrl);
    return parsed.protocol === 'http:' && ALLOWED_ORIGINS.has(parsed.origin);
  } catch {
    return false;
  }
}

function isBackendRunning() {
  return new Promise((resolve) => {
    const req = http.get(`${BACKEND_URL}/health`, (res) => {
      res.resume();
      resolve(res.statusCode >= 200 && res.statusCode < 500);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(1200, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function startBackend() {
  const rootDir = path.resolve(__dirname, '..');
  const srcDir = path.join(rootDir, 'src');
  const env = {
    ...process.env,
    PORT: String(BACKEND_PORT),
    PYTHONUNBUFFERED: '1',
    PYTHONDONTWRITEBYTECODE: '1',
    PYTHONPATH: process.env.PYTHONPATH ? `${srcDir}:${process.env.PYTHONPATH}` : srcDir,
  };

  const pythonBin = fs.existsSync('/opt/zothos-ai-env/bin/python3')
    ? '/opt/zothos-ai-env/bin/python3'
    : 'python3';

  backendProcess = spawn(
    pythonBin,
    ['-m', 'neuro_memory_daemon.cli', 'serve', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)],
    {
      cwd: rootDir,
      stdio: 'ignore',
      detached: false,
      env,
    }
  );
  startedOwnedBackend = true;
  backendProcess.on('exit', () => {
    backendProcess = null;
    startedOwnedBackend = false;
  });
}

function stopOwnedBackend() {
  if (startedOwnedBackend && backendProcess && !backendProcess.killed) {
    try {
      backendProcess.kill('SIGTERM');
    } catch {
      // ignore teardown errors
    }
    backendProcess = null;
    startedOwnedBackend = false;
  }
}

async function waitForBackend(maxAttempts = 35, interval = 200) {
  for (let i = 0; i < maxAttempts; i++) {
    if (await isBackendRunning()) return true;
    await new Promise((r) => setTimeout(r, interval));
  }
  return false;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1024,
    minHeight: 700,
    show: !IS_SMOKE,
    backgroundColor: '#0A0A0D',
    title: `${TOOL_NAME} v2.9.0 — Local Loopback Workstation (:${BACKEND_PORT})`,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
      sandbox: true,
    },
    autoHideMenuBar: true,
  });

  mainWindow.webContents.on('console-message', (_event, level, message) => {
    if (level >= 3 && !message.includes('favicon')) {
      consoleErrors.push(message);
    }
  });

  // Strict loopback navigation lock
  mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
    if (!isAllowedLoopbackUrl(navigationUrl)) {
      event.preventDefault();
    }
  });

  // Strict external window open lock
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'https:' || parsed.protocol === 'http:' || parsed.protocol === 'solana:') {
        shell.openExternal(url);
      }
    } catch {
      // deny invalid URLs
    }
    return { action: 'deny' };
  });

  if (IS_SMOKE) {
    const timer = setTimeout(() => {
      console.log(JSON.stringify({ tool: TOOL_ID, port: BACKEND_PORT, ok: false, error: 'timeout' }));
      stopOwnedBackend();
      app.exit(1);
    }, 10000);

    mainWindow.webContents.once('dom-ready', async () => {
      clearTimeout(timer);
      try {
        const metrics = await mainWindow.webContents.executeJavaScript(`({
          title: document.title || '',
          textLen: (document.body && document.body.innerText ? document.body.innerText.trim().length : 0),
          htmlLen: (document.documentElement ? document.documentElement.innerHTML.length : 0),
          buttons: document.querySelectorAll('button, a, input, select, canvas').length
        })`);
        const ok = metrics.htmlLen > 100;
        console.log(JSON.stringify({
          tool: TOOL_ID,
          name: TOOL_NAME,
          port: BACKEND_PORT,
          url: BACKEND_URL,
          ok,
          ...metrics,
          consoleErrors: consoleErrors.slice(0, 5),
        }));
        stopOwnedBackend();
        app.exit(ok ? 0 : 1);
      } catch (err) {
        console.log(JSON.stringify({ tool: TOOL_ID, port: BACKEND_PORT, ok: false, error: String(err) }));
        stopOwnedBackend();
        app.exit(1);
      }
    });
  }

  mainWindow.loadURL(BACKEND_URL);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  if (!(await isBackendRunning())) {
    startBackend();
    await waitForBackend();
  }
  createWindow();
});

app.on('before-quit', () => {
  stopOwnedBackend();
});

app.on('window-all-closed', () => {
  stopOwnedBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
