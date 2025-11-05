'use client'

import { TldrawAgent } from "@/agent/TldrawAgent"
import { AgentAction } from "@/shared/types/AgentAction"
import { Streaming } from "@/shared/types/Streaming"
import { getActionInfo } from "@/utils/history"

interface IProps {
  action: Streaming<AgentAction>
	agent: TldrawAgent
}

const ChatHistoryItemExpanded: React.FC<IProps> = ({ action, agent }) => {
	const { icon, description } = getActionInfo(action, agent)

	return (
		<div className={`agent-action agent-action-type-${action._type}`}>
			{icon && (
				<span>
					{/* <AgentIcon type={icon} /> */}
				</span>
			)}
			<span className="agent-action-description">
				{/* <Markdown>{description}</Markdown> */}
			</span>
		</div>
	)
}

export default ChatHistoryItemExpanded;