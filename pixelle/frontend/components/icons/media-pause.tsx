import { DEFAULT_ICON_CLASSNAME } from "@/constans/data"

interface IProps {
  className?: string
}

const MediaPauseIcon: React.FC<IProps> = ({ className = DEFAULT_ICON_CLASSNAME }) => {
  return <svg viewBox="0 0 1024 1024" fill='currentColor' className={className}>
    <path 
      d="M6.04995 2.74998C6.04995 2.44623 5.80371 2.19998 5.49995 2.19998C5.19619 2.19998 4.94995 2.44623 4.94995 2.74998V12.25C4.94995 12.5537 5.19619 12.8 5.49995 12.8C5.80371 12.8 6.04995 12.5537 6.04995 12.25V2.74998Z" 
      fillRule="evenodd" 
      clipRule="evenodd"
      className="animate-bounce"
      style={{ animationDuration: '1.5s', animationDelay: '0s' }}
    />
    <path 
      d="M10.05 2.74998C10.05 2.44623 9.80371 2.19998 9.49995 2.19998C9.19619 2.19998 8.94995 2.44623 8.94995 2.74998V12.25C8.94995 12.5537 9.19619 12.8 9.49995 12.8C9.80371 12.8 10.05 12.5537 10.05 12.25V2.74998Z" 
      fillRule="evenodd" 
      clipRule="evenodd"
      className="animate-bounce"
      style={{ animationDuration: '1.5s', animationDelay: '0.3s' }}
    />
  </svg>
}

export default MediaPauseIcon