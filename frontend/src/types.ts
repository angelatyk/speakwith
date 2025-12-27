export interface HistoricalFigure {
	id: string;
	name: string;
	category: string;
	description: string;
	avatarUrl: string;
	voiceName: "Puck" | "Charon" | "Kore" | "Fenrir" | "Zephyr";
	systemInstruction: string;
}

export interface ChatMessage {
	role: "user" | "model";
	name?: string;
	text: string;
	timestamp: number;
}

export type InteractionMode = "TEXT" | "VOICE";
