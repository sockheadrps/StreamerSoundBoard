// Function for Login/Register error/success messages
function setFormMessage(formElement, type, message) {
    const messageElement = formElement.querySelector(".form__message");
    messageElement.textContent = message;
    messageElement.classList.remove("form__message--success", "form__message--error")
    messageElement.classList.add(`form__message--${type}`);
}

// WebSocket connection
function startWebsocketConnection(){
    var socket = new WebSocket("ws://localhost:8080");
    let queue = [];
    let client_id = document.getElementById("client-id")


    socket.onopen = function(event) {
        // Send connection request
        socket.send(JSON.stringify({"CONNECT": true}));
        var pElem = document.createElement('p')
        pElem.innerHTML = "CONNECT: True"
        pElem.classList.add('ws-msg-send')
        table.appendChild(pElem)
        
        // Send sound files present in the sound_files folder
        var pElem = document.createElement('p')
        socket.send(JSON.stringify({"SOUND_FILES": window.api.soundFiles}));
        pElem.innerHTML = "SOUNDFILES: Sent"
        pElem.classList.add('ws-msg-send')
        table.appendChild(pElem)

        // Copy client id to clipboard when clicked
        document.getElementById("client-id").addEventListener("click", e => {
            navigator.clipboard.writeText(client_id.innerHTML);
            var pElem = document.createElement('p')
            pElem.innerHTML = "Copied URL to clipboard"
            pElem.classList.add('ws-msg-send')
            table.appendChild(pElem)
        });
    };
    
    var table = document.getElementById('ws-table-container');
    let audioList = []

    socket.onmessage = function(event) {
        // On message add to the ws-table-container
        let data = JSON.parse(event.data);
        var pElem = document.createElement('p')
        var out = '';
        for (var p in data) {
            out += p + ': ' + data[p] + '\n';
        }
        pElem.innerHTML = `${out}`
        pElem.classList.add('ws-msg')

        // Edit the client id div to reflect the client URL
        if (Object.keys(data) == 'CLIENT_ID'){
            let clientID = Object.values(data)
            const soundboard_endpoint = `http://192.168.1.66:8080/soundboard/${clientID}`
            client_id.innerText = `${soundboard_endpoint}`
        }
        // If a sound command is received, play the sound
        if (Object.keys(data) == 'SOUND'){
            let audio = new Audio(`sound_files/${Object.values(data)}`)
            audio.play();
            audioList.push(audio)
        }

        // If a stop command is received, stop all sounds
        if (Object.values(data) == 'stop'){
            for ( i=0; i < audioList.length; i++){
                audioList[i].pause()
            }
            audioList = []
        }
        table.appendChild(pElem)

        // Stop the table from scrolling
        const scrollingElement = document.getElementById('ws-table-container');
        scrollingElement.scrollTo(0, scrollingElement.scrollHeight)
    };
}


document.addEventListener("DOMContentLoaded", () =>{
    const loginForm = document.querySelector('#login');
    const signup = document.getElementById('signup')
    const websocketContainer = document.getElementById('ws-container')
    const createAccountForm = document.querySelector('#createAccount')
    
    // Hide/show the create account form
    document.querySelector('#linkCreateAccount').addEventListener("click", e => {
        e.preventDefault();
        loginForm.classList.add("form--hidden");
        createAccountForm.classList.remove("form--hidden")
    });
    // Hide/show the login form
    document.querySelector('#linkLogin').addEventListener("click", e => {
        e.preventDefault();
        loginForm.classList.remove("form--hidden");
        createAccountForm.classList.add("form--hidden")
    });

    // Register a new user
    const register_endpoint = 'http://192.168.1.66:8080/sign_up'
    signup.addEventListener("submit", e =>{
        e.preventDefault();
        let email = document.getElementById('email').value;
        let password = document.getElementById('password').value
        let confirm_password = document.getElementById('confirm-password').value
        // Text fields to JSON
        if (password === confirm_password){
            let json = {
                email: email,
                password: password
            }
            // Response from server
            let xhr = new XMLHttpRequest();
            xhr.open("POST", `${register_endpoint}`)
            xhr.onload = () => {
                response_object = JSON.parse(xhr.response)
                if(response_object.status == 400)
                    setFormMessage(createAccountForm, "error", "Email already registered!");
                if(response_object.status == 201)
                    setFormMessage(createAccountForm, "success", "Successfully registered!");
            }
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify(json));
        } else {
            setFormMessage(createAccountForm, "error", "Passwords do not match!");
        }
    });

    // Log in a user
    const login_endpoint = 'http://192.168.1.66:8080/login'
    loginForm.addEventListener("submit", e =>{
        e.preventDefault();
        // Text fields to JSON
        let email = document.getElementById('login-email').value;
        let password = document.getElementById('login-password').value
        let json = {
            email: email,
            password: password
        }
        if (email.length < 4 || password.length < 4){
            setFormMessage(loginForm, "error", "Invalid Username/Password length");
        } else{
            // Response from server
            let xhr = new XMLHttpRequest();
            xhr.open("POST", `${login_endpoint}`)
            xhr.onload = () => {
                if(xhr.status == 400){
                    setFormMessage(loginForm, "error", "Bad Username/Password combo");
                }
                if(xhr.status == 200){
                    setFormMessage(loginForm, "success", "Logging in....");
                    loginForm.classList.add("form--hidden");
                    websocketContainer.classList.remove("form--hidden");
                    startWebsocketConnection();
                }

            }
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify(json));
        }        
    });
});




