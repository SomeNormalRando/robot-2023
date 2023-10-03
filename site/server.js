import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { createServer } from "http";
import express from "express";
import { Server } from "socket.io";
import * as mqtt from "mqtt";

// constants
// eslint-disable-next-line no-underscore-dangle
const __dirname = dirname(fileURLToPath(import.meta.url));
const SERVER_PORT = 8000;
const SOCKET_EVENT_NAME = "ev3-message";
const MQTT_OPTIONS = {
	host: "f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud",
	port: 8883,
	protocol: "mqtts",
	username: "ev3maker",
	password: "Test123-",
};
const MQTT_TOPIC = "ev3/test";

// functions
function log(msg) {
	const time = new Date(Date.now());
	const hours = String(time.getHours()).padStart(2, "0");
	const minutes = String(time.getMinutes()).padStart(2, "0");
	const seconds = String(time.getSeconds()).padStart(2, "0");

	// eslint-disable-next-line no-console
	console.log(`[${hours}:${minutes}:${seconds}] ${msg}`);
}

// #region server
const app = express();
const server = createServer(app);

app.get("/", (_req, res) => {
	res.sendFile(join(__dirname, "/public/index.html"));
});
app.use(express.static(join(__dirname, "/public")));

server.listen(SERVER_PORT, () => {
	log(`[server] Server listening on localhost:${SERVER_PORT}`);
});

const io = new Server(server);
io.on("connection", (socket) => {
	log(`[server] Socket connection received from ${socket.handshake.address}.`);
});
// #endregion

// #region MQTT
log("[MQTT] Connecting to broker...");

const client = mqtt.connect(MQTT_OPTIONS);

client.on("connect", () => {
	log("[MQTT] Connected to broker.");

	client.subscribe(MQTT_TOPIC, (err, granted) => {
		if (err) throw new Error(err);
		log(`[MQTT] Subscribed to topic "${granted[0].topic}" with QoS level ${granted[0].qos}.`);
	});
});

client.on("message", (_topic, message) => {
	// message is Buffer
	const msgStr = message.toString();
	log(`[MQTT] Message received from broker: "${msgStr}".`);

	// Send data to all connected clients
	io.emit(SOCKET_EVENT_NAME, msgStr);
});

client.on("close", () => log("[MQTT] Disconnected from broker."));

// eslint-disable-next-line no-console
client.on("error", (e) => console.error(e));
// #endregion
