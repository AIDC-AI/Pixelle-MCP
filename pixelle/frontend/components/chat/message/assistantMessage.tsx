import Media from "@/components/Media";
import { detectType } from "@/utils/utils";
import { IElement, IStep } from "@chainlit/react-client";

interface IProps {
  message: IStep
  element?: IElement
} 

const AssistantMessage: React.FC<IProps> = ({ message, element }) => {
  return (
    <div>
      {
        message.output
      }
      {
        element && <Media url={element.url || ''} type={detectType(element.mime || '')} />
      }
    </div>
  )
}

export default AssistantMessage;