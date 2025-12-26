import React, { useEffect, useRef } from "react";
import type { ChatMessage } from "../types";

interface TranscriptViewProps {
	messages: ChatMessage[];
}

export const TranscriptView: React.FC<TranscriptViewProps> = ({ messages }) => {
	const scrollRef = useRef<HTMLDivElement>(null);

	useEffect(() => {
		// Scroll to bottom when messages update
		if (scrollRef.current) {
			scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
		}
	}, [messages]);

	return (
		<div ref={scrollRef} className="transcript-container">
			{messages.length === 0 ? (
				<div className="transcript-empty">Begin a conversation and watch it unfold here.</div>
			) : (
				messages.map((msg, idx) => (
					<div key={idx} className="transcript-entry">
						<span className={`transcript-speaker ${msg.role}`}>{msg.name || (msg.role === "user" ? "You" : msg.name || "Echo Guide")}</span>
						<p className={`transcript-text ${msg.role}`}>{msg.text}</p>
					</div>
				))
			)}
		</div>
	);
};
