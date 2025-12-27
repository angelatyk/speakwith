import { useMemo, useState } from "react";
import { CATEGORIES, HISTORICAL_FIGURES } from "../data/historicalFigures";
import type { HistoricalFigure } from "../types";
import CoreDisc from "./CoreDisc";

interface DiscSystemProps {
	isActive: boolean;
	onToggleSession: () => void;
	onSelectFigure: (figure: HistoricalFigure) => void;
	activeFigure: HistoricalFigure;
}

function DiscSystem({ isActive, onToggleSession, onSelectFigure, activeFigure }: DiscSystemProps) {
	const [activeCategory, setActiveCategory] = useState("All");

	const filteredFigures = useMemo(() => {
		return HISTORICAL_FIGURES.filter((f) => activeCategory === "All" || f.category === activeCategory);
	}, [activeCategory]);

	return (
		<div className="relative w-full max-w-5xl flex items-center justify-between gap-8">
			{/* Left Menu: Categories */}
			<nav className="flex flex-col items-end gap-5 z-10 w-40">
				{CATEGORIES.map((cat) => (
					<button key={cat} onClick={() => setActiveCategory(cat)} className={`category-item ${activeCategory === cat ? "active" : ""}`}>
						<span className="category-label">{cat}</span>
						<div className="category-indicator" />
					</button>
				))}
			</nav>
			{/* Core Disc */}
			<div className="flex flex-col items-center justify-center min-w-[320px]">
				<CoreDisc isActive={isActive} onToggleSession={onToggleSession} avatarUrl={activeFigure.avatarUrl} figureName={activeFigure.name} isModelSpeaking={false} isUserSpeaking={false} />
			</div>
			{/* Right Menu: Historical Figures */}
			<aside className="flex flex-col items-start gap-4 z-10 w-56 max-h-87.5 overflow-y-auto custom-scrollbar pr-2">
				{filteredFigures.map((fig) => (
					<button key={fig.id} onClick={() => onSelectFigure(fig)} className={`figure-item ${activeFigure.id === fig.id ? "active" : ""}`}>
						<div className="figure-indicator" />
						<div className="figure-card">{fig.name}</div>
					</button>
				))}
			</aside>
		</div>
	);
}

export default DiscSystem;
