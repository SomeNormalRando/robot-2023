/* eslint-env browser */
/* eslint-disable no-use-before-define */
// constants
const MIN_BATTERY_VOLTS = 4.8;
const FULL_BATTERY_VOLTS = 8.5 - MIN_BATTERY_VOLTS;
const LAST_CONTACT_UPDATE_INTERVAL = 250;
// time taken for robot status to switch from "connected" to "disconnected" if no data is received (in ms)
const DISCONNECT_THRESHOLD = 4000;

const display = {
	connection: document.getElementById("connection-display"),
	lastContactTime: document.getElementById("last-contact-time-display"),
	lastContactMs: document.getElementById("last-contact-ms-display"),
	batteryPercentage: document.getElementById("battery-percentage-display"),
	batteryVolts: document.getElementById("battery-volts-display"),

	rightMotorSpeed: document.getElementById("right-motor-speed-display"),
	leftMotorSpeed: document.getElementById("left-motor-speed-display"),
	drivingDirection: document.getElementById("driving-direction-display"),
	// openerMotorStatus: document.getElementById("opener-motor-status-display"),
	pusherMotorStatus: document.getElementById("pusher-motor-status-display"),

	detectedColour: document.getElementById("detected-colour-display"),
	robotHeight: document.getElementById("robot-height-display"),

	latency: document.getElementById("latency-display"),
	currentTime: document.getElementById("current-time-display"),
};

let lastContactTimestamp = -Infinity;

const socket = io();
socket.on("ev3-message", (rawData) => {
	console.log(`Message received: ${rawData}`);

	lastContactTimestamp = Date.now();

	const data = JSON.parse(rawData);

	display.latency.textContent = Date.now() - data.timestamp;

	display.batteryVolts.textContent = round1(data.batteryLevel);
	display.batteryPercentage.textContent = round1(
		((data.batteryLevel - MIN_BATTERY_VOLTS) / FULL_BATTERY_VOLTS) * 100,
	);

	display.leftMotorSpeed.textContent = data.leftMotorSpeed;
	display.rightMotorSpeed.textContent = data.rightMotorSpeed;

	let drivingDirection;

	if ((data.leftMotorSpeed > 0) && (data.rightMotorSpeed > 0)) {
		drivingDirection = "forwards";
	} else if ((data.leftMotorSpeed < 0) && (data.rightMotorSpeed < 0)) {
		drivingDirection = "backwards";
	} else if ((data.leftMotorSpeed > 0) && (data.rightMotorSpeed < 0)) {
		drivingDirection = "right";
	} else if ((data.leftMotorSpeed < 0) && (data.rightMotorSpeed > 0)) {
		drivingDirection = "left";
	} else if ((data.leftMotorSpeed === 0) && (data.rightMotorSpeed === 0)) {
		drivingDirection = "idle";
	} else drivingDirection = "???";
	display.drivingDirection.textContent = drivingDirection;

	// display.openerMotorStatus.textContent = data.openerMotorSpeed === 0 ? "idle" : "opening";
	display.pusherMotorStatus.textContent = data.pusherMotorSpeed === 0 ? "idle" : "pushing";

	display.detectedColour.textContent = data.detectedColour;
	display.robotHeight.textContent = data.height;
});

setInterval(() => {
	const lastContactDiff = Date.now() - lastContactTimestamp;
	const lastContactDate = new Date(lastContactTimestamp);

	display.lastContactTime.textContent = formatTime(lastContactDate);
	display.lastContactMs.textContent = String(lastContactDiff).padStart(4, "0");

	// if last contact was too long ago
	if ((lastContactDiff > DISCONNECT_THRESHOLD)) {
		// prevent rerunning if connectionDisplay already shows "disconnected"
		if (display.connection.textContent === "disconnected") return;

		display.connection.textContent = "disconnected";

		for (const infoDisplay of document.getElementsByClassName("dynamic-info-display")) {
			infoDisplay.style.color = "red";
		}
	// if lastContact is within threshold but connectionDisplay is still "disconnected" (robot reconnected)
	} else if (display.connection.textContent === "disconnected") {
		display.connection.textContent = "active";

		for (const infoDisplay of document.getElementsByClassName("dynamic-info-display")) {
			infoDisplay.style.color = "green";
		}
	}
}, LAST_CONTACT_UPDATE_INTERVAL);

setInterval(() => {
	display.currentTime.textContent = formatTime(new Date(Date.now()));
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
