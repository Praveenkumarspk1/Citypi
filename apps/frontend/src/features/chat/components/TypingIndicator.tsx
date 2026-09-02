interface TypingIndicatorProps {
  userName?: string;
}

export function TypingIndicator({ userName = 'Assistant' }: TypingIndicatorProps) {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
        <span className="text-sm">AI</span>
      </div>
      <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 border border-gray-200">
        <div className="flex gap-1">
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}
