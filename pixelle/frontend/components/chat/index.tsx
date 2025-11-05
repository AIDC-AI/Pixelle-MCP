"use client";

import React from "react";
import { TldrawAgent } from "@/agent/TldrawAgent";
import ChatFallback from "./fallback";
import { ErrorBoundary } from "tldraw";
import ChatList from "./list";
import ChatInput from "./input";

interface IProps {
  agent?: TldrawAgent | undefined
}

const Chat: React.FC<IProps> = ({ agent }) => {
  return <ErrorBoundary fallback={ChatFallback}>
  {
      agent && <div className="flex flex-col h-full text-sm border-l-[#1A1A1C] bg-[#202025] text-[#D9D9D9] overflow-y-hidden">
        <ChatList agent={agent} />
        <ChatInput agent={agent} />
      </div>
    }
  </ErrorBoundary>
}

export default Chat;