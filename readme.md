# Streamer Sound Board
## _A free Soundboard Tool for Streaming_

An Async tool built with FastAPI, MongoDB and ElectronJS.

## Features

- Ability to create Users, handle multiple users at once
- Hashed Passwords
- Soundboard can be controlled by multiple clients from multiple devices
- Auto detect mp3 soundfiles by dropping them in the ElectronClient/sound_files directory
- A handy websocket console for development, and seeing when Websocket events happen!


## Tech

SSB uses a number of open source projects to work properly:

- [FastAPI](https://fastapi.tiangolo.com/) - The new Python backend hotness
- [ElectronJS](https://www.electronjs.org/) - Application framework for creating local web app-like applications, easy to package and run!
- [MongoDB](https://www.mongodb.com/) - Fast, NOSQL document databa
- Vanilla Javascript - No need for complex bloated JS frameworks
- HTML - You cant have a chromium app without it!
- CSS - No need for preprocessors when you write it oldschool

## Usage
- Run the server and connect to it via LAN with a phone or tablet, actuate sounds from the browser on your device and the sound is played on your PC via the Electron App



## Installation

SSB requires [Python 3.7+](https://www.python.org/), [Node.js](https://nodejs.org/en/download/) and a MongoDB database (local or hosted)

Install the dependencies and start the server. Ensure you have MongoDB Compass running, or change the DB connection variable in server.py to match your host

```sh
cd SSB
pip install -r requirements.txt
python server.py
```
Run the Electron app via shell:
```sh
cd ElectronClient
npm start
```
Or build an executable by following these [instructions](https://www.electronjs.org/docs/latest/development/build-instructions-gn)


## Development

Want to contribute? Great!


## License

MIT

**Free Software, Hell Yeah!**

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)




