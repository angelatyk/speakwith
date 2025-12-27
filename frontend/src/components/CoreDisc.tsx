import { Power, X } from "lucide-react";

type CoreDiscProps = {
	isActive: boolean;
	onToggleSession: () => void;
	avatarUrl?: string;
	figureName?: string;
	isModelSpeaking?: boolean;
	isUserSpeaking?: boolean;
};

function CoreDisc({ isActive, onToggleSession, avatarUrl, figureName, isModelSpeaking, isUserSpeaking }: CoreDiscProps) {
	const getStatusText = () => {
		if (!isActive) return "Tap the disc to begin";
		if (isModelSpeaking) return figureName || "Echo Guide";
		if (isUserSpeaking) return "Listening...";
		return "Standing by";
	};

	return (
		<div className="flex flex-col items-center">
			<div className="core-disc-wrapper">
				{/* Rotating Signal Ring */}
				<svg className={`signal-ring ${isActive ? "active" : ""}`} viewBox="0 0 100 100">
					<defs>
						<linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="0%">
							<stop offset="0%" stopColor="#fff" stopOpacity="1" />
							<stop offset="20%" stopColor="var(--color-amber-500)" stopOpacity="1" />
							<stop offset="100%" stopColor="var(--color-amber-500)" stopOpacity="0" />
						</linearGradient>
					</defs>
					<circle cx="50" cy="50" r="48.5" fill="none" stroke="url(#ringGradient)" strokeWidth="1.5" strokeLinecap="round" className="animate-revolve-slow" />
				</svg>

				<div className={`disc-glow ${isActive ? "active" : ""}`} />

				<div className={`disc-metallic ${isActive ? "active" : ""}`}>
					<div className={`disc-surface ${isActive ? "active" : ""}`} />

					<div className="disc-center">{avatarUrl && <img src={avatarUrl} alt={figureName} className={`disc-avatar ${isActive ? "active" : "grayscale opacity-30"}`} />}</div>

					<button className={`disc-power-btn ${isActive ? "active" : ""}`} onClick={onToggleSession} aria-label="Toggle session">
						{isActive ? <X size={24} className="text-white" /> : <Power size={22} className="text-zinc-600" />}
					</button>
				</div>
			</div>

			<div className="mt-8 h-8 flex items-center justify-center">
				<span className={`disc-status ${isActive ? "active" : "inactive"}`}>{getStatusText()}</span>
			</div>
		</div>
	);
}

export default CoreDisc;
