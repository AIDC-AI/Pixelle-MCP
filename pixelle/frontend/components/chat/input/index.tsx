'use client'

import { TldrawAgent } from "@/agent/TldrawAgent";
import { convertTldrawShapeToSimpleShape } from "@/shared/format/convertTldrawShapeToSimpleShape";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useValue } from "tldraw";
import {
  IStep,
  useChatInteract,
  useChatSession,
} from "@chainlit/react-client";
import { useRecoilValue } from "recoil";
import { v4 as uuidv4 } from 'uuid';
import FileIcon from "@/components/icons/file";
import { FileType, IFileProps } from "@/types/chat";
import { API_BASE } from "@/constans/data";
import ChatPauseIcon from "@/components/icons/chat-pause";
import ChatSubmitIcon from "@/components/icons/chat-submit";
import Media from "@/components/Media";
import CloseIcon from "@/components/icons/close";
import { detectType, getFileShortName } from "@/utils/utils";

interface IProps {
  agent: TldrawAgent 
}

const ChatInput: React.FC<IProps> = ({ agent }) => {
	const { editor } = agent
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
	const [inputValue, setInputValue] = useState<string>('')
  const [uploading, setUploading] = useState(false)
  const [files, setFiles] = useState<IFileProps[]>([])
  const { sendMessage, uploadFile } = useChatInteract();
	const isGenerating = useValue('isGenerating', () => agent.isGenerating(), [agent])
	const modelName = useValue(agent.$modelName)
  const isContextToolActive = useValue(
		'isContextToolActive',
		() => {
			const tool = editor.getCurrentTool()
			return tool.id === 'target-shape' || tool.id === 'target-area'
		},
		[editor]
	)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!inputRef.current) return
    const content = inputValue.trim();
    if (content || files?.length > 0) {
      const message: IStep = {
        threadId: '',
        name: "User",
        type: "user_message",
        output: content,
        id: uuidv4(),
        createdAt: new Date().toISOString(),
        metadata: { location: window.location.href }
      };
      const fileReferences = files.filter((file) => !!file.serverId && file.serverId !== '').map((file) => ({
        id: file.serverId!,
      })) || [];
      sendMessage(message, fileReferences);
      setInputValue("");
      setFiles([]);
      if (inputRef.current) inputRef.current.value = ''
    }
    return;
    const formData = new FormData(e.currentTarget)
    const value = formData.get('input') as string

    // If the user's message is empty, just cancel the current request (if there is one)
    if (value === '') {
      agent.cancel()
      return
    }

    // If every todo is done, clear the todo list
    const todosRemaining = agent.$todoList.get().filter((item) => item.status !== 'done')
    if (todosRemaining.length === 0) {
      agent.$todoList.set([])
    }

    // Grab the user query and clear the chat input
    const message = value
    const contextItems = agent.$contextItems.get()
    agent.$contextItems.set([])
    const _el = inputRef.current
    if (_el) _el.value = ''

    // Prompt the agent
    const selectedShapes = editor.getSelectedShapes().map((shape) => convertTldrawShapeToSimpleShape(editor, shape))

    await agent.prompt({
      message,
      contextItems,
      bounds: editor.getViewportPageBounds(),
      modelName,
      selectedShapes,
      type: 'user',
    })
  }

  const handlePickFile = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files
    if (!fileList || fileList.length === 0) return
    try {
      setUploading(true)
      const arr = Array.from(fileList)
      const fileResults = arr.map((file) => {
        const id = uuidv4();
        const previewUrl = URL.createObjectURL(file);
        const { xhr, promise } = uploadFile(file, (progress) => {
          setFiles((prev) => prev.map((item) => {
            if (item.id === id) {
              return {
                ...item,
                uploadProgress: progress,
              }
            }
            return item
          })
        )})
        promise
          .then((res) => {
            setFiles((prev) => prev.map((item) => {
              if (item.id === id) {
                return {
                  ...item,
                  serverId: res.id,
                  uploaded: true,
                  uploadProgress: 100,
                }
              }
              return item
            }))
          })
          .catch((error) => {
            
          })

        return {
          id,
          type: file.type,
          name: file.name,
          size: file.size,
          url: previewUrl,
          uploadProgress: 0
        }
      })
      setFiles((prev) => [...prev, ...fileResults])
      return
      if (results?.length > 0) {
        const list = results.filter((result: any) => !!result).map((result: any) => {
          return {
            id: result.id,
            type: result.type,
            name: result.name,
            size: result.size,
            url: result.url,
          }
        })
        setFiles((prev) => [...prev, ...list])
      }
      const uploaded = await Promise.all(arr.map(async (file) => {
        const form = new FormData()
        form.append('file', file)
        const res = await fetch(`${API_BASE}/files/upload`, { method: 'POST', body: form })
        const data = await res.json()
        if (!res.ok) throw new Error(data?.detail || data?.error || 'Upload failed')
        const id: string = data.file_id || ''
        const contentType: string = data.content_type || ''
        const name: string = data.filename || file.name || ''
        const url: string = data.url || ''
        const size: number = data.size || file.size || 0
        let type: FileType = FileType.OTHER
        if (contentType.startsWith('image/')) type = FileType.IMAGE
        else if (contentType.startsWith('audio/')) type = FileType.AUDIO
        else if (contentType.startsWith('video/')) type = FileType.VIDEO
        return { id, type, name, url, size } as IFileProps
      }))
      setFiles((prev) => [...prev, ...uploaded])
    } catch (err) {
      // no-op, rely on UI toast elsewhere if needed
    } finally {
      setUploading(false)
      if (e.target) e.target.value = ''
    }
  }, [API_BASE])

  return <div className="relative flex flex-col flex-1">
    <div className="sticky shrink-0 bottom-0 rounded-xl m-2 bg-[#202025] z-[9999]">
      <form 
        className="flex flex-col gap-2 p-2 rounded-xl bg-[#ffffff1a] text-[#8c8c8c]"
        onSubmit={(e) => {
          e.preventDefault()
					setInputValue('')
          handleSubmit(e)
        }}
      >
        {
          files?.length > 0 && <div className="p-2 flex flex-row gap-2 overflow-x-auto">
            {
              files?.map((file: IFileProps) => (
                <div 
                  key={file.url}
                  className="relative flex flex-col justify-center items-center p-2 bg-[#e9e9e9] rounded-lg"
                >
                  <Media 
                    url={file.url}
                    type={detectType(file.type)}
                    className="w-6 h-6"
                  />
                  <p className="text-xs text-[#363636] mt-2">
                    {getFileShortName(file.name)}
                  </p>
                  <button
                    onClick={() => setFiles((prev) => prev.filter((f) => f.url !== file.url))}
                    className="absolute top-0 right-0 translate-x-1/2 -translate-y-1/2"
                  >
                    <CloseIcon />
                  </button>
                </div>
              ))
            }
          </div>
        }
        <textarea
          ref={inputRef}
          name="input"
          autoComplete="off"
					placeholder="Ask, learn, brainstorm, draw"
          className="flex flex-1 py-2 mb-4 border-none outline-none resize-none rounded-sm w-full"
          onInput={(e) => setInputValue(e.currentTarget.value)}
					onKeyDown={(e) => {
						if (e.key === 'Enter' && !e.shiftKey) {
							e.preventDefault()
							const form = e.currentTarget.closest('form')
							if (form) {
								const submitEvent = new Event('submit', { bubbles: true, cancelable: true })
								form.dispatchEvent(submitEvent)
							}
						}
					}}
        />
        <div className="w-full flex justify-between items-center">
          <div className="flex justify-center items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={handleFileChange}
            />
            <button
              type="button"
              onClick={handlePickFile}
              className="flex justify-center items-center text-[#f1f1f1] cursor-pointer disabled:cursor-not-allowed"
              disabled={uploading || isGenerating}
              title={uploading ? 'Uploading...' : 'Attach file'}
            >
              <FileIcon />
            </button>
          </div>
          <button
            type="submit"
            className="flex justify-center items-center text-[#f1f1f1] cursor-pointer disabled:text-[#999] disabled:cursor-not-allowed"
            disabled={(inputValue === '' && files?.length === 0 && !isGenerating) || uploading}
          >
            {
              isGenerating ? <ChatPauseIcon /> : <ChatSubmitIcon />
            }
          </button>
        </div>
      </form>
    </div>
  </div>
}

export default ChatInput;