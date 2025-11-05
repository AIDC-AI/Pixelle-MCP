'use client'

import { TldrawAgent } from "@/agent/TldrawAgent"
import { useTldrawAgent } from "@/agent/useTldrawAgent"
import { AGENT_ID } from "@/constans/data"
import { useEffect } from "react"
import { useEditor } from "tldraw"

interface IPorps {
  setAgent: (agent: TldrawAgent) => void
}

const AppInner: React.FC<IPorps> = ({ setAgent }) => {
	const editor = useEditor()
	const agent = useTldrawAgent(editor, AGENT_ID)

	useEffect(() => {
		if (!editor || !agent) return
		setAgent(agent)
		;(window as any).editor = editor
		;(window as any).agent = agent
	}, [agent, editor, setAgent])

	return null
}

export default AppInner;