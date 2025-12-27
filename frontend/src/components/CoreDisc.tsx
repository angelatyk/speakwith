import { Power, X } from "lucide-react";

type CoreDiscProps = {
	isActive: boolean;
	onToggleSession: () => void;
	avatarUrl?: string;
	figureName?: string;
};

export default function CoreDisc({ isActive, onToggleSession, avatarUrl, figureName }: CoreDiscProps) {
	return (
		<div className="core-disc-wrapper">
			{/* 🔶 High-Intensity Rotating Signal Ring */}
			<svg className={`signal-ring transition-opacity duration-1000 ${isActive ? "opacity-100" : "opacity-0"}`} viewBox="0 0 100 100">
				<defs>
					<linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="0%">
						{/* Adding a white stop at the start makes the "head" of the line glow much brighter */}
						<stop offset="0%" stopColor="#fff" stopOpacity="1" />
						<stop offset="20%" stopColor="var(--color-amber-500)" stopOpacity="1" />
						<stop offset="100%" stopColor="var(--color-amber-500)" stopOpacity="0" />
					</linearGradient>
				</defs>
				<circle cx="50" cy="50" r="48.5" fill="none" stroke="url(#ringGradient)" strokeWidth="1.5" strokeLinecap="round" className="animate-revolve-slow" />
			</svg>

			{/* 🔶 Soft glow behind disc */}
			<div className={`disc-glow ${isActive ? "active" : ""}`} />

			{/* 🔘 Main Metallic Disc */}
			<div className={`disc-metallic ${isActive ? "active" : ""}`}>
				{/* 1. Brushed Metal Texture Layer */}
				<div className={`disc-surface ${isActive ? "active" : ""}`} />

				{/* 2. Content Center Layer */}
				<div className="disc-center">
					{avatarUrl ? (
						<img src={avatarUrl} alt={figureName} className={`disc-avatar ${isActive ? "active" : "grayscale opacity-30"}`} />
					) : (
						<div className="disc-placeholder">
							<div className="disc-placeholder-text">{isActive ? "Communion" : "Echo Guide"}</div>
						</div>
					)}
				</div>

				{/* 3. Central Power Button Overlay */}
				<button className={`disc-power-btn ${isActive ? "active" : ""}`} onClick={onToggleSession} aria-label="Toggle session">
					{isActive ? <X size={24} className="text-white" /> : <Power size={22} className="text-zinc-600" />}
				</button>
			</div>
		</div>
	);
}
