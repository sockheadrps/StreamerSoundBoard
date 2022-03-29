const { BrowserWindow, app, contextBridge } = require("electron")




let win = null;

const createWindow = () => {
    win = new BrowserWindow({
        width: 700,
        height: 800,
        resizable: false,
        webPreferences: {
            preload: `${__dirname}/preload.js`,
        }
    })

    win.loadFile('index.html')
};

app.whenReady().then(createWindow);
