'use client'

import { TldrawAgent } from "@/agent/TldrawAgent";
import { getAgentHistorySections } from "@/utils/history";
import { IElement, IStep, useChatData, useChatMessages } from "@chainlit/react-client";
import { useEffect, useMemo, useRef } from "react";
import { useValue } from "tldraw";
import Message from "../message";
import { flattenMessages } from "@/utils/utils";

interface IProps {
  agent: TldrawAgent
}

const ChatList: React.FC<IProps> = ({ agent }) => {
  const historyItems = useValue(agent.$chatHistory)
	// const sections = getAgentHistorySections(historyItems)
  const { messages } = useChatMessages();
  const { elements } = useChatData();
	const ref = useRef<HTMLDivElement>(null)
	const previousScrollDistanceFromBottomRef = useRef<number>(0)

	const flatMessages = useMemo(() => {
    return flattenMessages(messages, (message: IStep) => message.type.includes("message"))
  }, [messages])
	
	const elementMap = useMemo(() => {
		return elements.reduce((acc: Record<string, IElement>, element) => {
			acc[element.forId] = element;
			return acc;
		}, {})
	}, [elements])
  console.log('flatMessages-->', flatMessages, elementMap)

  useEffect(() => {
		if (!ref.current) return

		// If a new prompt is submitted by the user, scroll to the bottom
		// if (historyItems.at(-1)?.type === 'prompt') {
		// 	if (previousScrollDistanceFromBottomRef.current <= 0) {
		// 		ref.current.scrollTo(0, ref.current.scrollHeight)
		// 		previousScrollDistanceFromBottomRef.current = 0
		// 	}
		// 	return
		// }

		// // If the user is scrolled to the bottom, keep them there while new actions appear
		// if (previousScrollDistanceFromBottomRef.current <= 0) {
		// 	const scrollDistanceFromBottom = ref.current.scrollHeight - ref.current.scrollTop - ref.current.clientHeight

		// 	if (scrollDistanceFromBottom > 0) {
		// 		ref.current.scrollTo(0, ref.current.scrollHeight)
		// 	}
		// }
	}, [ref, historyItems])

  const handleScroll = () => {
		if (!ref.current) return
		const scrollDistanceFromBottom = ref.current.scrollHeight - ref.current.scrollTop - ref.current.clientHeight

		previousScrollDistanceFromBottomRef.current = scrollDistanceFromBottom
	}

  return <div 
    className="relative p-4 flex flex-col gap-4 w-full h-full overflow-y-auto"
    ref={ref}
    onScroll={handleScroll}
  >
    {
			flatMessages?.map((message: IStep) => <Message message={message} element={elementMap[message.id]} />)
		}
  </div>
}

export default ChatList;