'use client'

import { Tldraw } from "tldraw";
import { TldrawAgent } from "@/agent/TldrawAgent";
import AppInner from "./appInner";

interface IProps {
  setAgent: (agent: TldrawAgent) => void
}

const Canvas: React.FC<IProps> = ({ setAgent }) => {  
  return <div className="w-full h-full">
    <Tldraw
      persistenceKey="tldraw-agent-demo"
      // hideUi={true}
    >
      <AppInner setAgent={setAgent} />
    </Tldraw>
  </div>
}

export default Canvas;