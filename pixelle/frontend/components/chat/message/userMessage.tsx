import Media from "@/components/Media";
import { detectType } from "@/utils/utils";
import { IElement, IStep } from "@chainlit/react-client";

interface IProps {
  message: IStep
  element?: IElement
} 

const UserMessage: React.FC<IProps> = ({ message, element }) => {
  return (
    <div className="flex p-2 bg-[#FFFFFF1A] rounded-lg">
      <div>{message.output}</div>
      {
        element && <Media url={element.url || ''} type={detectType(element.mime || '')} />
      }
    </div>
  )
}

export default UserMessage;