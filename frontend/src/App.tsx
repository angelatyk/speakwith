import { useState } from "react";
import { TranscriptView } from "./components/TranscriptView";
import type { ChatMessage } from "./types";

function App() {
	// Mock chat messages
	const [messages, setMessages] = useState<ChatMessage[]>(() => [
		{
			role: "model",
			text: "Greetings, traveler. Who would you like to speak with today?",
			timestamp: Date.now(),
		},
		{
			role: "user",
			name: "You",
			text: "I want to talk to Albert Einstein.",
			timestamp: Date.now(),
		},
		{
			role: "model",
			name: "Albert Einstein",
			text: "Ah, relativity! Let us explore the universe together.",
			timestamp: Date.now(),
		},
	]);

	return (
		<div className="app-container">
			<header className="app-header">Echoes: Journal</header>
			<main className="app-main">
				<div className="app-stage">
					<TranscriptView messages={messages} />
				</div>
			</main>
		</div>
	);
}

export default App;
