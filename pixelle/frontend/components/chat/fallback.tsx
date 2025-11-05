'use client'

const ChatFallback = () => {
  return (
		<div className="p-2 flex justify-center items-center text-sm">
			<p>Error loading chat history</p>
			<button
				onClick={() => {
					localStorage.clear()
					window.location.reload()
				}}
			>
				Clear chat history
			</button>
		</div>
	)
}

export default ChatFallback;