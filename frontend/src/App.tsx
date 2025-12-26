import { useState } from "react";
import TranscriptHeader from "./components/TranscriptHeader";
import TranscriptView from "./components/TranscriptView";
import type { ChatMessage, HistoricalFigure } from "./types";

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

	const [isSessionActive, setIsSessionActive] = useState(false);
	const [selectedFigure, setSelectedFigure] = useState<HistoricalFigure | null>(null);

	return (
		<div className="app-container">
			<main className="app-main">
				<div className="app-stage">
					<TranscriptHeader isSessionActive={isSessionActive} selectedFigure={selectedFigure} />
					<TranscriptView messages={messages} />
				</div>
			</main>
		</div>
	);
}

export default App;
