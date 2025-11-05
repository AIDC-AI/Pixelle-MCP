import { DEFAULT_ICON_CLASSNAME } from "@/constans/data"

interface IProps {
  className?: string
}

const ChatPauseIcon: React.FC<IProps> = ({ className = DEFAULT_ICON_CLASSNAME }) => {
  return <svg viewBox="0 0 1024 1024" fill='currentColor' className={className}>
    <path d="M853.333333 870.4H170.666667a17.066667 17.066667 0 0 1-17.066667-17.066667V170.666667a17.066667 17.066667 0 0 1 17.066667-17.066667h682.666666a17.066667 17.066667 0 0 1 17.066667 17.066667v682.666666a17.066667 17.066667 0 0 1-17.066667 17.066667z m-665.6-34.133333h648.533334V187.733333H187.733333v648.533334z">
    </path>
  </svg>
}

export default ChatPauseIcon