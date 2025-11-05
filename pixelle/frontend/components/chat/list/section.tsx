'use client'

import { TldrawAgent } from "@/agent/TldrawAgent"
import type { ChatHistorySection } from "@/types/chat"
import { getActionHistoryGroups } from "@/utils/history"
import ChatHistoryGroup from "./group"
import ChatHistoryPrompt from "./prompt"

interface IProps {
  section: ChatHistorySection
	agent: TldrawAgent
	loading: boolean
}

const ChatHistorySection: React.FC<IProps> = ({ section, agent, loading }) => {
	const actions = section.items.filter((item) => item.type === 'action')
	const groups = getActionHistoryGroups(actions, agent)
	return (
		<div className="chat-history-section">
			<ChatHistoryPrompt item={section.prompt} editor={agent.editor} />
			{groups.map((group, i) => {
				return <ChatHistoryGroup key={'chat-history-group-' + i} group={group} agent={agent} />
			})}
			{/* {loading && <SmallSpinner />} */}
		</div>
	)
}