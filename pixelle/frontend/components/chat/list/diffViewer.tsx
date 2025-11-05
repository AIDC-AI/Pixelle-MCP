'use client'

import { forwardRef, useMemo } from "react"
import { DefaultShapeWrapper, RecordsDiff, TLRecord, TLShapeWrapperProps } from "tldraw"
import Viewer from "./viewer"
import { getDiffShapesFromDiff } from "@/utils/history"

interface IProps {
  diff: RecordsDiff<TLRecord> 
}

const DiffViewer: React.FC<IProps> = ({ diff }) => {
  const diffShapes = useMemo(() => getDiffShapesFromDiff(diff), [diff])
	return <Viewer shapes={diffShapes} components={{ ShapeWrapper: DiffShapeWrapper }} />
}

const DiffShapeWrapper = forwardRef(function DiffShapeWrapper(
	{ children, shape, isBackground }: TLShapeWrapperProps,
	ref: React.Ref<HTMLDivElement>
) {
	const changeType = shape.meta.changeType

	return (
		<DefaultShapeWrapper
			ref={ref}
			shape={shape}
			isBackground={isBackground}
			className={changeType ? 'diff-shape-' + changeType : undefined}
		>
			{children}
		</DefaultShapeWrapper>
	)
})

export default DiffViewer;