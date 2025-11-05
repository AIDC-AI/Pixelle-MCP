'use client'

import { ChatHistoryInfo } from "@/shared/types/ChatHistoryInfo"

interface IProps {
  steps: ChatHistoryInfo[]
}

const DiffSteps: React.FC<IProps> = ({ steps }) =>{
	let previousDescription = ''

	return (
		<div className="agent-changes">
			{steps.map((step, i) => {
				if (!step.description) return null

				if (step.description === previousDescription) return null
				previousDescription = step.description
				return (
					<div className="agent-change" key={'intent-' + i}>
						{step.icon && (
							<span className="agent-change-icon">
								{/* <AgentIcon type={step.icon} /> */}
							</span>
						)}
						{step.description}
					</div>
				)
			})}
		</div>
	)
}

export default DiffSteps;