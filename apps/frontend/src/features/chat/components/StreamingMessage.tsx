interface StreamingMessageProps {
  content: string;
  isComplete: boolean;
}

export function StreamingMessage({ content, isComplete }: StreamingMessageProps) {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
        <span className="text-sm">AI</span>
      </div>
      <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-2 border border-gray-200">
        <p className="whitespace-pre-wrap text-sm">
          {content}
          {!isComplete && (
            <span className="inline-block w-2 h-4 bg-primary-500 animate-pulse ml-0.5 align-middle" />
          )}
        </p>
      </div>
    </div>
  );
}
