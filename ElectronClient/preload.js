const {ipcRenderer, contextBridge} = require("electron");
const fs = require('fs')


let soundFiles = fs.readdirSync('./sound_files', (err, files) => {
})


contextBridge.exposeInMainWorld("api", {
    "soundFiles": soundFiles
});