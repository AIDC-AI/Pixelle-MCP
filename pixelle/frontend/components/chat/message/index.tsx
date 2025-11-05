import { IElement, IStep } from "@chainlit/react-client";
import { memo } from "react";
import UserMessage from "./userMessage";
import AssistantMessage from "./assistantMessage";

interface IProps {
  message: IStep
  element?: IElement
}

const Message: React.FC<IProps> = memo(({ message, element }) => {
  if (message.type === 'user_message') {
    return <UserMessage message={message} element={element} />
  } else if (message.type === 'assistant_message') {
    return <AssistantMessage message={message} element={element} />
  }
    
  return null
})

export default Message;