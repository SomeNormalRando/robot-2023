import { dirname } from "path";
import { fileURLToPath } from "url";
import { createServer } from "http";
import express from "express";
import { Server } from "socket.io";
import * as mqtt from "mqtt";

// constants
const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = 6969;
const SOCKET_EVENT_NAME = "eventName";

// #region server
const app = express();
const server = createServer(app);
const io = new Server(server);

app.get("/", (req, res) => {
	res.sendFile(__dirname + "/public/index.html")
});
app.use(express.static("public"));

io.on("connection", (socket) => {
	console.log(`Socket connection received from ${socket.handshake.address}.`)
});

server.listen(PORT, () => {
	console.log(`Server listening on localhost:${PORT}`);
});
// #endregion

// #region mqtt 
const OPTIONS = {
	host: "f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud",
	port: 8883,
	protocol: "mqtts",
	username: "ev3maker",
	password: "Test123-"
};

const TOPIC = "ev3/test";

console.log("Connecting to broker...")
mqtt.connectAsync("mqtts://f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud:8883", OPTIONS).then((client) => {
	client.on("connect", () => {
		console.log("Connected to broker.")

		client.subscribeAsync(TOPIC)
			.then(() =>  console.log(`Subscribed to ${TOPIC}.`))
			.catch(err => console.error(err));
	});

	client.on("message", (topic, message) => {
		// message is Buffer
		const msgStr = message.toString();
		console.log(`Message received: \`${msgStr}\`.`);

		// const dataJSON = JSON.parse(msgStr);

		// Send data to all connected clients
		io.emit(SOCKET_EVENT_NAME, msgStr);
	});

}).catch(err => console.error(err));
// #endregion

