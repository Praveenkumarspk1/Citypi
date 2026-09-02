// ChatWindow Component
// Main chat interface with message history and input

import { 
  Send, 
  Mic, 
  Image, 
  Paperclip, 
  X, 
  Loader2, 
  MessageSquare, 
  Bot, 
  User, 
  Check, 
  CheckCheck 
} from 'lucide-react';
import { useState, useRef, useEffect, useCallback } from 'react';
import { useConversationMessages, useSendMessage, useCreateConversation } from '@shared/hooks/useApi';
import { queryKeys } from '@shared/utils/api';
import type { Message, Conversation } from '@shared/types';

interface ChatWindowProps {
  conversationId?: string;
  onNewConversation?: (conversation: Conversation) => void;
}

export function ChatWindow({ conversationId, onNewConversation }: ChatWindowProps) {
  const [newMessage, setNewMessage] = useState('');
  const [isRecording] = useState(false);
  const [attachments, setAttachments] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  const { data: messagesData, isLoading, error, refetch } = useConversationMessages(
    conversationId || '',
    { page: 1, page_size: 50 },
    { 
      enabled: !!conversationId,
      queryKey: queryKeys.conversations.messages(conversationId || '', { page: 1, page_size: 50 }),
    }
  );
  
  const sendMessageMutation = useSendMessage();
  const createConversationMutation = useCreateConversation();
  
  const messages = messagesData?.items || [];
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);
  
  const handleSendMessage = useCallback(async () => {
    if (!newMessage.trim() && attachments.length === 0) return;
    if (sendMessageMutation.isPending) return;
    
    const content = newMessage.trim();
    const files = [...attachments];
    
    setNewMessage('');
    setAttachments([]);
    
    try {
      if (!conversationId) {
        // Create new conversation first
        const conversation = await createConversationMutation.mutateAsync({
          initial_message: content,
          context: {},
        });
        
        if (onNewConversation) {
          onNewConversation(conversation);
        }
        
        // Send message in new conversation
        await sendMessageMutation.mutateAsync({
          conversationId: conversation.id,
          data: { content, attachments: files },
        });
        
        refetch();
      } else {
        await sendMessageMutation.mutateAsync({
          conversationId,
          data: { content, attachments: files },
        });
        
        refetch();
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Error handling would go here
    }
  }, [newMessage, attachments, conversationId, sendMessageMutation, createConversationMutation, onNewConversation, refetch]);
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachments(prev => [...prev, ...files].slice(0, 5)); // Max 5 attachments
    e.target.value = '';
  };
  
  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };
  
  const handleVoiceInput = () => {
    // Voice input implementation would go here
    console.log('Voice input clicked');
  };
  
  if (!conversationId && !onNewConversation) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-gray-500">
        <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mb-4">
          <MessageSquare className="w-8 h-8 text-primary-600" />
        </div>
        <h3 className="text-lg font-medium text-gray-900">Start a Conversation</h3>
        <p className="text-sm text-gray-500 mt-1 text-center max-w-xs">
          Ask me anything about your trip - places to visit, transit routes, weather, or create an itinerary!
        </p>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col h-full bg-white">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading && messages.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
          </div>
        ) : (
          <>
            {messages.map((message: Message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {sendMessageMutation.isPending && (
              <MessageBubble
                message={{
                  id: 'pending',
                  role: 'assistant',
                  content: '',
                  type: 'text',
                  created_at: new Date().toISOString(),
                } as Message}
                isStreaming
              />
            )}
            <div ref={messagesEndRef} />
          </>
        )}
        
        {error && (
          <div className="text-center text-red-500 text-sm p-4">
            Failed to load messages. Please try again.
          </div>
        )}
      </div>
      
      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 p-2 border-t border-gray-100">
          {attachments.map((file, index) => (
            <div key={index} className="flex items-center gap-2 px-3 py-1 bg-gray-50 rounded-lg text-sm">
              <span className="text-gray-600 truncate max-w-[150px]">{file.name}</span>
              <span className="text-gray-400">({(file.size / 1024).toFixed(1)} KB)</span>
              <button
                onClick={() => removeAttachment(index)}
                className="text-gray-400 hover:text-red-500"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
      
      {/* Input Area */}
      <div className="p-4 border-t border-gray-100">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={conversationId ? 'Type a message...' : 'Start a new conversation...'}
              disabled={sendMessageMutation.isPending}
              className="input resize-none min-h-[44px] max-h-[150px] pr-12"
              rows={1}
            />
            <div className="absolute bottom-2 right-2 flex items-center gap-1">
              <label className="p-2 text-gray-400 hover:text-primary-600 cursor-pointer">
                <input
                  type="file"
                  onChange={handleFileSelect}
                  accept="image/*,audio/*,.pdf"
                  multiple
                  className="hidden"
                  id="file-upload"
                />
                <Paperclip className="w-5 h-5" />
              </label>
              <label className="p-2 text-gray-400 hover:text-primary-600 cursor-pointer">
                <Image className="w-5 h-5" />
              </label>
              <button
                onClick={handleVoiceInput}
                disabled={sendMessageMutation.isPending}
                className={`p-2 rounded-lg transition-colors ${
                  isRecording 
                    ? 'bg-red-100 text-red-600' 
                    : 'text-gray-400 hover:text-primary-600'
                }`}
              >
                <Mic className="w-5 h-5" />
              </button>
            </div>
          </div>
          <button
            onClick={handleSendMessage}
            disabled={sendMessageMutation.isPending || (!newMessage.trim() && attachments.length === 0)}
            className="btn-primary p-3 rounded-xl disabled:opacity-50"
            aria-label="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}

// MessageBubble Component
interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-primary-100 text-primary-600' : 'bg-gray-100 text-gray-600'
      }`}>
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <Bot className="w-4 h-4" />
        )}
      </div>
      
      <div className={`max-w-[70%] ${isUser ? 'text-right' : ''}`}>
        <div className={`inline-block px-4 py-2 rounded-2xl ${
          isUser 
            ? 'bg-primary-600 text-white rounded-tr-sm' 
            : 'bg-gray-100 text-gray-900 rounded-tl-sm'
        }`}>
          {isStreaming ? (
            <span className="flex items-center gap-1 text-gray-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Thinking...</span>
            </span>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>
        
        <div className={`flex items-center gap-2 mt-1 text-xs text-gray-400 ${isUser ? 'justify-end' : ''}`}>
          <time>{new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>
          {isAssistant && !isStreaming && (
            <>
              <Check className="w-3 h-3" />
              <CheckCheck className="w-3 h-3" />
            </>
          )}
        </div>
        
        {/* Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-2 flex gap-2">
            {message.attachments.map((attachment, index) => (
              <div key={index} className="relative w-20 h-20 rounded-lg overflow-hidden bg-gray-100">
                {attachment.type === 'image' && (
                  <img src={attachment.url} alt={attachment.name} className="w-full h-full object-cover" />
                )}
                {attachment.type !== 'image' && (
                  <div className="w-full h-full flex items-center justify-center text-gray-500">
                    <Paperclip className="w-5 h-5" />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}