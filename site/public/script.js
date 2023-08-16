// constants
const MAX_BATTERY_VOLTS = 8.5;
const LAST_CONTACT_UPDATE_INTERVAL = 250;
// time taken for robot status to switch from "connected" to "disconnected" if no data is received (in ms)
const DISCONNECT_THRESHOLD = 7000;

const connectionDisplay = document.getElementById("connection-display");
const lastContactTimeDisplay = document.getElementById("last-contact-time-display");
const lastContactMsDisplay = document.getElementById("last-contact-ms-display");
const batteryPercentageDisplay = document.getElementById("battery-percentage-display");
const batteryVoltsDisplay = document.getElementById("battery-volts-display");

const rightMotorSpeedDisplay = document.getElementById("right-motor-speed-display")
const leftMotorSpeedDisplay = document.getElementById("left-motor-speed-display")
const mediumMotorSpeedDisplay = document.getElementById("medium-motor-speed-display")

let lastContactTimestamp = -Infinity;

const socket = io();
socket.on("ev3-message", rawData => {
	console.log(`Message received: ${rawData}`);

	const data = processData(rawData);

	lastContactTimestamp = Date.now();

	batteryVoltsDisplay.textContent = round1(data.batteryLevel);
	batteryPercentageDisplay.textContent = round1(data.batteryLevel / MAX_BATTERY_VOLTS * 100);

	leftMotorSpeedDisplay.textContent = data.leftMotorSpeed;
	rightMotorSpeedDisplay.textContent = data.rightMotorSpeed;
	mediumMotorSpeedDisplay.textContent = data.mediumMotorSpeed;
});

setInterval(() => {
	const lastContactDiff = Date.now() - lastContactTimestamp;
	const lastContactDate = new Date(lastContactTimestamp);

	lastContactTimeDisplay.textContent = `${lastContactDate.getHours()}:${lastContactDate.getMinutes()}:${lastContactDate.getSeconds()}`;

	lastContactMsDisplay.textContent = lastContactDiff;

	// if last contact is too long ago
	if ((lastContactDiff > DISCONNECT_THRESHOLD)) {
		// prevent rerunning if connectionDisplay already shows "disconnected"
		if (connectionDisplay.textContent === "disconnected") return;

		connectionDisplay.textContent = "disconnected";

		for (const infoDisplay of document.getElementsByClassName("dynamic-info-display")) {
			infoDisplay.style.color = "red";
		}
	// if lastContact is within threshold but connectionDisplay is still "disconnected" (robot reconnected)
	} else if (connectionDisplay.textContent === "disconnected") {
		connectionDisplay.textContent = "active";

		for (const infoDisplay of document.getElementsByClassName("dynamic-info-display")) {
			infoDisplay.style.color = "green";
		}
	}
}, 100);

function processData(rawData) {
	const dataJSON = JSON.parse(`[${rawData}]`);

	return {
		leftMotorSpeed: dataJSON[0],
		rightMotorSpeed: dataJSON[1],
		batteryLevel: dataJSON[2]
	}
}

/** rounds a number to 1 decimal place */
function round1(num) {
	return Math.round((num + Number.EPSILON) * 10) / 10;
}