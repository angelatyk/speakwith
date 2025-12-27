import { useState } from "react";
import DiscSystem from "./components/DiscSystem";
import TranscriptHeader from "./components/TranscriptHeader";
import TranscriptView from "./components/TranscriptView";
import { ECHOES_GUIDE } from "./data/historicalFigures";
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
	const [selectedFigure, setSelectedFigure] = useState<HistoricalFigure>(ECHOES_GUIDE);

	const handleSelectFigure = (figure: HistoricalFigure) => {
		setSelectedFigure(figure);
	};

	const handleToggleSession = () => {
		setIsSessionActive((prev) => !prev);
	};

	return (
		<div className="app-container">
			<main className="app-main">
				<div className="app-stage">
					<header className="app-header">
						<h1 className="app-title">Echoes</h1>
						<p className="app-subtitle">Learn history through conversation with those who shaped it</p>
					</header>

					{/* Disc */}
					<div className="disc-zone">
						<DiscSystem isActive={isSessionActive} onToggleSession={handleToggleSession} onSelectFigure={handleSelectFigure} activeFigure={selectedFigure} />
					</div>

					{/* Transcript */}
					<div className="transcript-zone">
						<TranscriptHeader isSessionActive={isSessionActive} selectedFigure={selectedFigure} />
						<TranscriptView messages={messages} />
					</div>
				</div>
			</main>
		</div>
	);
}

export default App;
