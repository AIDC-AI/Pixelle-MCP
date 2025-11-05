import { DEFAULT_ICON_CLASSNAME } from "@/constans/data"

interface IProps {
  className?: string
}

const CloseIcon: React.FC<IProps> = ({ className = DEFAULT_ICON_CLASSNAME }) => {
  return <svg viewBox="0 0 1024 1024" fill='currentColor' className={className}>
    <path d="M512 0a512 512 0 1 1 0 1024A512 512 0 0 1 512 0zM380.224 326.784a38.4 38.4 0 0 0-48.96 58.752L457.6 512 331.264 638.464l-4.48 5.312a38.4 38.4 0 0 0 58.752 48.96L512 566.4l126.464 126.4 5.312 4.48a38.4 38.4 0 0 0 48.96-58.752L566.4 512l126.4-126.464 4.48-5.312a38.4 38.4 0 0 0-58.752-48.96L512 457.6 385.536 331.264z">
    </path>
  </svg>
}

export default CloseIcon
