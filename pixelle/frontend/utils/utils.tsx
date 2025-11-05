import { FileType } from "@/types/chat";
import { IStep } from "@chainlit/react-client";

export const flattenMessages = (
  messages: IStep[], 
  condition: (node: IStep) => boolean
) => {
  return messages.reduce((acc: IStep[], node) => {
    if (condition(node)) {
      acc.push(node);
    }
    
    if (node.steps?.length) {
      acc.push(...flattenMessages(node.steps, condition));
    }
    
    return acc;
  }, []);
}

export const getFileShortName = (name: string) => {
  const parts = name.split('.')
  const MAX_LENGTH = 6
  if (parts.length > 1) {
    if (parts[0].length > MAX_LENGTH) {
      return `${parts[0].slice(0, MAX_LENGTH)}....${parts[1]}`
    }
    return name
  }
  return `${name.slice(0, MAX_LENGTH)}...`
}

export const detectType = (url: string): FileType => {
  if (url.startsWith('image/')) return FileType.IMAGE;
  if (url.startsWith('audio/')) return FileType.AUDIO;
  if (url.startsWith('video/')) return FileType.VIDEO;
  return FileType.OTHER;
};