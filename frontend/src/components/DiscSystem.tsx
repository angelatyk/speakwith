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
		<div className="disc-system-shell">
			{/* Left Menu: Categories */}
			<nav className="category-nav">
				{CATEGORIES.map((cat) => (
					<button key={cat} onClick={() => setActiveCategory(cat)} className={`category-item ${activeCategory === cat ? "active" : ""}`}>
						<span className="category-label">{cat}</span>
						<div className="category-indicator" />
					</button>
				))}
			</nav>
			{/* Core Disc */}
			<div className="flex items-center justify-center min-w-[320px]">
				<CoreDisc isActive={isActive} onToggleSession={onToggleSession} avatarUrl={activeFigure.avatarUrl} figureName={activeFigure.name} />
			</div>
			{/* Right Menu: Historical Figures */}
			<aside className="figure-list custom-scrollbar">
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
