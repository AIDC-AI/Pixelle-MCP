'use client'

import { TldrawAgent } from "@/agent/TldrawAgent"
import { ChatHistoryGroup } from "@/types/chat"
import { getActionInfo } from "@/utils/history"
import { useMemo, useState } from "react"
import ChatHistoryItem from "./item"
import ChatHistoryItemExpanded from "./itemExpanded"

interface IProps {
  group: ChatHistoryGroup
	agent: TldrawAgent
}

const ChatHistoryGroupWithoutDiff: React.FC<IProps> = ({ group, agent }) => {
	const { items } = group

	const nonEmptyItems = useMemo(() => {
		return items.filter((item) => {
			const { description } = getActionInfo(item.action, agent)
			return description !== null
		})
	}, [items, agent])

	const [collapsed, setCollapsed] = useState(true)

	const complete = useMemo(() => {
		return items.every((item) => item.action.complete)
	}, [items])

	const summary = useMemo(() => {
		const time = Math.floor(items.reduce((acc, item) => acc + item.action.time, 0) / 1000)
		if (time === 0) return 'Thought for less than a second'
		if (time === 1) return 'Thought for 1 second'
		return `Thought for ${time} seconds`
	}, [items])

	if (nonEmptyItems.length === 0) {
		return null
	}

	if (nonEmptyItems.length < 2) {
		return (
			<div className="chat-history-group">
				{nonEmptyItems.map((item, i) => {
					return <ChatHistoryItem item={item} agent={agent} key={'action-' + i} />
				})}
			</div>
		)
	}

	const showContent = !collapsed || !complete

	return (
		<div className="chat-history-group">
			{complete && (
				<button onClick={() => setCollapsed((v) => !v)}>
					{/* <span>{showContent ? <ChevronDownIcon /> : <ChevronRightIcon />}</span> */}
					{summary}
				</button>
			)}
			{showContent && (
				<div className="agent-actions-container">
					{nonEmptyItems.map((item, i) => {
						return (
							<ChatHistoryItemExpanded action={item.action} agent={agent} key={'action-' + i} />
						)
					})}
				</div>
			)}
		</div>
	)
}

export default ChatHistoryGroupWithoutDiff;