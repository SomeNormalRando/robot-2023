const statusDisplay = document.getElementById("status-display");

const socket = io();

socket.on("eventName", data => {
	console.log("Message received: ", data)
	// temporary (for testing)
	statusDisplay.textContent = data;
});
