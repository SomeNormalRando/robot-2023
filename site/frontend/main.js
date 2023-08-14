const timeSinceLastContactDisplay = document.getElementById("time-since-last-contact-display");
// in milliseconds
let timeSinceLastContact = 0;

document.addEventListener("keydown", (e) => {
	if (e.key === "g") {
		timeSinceLastContact = 0;
		timeSinceLastContactDisplay.textContent = timeSinceLastContact;
	}
});

// setInterval(() => {
// 	timeSinceLastContact += 200;
// 	timeSinceLastContactDisplay.textContent = timeSinceLastContact;
// }, 200);
