import type { Message } from '../types/chat';

interface MessageBubbleProps {
  message: Message;
  isOwn?: boolean;
}

export function MessageBubble({ message, isOwn = false }: MessageBubbleProps) {
  return (
    <div className={`flex gap-3 ${isOwn ? 'flex-row-reverse' : ''}`}>
      <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
        <span className="text-sm">{isOwn ? 'U' : 'AI'}</span>
      </div>
      <div
        className={`max-w-[70%] px-4 py-2 rounded-2xl ${
          isOwn
            ? 'bg-primary-600 text-white rounded-br-sm'
            : 'bg-white border border-gray-200 rounded-bl-sm'
        }`}
      >
        <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        <span className="text-[10px] opacity-60 mt-1 block">
          {new Date(message.created_at).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}
