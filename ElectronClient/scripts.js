function setFormMessage(formElement, type, message) {
    const messageElement = formElement.querySelector(".form__message");
    messageElement.textContent = message;

    messageElement.classList.remove("form__message--success", "form__message--error")
    messageElement.classList.add(`form__message--${type}`);
}


function startWebsocketConnection(){
    var socket = new WebSocket("ws://localhost:8080");
    let queue = [];
    let client_id = document.getElementById("client-id")


    socket.onopen = function(event) {
        socket.send(JSON.stringify({"CONNECT": true}));
        var pElem = document.createElement('p')
        pElem.innerHTML = "CONNECT: True"
        pElem.classList.add('ws-msg-send')
        table.appendChild(pElem)
        
        var pElem = document.createElement('p')
        socket.send(JSON.stringify({"SOUNDFILES": window.api.soundFiles}));
        pElem.innerHTML = "SOUNDFILES: Sent"
        pElem.classList.add('ws-msg-send')
        table.appendChild(pElem)

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
        let data = JSON.parse(event.data);
        // console.log(data)
        var pElem = document.createElement('p')
        pElem.innerHTML = `${Object.keys(data)} ${Object.values(data)}`
        pElem.classList.add('ws-msg')
        if (Object.keys(data) == 'client_id'){
            let clientID = Object.values(data)
            const soundboard_endpoint = `http://192.168.1.66:8080/soundboard/${clientID}`
            client_id.innerText = `${soundboard_endpoint}`
        }
        if (Object.keys(data) == 'SOUND'){
            let audio = new Audio(`sound_files/${Object.values(data)}`)
            audio.play();
            audioList.push(audio)
        }

        if (Object.keys(data) == 'STOP'){
            console.log('stppp.....')
            for ( i=0; i < audioList.length; i++){
                console.log(i)
                console.log(audioList.length)
                audioList[i].pause()
            }
            audioList = []
        }
        table.appendChild(pElem)
        const scrollingElement = document.getElementById('ws-table-container');
        scrollingElement.scrollTo(0, scrollingElement.scrollHeight)
    };
}


document.addEventListener("DOMContentLoaded", () =>{
    const loginForm = document.querySelector('#login');
    const registerForm = document.getElementsByClassName('register');
    const signup = document.getElementById('signup')
    const websocketContainer = document.getElementById('ws-container')

    const createAccountForm = document.querySelector('#createAccount')
    

    document.querySelector('#linkCreateAccount').addEventListener("click", e => {
        e.preventDefault();
        loginForm.classList.add("form--hidden");
        createAccountForm.classList.remove("form--hidden")
    });

    document.querySelector('#linkLogin').addEventListener("click", e => {
        e.preventDefault();
        loginForm.classList.remove("form--hidden");
        createAccountForm.classList.add("form--hidden")
    });

    document.querySelector('#linkLogin').addEventListener("click", e => {
        e.preventDefault();
        loginForm.classList.remove("form--hidden");
        createAccountForm.classList.add("form--hidden")
    });

    
    const register_endpoint = 'http://192.168.1.66:8080/sign_up'
    signup.addEventListener("submit", e =>{
        e.preventDefault();
        // Perform Register
        let email = document.getElementById('email').value;
        let password = document.getElementById('password').value
        let confirm_password = document.getElementById('confirm-password').value
        if (password === confirm_password){
            let json = {
                email: email,
                password: password
            }
            console.log(json)
            let xhr = new XMLHttpRequest();
            xhr.open("POST", `${register_endpoint}`)
            xhr.onload = () => {
                response_object = JSON.parse(xhr.response)
                console.log(response_object)
                if(response_object.status == 409)
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

    const login_endpoint = 'http://192.168.1.66:8080/login'
    loginForm.addEventListener("submit", e =>{
        e.preventDefault();
        // Perform login
        let email = document.getElementById('login-email').value;
        let password = document.getElementById('login-password').value
        let json = {
            email: email,
            password: password
        }
        if (email.length < 4 || password.length < 4){
            setFormMessage(loginForm, "error", "Invalid Username/Password length");
        } else{
            console.log(json)
            let xhr = new XMLHttpRequest();
            xhr.open("POST", `${login_endpoint}`)
            xhr.onload = () => {
                response_object = JSON.parse(xhr.response)
                console.log(response_object)
                if(response_object.status == 409){
                    setFormMessage(loginForm, "error", "Bad Username/Password combo");
                }
                if(response_object.status == 200){
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




