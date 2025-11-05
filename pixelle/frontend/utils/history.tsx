import { TldrawAgent } from "@/agent/TldrawAgent"
import { AgentAction } from "@/shared/types/AgentAction"
import { ChatHistoryActionItem, ChatHistoryItem } from "@/shared/types/ChatHistoryItem"
import { Streaming } from "@/shared/types/Streaming"
import { ChatHistoryGroup, ChatHistorySection } from "@/types/chat"
import { isRecordsDiffEmpty, RecordsDiff, TLRecord, TLShape, TLShapeId } from "tldraw"

/**
 * Get the full info for an action to display in chat history UI.
 * This function adds default values for any unset properties.
 * If the action's util returns null, the action will not be shown in chat history.
 */
export const getActionInfo = (action: Streaming<AgentAction>, agent: TldrawAgent) => {
	const util = agent.getAgentActionUtil(action._type)
	const info = util.getInfo(action) ?? { description: null }
	const {
		icon = null,
		description = JSON.stringify(action, null, 2),
		summary = null,
		canGroup = () => true,
	} = info

	return {
		icon,
		description,
		summary,
		canGroup,
	}
}

export const getAgentHistorySections = (items: ChatHistoryItem[]) => {
  const sections: ChatHistorySection[] = []

	for (const item of items) {
		if (item.type === 'prompt') {
			sections.push({ prompt: item, items: [] })
			continue
		}

		sections[sections.length - 1].items.push(item)
	}

	return sections
}

export const getActionHistoryGroups = (items: ChatHistoryActionItem[], agent: TldrawAgent) => {
	const groups: ChatHistoryGroup[] = []

	for (const item of items) {
		const { description } = getActionInfo(item.action, agent)
		if (description === null) {
			continue
		}

		const group = groups[groups.length - 1]
		if (group && canActionBeGrouped({ item, group, agent })) {
			group.items.push(item)
		} else {
			groups.push({
				items: [item],
				withDiff: !isRecordsDiffEmpty(item.diff) && item.action.complete,
			})
		}
	}

	return groups
}

/**
 * Check if an action can be merged with a group.
 */
export const canActionBeGrouped = ({
	item,
	group,
	agent,
}: {
	item: ChatHistoryActionItem
	group: ChatHistoryGroup
	agent: TldrawAgent
}) => {
	if (!item.action.complete) return false
	if (!group) return false

	const showDiff = !isRecordsDiffEmpty(item.diff)
	if (showDiff !== group.withDiff) return false

	const groupAcceptance = group.items[0]?.acceptance
	if (groupAcceptance !== item.acceptance) return false

	const prevAction = group.items.at(-1)?.action
	if (!prevAction) return false

	const actionInfo = getActionInfo(item.action, agent)
	const prevActionInfo = getActionInfo(prevAction, agent)

	if (actionInfo.canGroup(prevAction) && prevActionInfo.canGroup(item.action)) {
		return true
	}

	return false
}

export const getDiffShapesFromDiff = (diff: RecordsDiff<TLRecord>) => {
	const diffShapes: TLShape[] = []

	const numberOfShapes =
		Object.keys(diff.added).length +
		Object.keys(diff.updated).length +
		Object.keys(diff.removed).length

	// If there are many shapes in the diff, don't show shadows (for performance reasons)
	const showShadows = numberOfShapes < 20

	for (const key in diff.removed) {
		const id = key as TLShapeId
		const prevShape = diff.removed[id]
		if (prevShape.typeName !== 'shape') continue
		const shape = {
			...prevShape,
			opacity: showShadows ? prevShape.opacity : prevShape.opacity / 2,
			props: { ...prevShape.props },
			meta: { ...prevShape.meta, changeType: showShadows ? 'delete-shadow' : 'delete' },
		}

		if ('dash' in shape.props) {
			shape.props.dash = 'solid'
		}

		diffShapes.push(shape)
	}

	for (const key in diff.updated) {
		const id = key as TLShapeId

		const prevBefore = diff.updated[id][0]
		const prevAfter = diff.updated[id][1]
		if (prevBefore.typeName !== 'shape' || prevAfter.typeName !== 'shape') continue

		const before = {
			...prevBefore,
			id: (id + '-before') as TLShapeId,
			opacity: prevAfter.opacity / 2,
			props: { ...prevBefore.props },
			meta: {
				...prevBefore.meta,
				changeType: showShadows ? 'update-before-shadow' : 'update-before',
			},
		}

		const after = {
			...prevAfter,
			props: { ...prevAfter.props },
			meta: {
				...prevAfter.meta,
				changeType: showShadows ? 'update-after-shadow' : 'update-after',
			},
		}

		if ('dash' in before.props) {
			before.props.dash = 'dashed'
		}
		if ('fill' in before.props) {
			before.props.fill = 'none'
		}
		if ('dash' in after.props) {
			after.props.dash = 'solid'
		}

		diffShapes.push(before)
		diffShapes.push(after)
	}

	for (const key in diff.added) {
		const id = key as TLShapeId
		const prevShape = diff.added[id]
		if (prevShape.typeName !== 'shape') continue
		const shape = {
			...prevShape,
			props: { ...prevShape.props },
			meta: {
				...prevShape.meta,
				changeType: showShadows ? 'create-shadow' : 'create',
			},
		}
		if ('dash' in shape.props) {
			shape.props.dash = 'solid'
		}
		diffShapes.push(shape)
	}

	return diffShapes
}