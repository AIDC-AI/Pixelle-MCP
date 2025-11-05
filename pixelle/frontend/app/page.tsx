'use client'

import ChatPanel from "@/components/chat-panel";
import { LOCAL_HOST } from "@/constans/data";
import { ChainlitContext, useChatData, useChatSession } from "@chainlit/react-client";
import { useContext, useEffect } from "react";

const Home = () => {
  const { connect, sessionId } = useChatSession();
  const { connected } = useChatData()
  console.log('-connected->', connected)
  const apiClient = useContext(ChainlitContext);
  
  useEffect(() => {
    connect({
      userEnv: {

      }
    })  
  }, [])
  
  useEffect(() => {
    if (connected && !sessionId) {
      apiClient.connectStreamableHttpMCP(sessionId, 'pixelle-mcp', `/pixelle/mcp`)
    }
  }, [connected, sessionId])
  
  return (
    <ChatPanel />
  );
}

export default Home;