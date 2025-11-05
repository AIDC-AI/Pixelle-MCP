import { ChatHistoryActionItem, ChatHistoryContinuationItem, ChatHistoryPromptItem } from "@/shared/types/ChatHistoryItem"

export interface ChatHistorySection {
	prompt: ChatHistoryPromptItem
	items: (ChatHistoryActionItem | ChatHistoryContinuationItem)[]
}

export interface ChatHistoryGroup {
	items: ChatHistoryActionItem[]
	withDiff: boolean
}

export enum FileType {
	IMAGE = 'image',
	VIDEO = 'video',
	AUDIO = 'audio',
	DOCUMENT = 'document',
	OTHER = 'other',
}

export interface IFileProps {
	id: string
	type: string
	name: string
	size: number
	url: string
	serverId?: string
	uploaded?: boolean
	uploadProgress?: number
}