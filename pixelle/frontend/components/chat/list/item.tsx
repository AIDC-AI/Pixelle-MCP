'use client'

import { TldrawAgent } from "@/agent/TldrawAgent";
import { ChatHistoryActionItem } from "@/shared/types/ChatHistoryItem";
import { getActionInfo } from "@/utils/history";
import { useState } from "react";
import ChatHistoryItemExpanded from "./itemExpanded";

interface IProps {
  item: ChatHistoryActionItem; 
  agent: TldrawAgent
}

const ChatHistoryItem: React.FC<IProps> = ({ item, agent }) => {
  const { action } = item
	const { description, summary } = getActionInfo(action, agent)
	const collapsible = summary !== null
	const [collapsed, setCollapsed] = useState(collapsible)

	if (!description) return null

	return (
		<div className="agent-actions-container">
			{action.complete && collapsible && (
				<button onClick={() => setCollapsed((v) => !v)}>
					{/* <span>{collapsed ? <ChevronRightIcon /> : <ChevronDownIcon />}</span> */}
					{summary}
				</button>
			)}

			{(!collapsed || !action.complete) && (
				<ChatHistoryItemExpanded action={action} agent={agent} />
			)}
		</div>
	)
}

export default ChatHistoryItem;