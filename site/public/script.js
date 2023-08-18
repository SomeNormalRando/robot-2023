/* eslint-env browser */
/* eslint-disable no-use-before-define */
// constants
const MIN_BATTERY_VOLTS = 4.8;
const FULL_BATTERY_VOLTS = 8.5 - MIN_BATTERY_VOLTS;
const LAST_CONTACT_UPDATE_INTERVAL = 250;
// time taken for robot status to switch from "connected" to "disconnected" if no data is received (in ms)
const DISCONNECT_THRESHOLD = 4000;

const connectionDisplay = document.getElementById("connection-display");
const lastContactTimeDisplay = document.getElementById("last-contact-time-display");
const lastContactMsDisplay = document.getElementById("last-contact-ms-display");
const batteryPercentageDisplay = document.getElementById("battery-percentage-display");
const batteryVoltsDisplay = document.getElementById("battery-volts-display");

const rightMotorSpeedDisplay = document.getElementById("right-motor-speed-display");
const leftMotorSpeedDisplay = document.getElementById("left-motor-speed-display");
const drivingDirectionDisplay = document.getElementById("driving-direction-display");
const openerMotorStatusDisplay = document.getElementById("opener-motor-status-display");
const pusherMotorStatusDisplay = document.getElementById("pusher-motor-status-display");

const latencyDisplay = document.getElementById("latency-display");
const currentTimeDisplay = document.getElementById("current-time-display");

let lastContactTimestamp = -Infinity;

const socket = io();
socket.on("ev3-message", (rawData) => {
	console.log(`Message received: ${rawData}`);

	const data = JSON.parse(rawData);

	lastContactTimestamp = Date.now();

	batteryVoltsDisplay.textContent = round1(data.batteryLevel);
	batteryPercentageDisplay.textContent = round1(
		((data.batteryLevel - MIN_BATTERY_VOLTS) / FULL_BATTERY_VOLTS) * 100
	);

	leftMotorSpeedDisplay.textContent = data.leftMotorSpeed;
	rightMotorSpeedDisplay.textContent = data.rightMotorSpeed;

	let drivingDirection;

	if (data.leftMotorSpeed > 0 && data.rightMotorSpeed > 0) drivingDirection = "forwards";
	else if (data.leftMotorSpeed < 0 && data.rightMotorSpeed < 0) drivingDirection = "backwards";
	if (data.leftMotorSpeed > 0 && data.rightMotorSpeed < 0) drivingDirection = "right";
	else if (data.leftMotorSpeed < 0 && data.rightMotorSpeed > 0) drivingDirection = "left";
	else if (data.leftMotorSpeed === 0 && data.rightMotorSpeed === 0) drivingDirection = "idle";
	else drivingDirection = "???";
	drivingDirectionDisplay.textContent = drivingDirection;

	openerMotorStatusDisplay.textContent = data.openerMotorSpeed === 0 ? "idle" : "opening";
	pusherMotorStatusDisplay.textContent = data.pusherMotorSpeed === 0 ? "idle" : "pushing";
});

setInterval(() => {
	const lastContactDiff = Date.now() - lastContactTimestamp;
	const lastContactDate = new Date(lastContactTimestamp);

	lastContactTimeDisplay.textContent = formatTime(lastContactDate);
	lastContactMsDisplay.textContent = String(lastContactDiff).padStart(4, "0");

	// if last contact was too long ago
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
}, LAST_CONTACT_UPDATE_INTERVAL);

setInterval(() => {
	currentTimeDisplay.textContent = formatTime(new Date(Date.now()));
}, 1000);

/** rounds a number to 1 decimal place */
function round1(num) {
	return Math.round((num + Number.EPSILON) * 10) / 10;
}
function formatTime(date) {
	const hours = String(date.getHours()).padStart(2, "0");
	const minutes = String(date.getMinutes()).padStart(2, "0");
	const seconds = String(date.getSeconds()).padStart(2, "0");

	return `${hours}:${minutes}:${seconds}`;
}
