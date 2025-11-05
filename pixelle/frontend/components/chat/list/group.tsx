'use client'

import type { ChatHistoryGroup } from "@/types/chat"
import ChatHistoryGroupWithDiff from "./groupWithDiff"
import { TldrawAgent } from "@/agent/TldrawAgent"
import ChatHistoryGroupWithoutDiff from "./groupWithoutDiff"

interface IProps {
  group: ChatHistoryGroup
	agent: TldrawAgent
}

const ChatHistoryGroup: React.FC<IProps> = ({ group, agent }) => {
	if (group.withDiff) {
		return <ChatHistoryGroupWithDiff group={group} agent={agent} />
	}

	return <ChatHistoryGroupWithoutDiff group={group} agent={agent} />
}

export default ChatHistoryGroup