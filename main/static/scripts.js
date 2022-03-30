var socket = new WebSocket("ws://localhost:8080");
let queue = [];

socket.onopen = function(event) {
    socket.send(JSON.stringify({event: "CONNECT"}));
    socket.send(JSON.stringify({event: "CONNECT", value: socket}));

};


socket.onmessage = function(event) {
    let data = JSON.parse(event.data);
    console.log(data)
};


let btns = document.getElementsByClassName("button");
let client_id = document.getElementById("client_id").innerHTML;

for (var i=0; i < btns.length; i++){
	let btn = btns[i]
	let func = () => {
		socket.send(JSON.stringify({'client_id': client_id,
		'sound': btn.id
		}));
	}
	btns[i].addEventListener('click', func);
}

let stopBtn = document.getElementsByClassName("stopBtn");
console.log(stopBtn)
let stopFunc = () => {
		socket.send(JSON.stringify({'client_id': client_id,
		'sound': "STOP"
		}));
	}
stopBtn[0].addEventListener('click', stopFunc);

