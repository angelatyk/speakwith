import type { HistoricalFigure } from "../types";

function TranscriptHeader({ isSessionActive, selectedFigure }: { isSessionActive: boolean; selectedFigure: HistoricalFigure | null }) {
	const statusText = isSessionActive ? `Connected to ${selectedFigure?.name || "Echo Guide"}` : "Offline";

	return (
		<div className="transcript-header">
			<h3 className="transcript-title">Echoes: Journal</h3>
			<div className="transcript-status">
				<div className={`status-dot ${isSessionActive ? "active" : ""}`} />
				<span className="status-text">{statusText}</span>
			</div>
		</div>
	);
}

export default TranscriptHeader;
