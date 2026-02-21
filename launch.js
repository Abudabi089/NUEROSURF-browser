const { spawn } = require('child_process');
const path = require('path');

// Clean environment
const cleanEnv = { ...process.env };
delete cleanEnv.ELECTRON_RUN_AS_NODE;
delete cleanEnv.ELECTRON_NO_ASAR;

console.log('🚀 Launching NeuroSurf Electron...');

const electronPath = path.join(process.cwd(), 'node_modules', '.bin', process.platform === 'win32' ? 'electron.cmd' : 'electron');

const child = spawn(`"${electronPath}"`, ['.'], {
    env: cleanEnv,
    stdio: 'inherit',
    shell: true
});

child.on('close', (code) => {
    console.log(`Electron process exited with code ${code}`);
    process.exit(code);
});
