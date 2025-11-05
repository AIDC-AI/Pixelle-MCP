'use client'

import { Editor } from 'tldraw'
import { ChatHistoryPromptItem } from '../../../shared/types/ChatHistoryItem'

interface IProps {
	item: ChatHistoryPromptItem
	editor: Editor
}

const ChatHistoryPrompt: React.FC<IProps> = ({ item, editor }) => {
	const { contextItems, message, selectedShapes } = item

	const showTags = selectedShapes.length > 0 || contextItems.length > 0

	return (
		<div className="chat-history-prompt-container">
			<div className="chat-history-prompt">
				{showTags && (
					<div className="prompt-tags">
						{/* {selectedShapes.length > 0 && <SelectionTag />}
						{contextItems.map((contextItem, i) => (
							<ContextItemTag editor={editor} key={'context-item-' + i} item={contextItem} />
						))} */}
					</div>
				)}
				{message}
			</div>
		</div>
	)
}

export default ChatHistoryPrompt;