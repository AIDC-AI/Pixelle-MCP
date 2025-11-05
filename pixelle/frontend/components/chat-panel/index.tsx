'use client'

import { TldrawAgent } from "@/agent/TldrawAgent";
import Canvas from "@/components/canvas";
import Chat from "@/components/chat";
import { enableLinedFillStyle } from "@/utils/enableLinedFillStyle";
import { useState } from "react";
import { DefaultSizeStyle, TldrawUiToastsProvider } from "tldraw";

DefaultSizeStyle.setDefaultValue('s')
enableLinedFillStyle()

const ChatPanel = () => {
	const [agent, setAgent] = useState<TldrawAgent | undefined>()
  
  return <TldrawUiToastsProvider>
    <div className="fixed inset-0 grid grid-cols-[minmax(0,1fr)_350px] max-md:grid-cols-1 max-md:grid-rows-[1fr_auto]">
      <Canvas setAgent={setAgent} />
      <Chat agent={agent} />
    </div>
  </TldrawUiToastsProvider>
}

export default ChatPanel;