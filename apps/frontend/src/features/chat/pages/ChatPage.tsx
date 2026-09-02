// ChatPage Component
// Main chat page with conversation list and chat window

import { useState } from 'react';
import { useConversations, useCreateConversation } from '@shared/hooks/useApi';
import { ChatWindow } from '../components/ChatWindow';
import type { Conversation } from '@shared/types';

export function ChatPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  
  const { data: conversationsData, isLoading: conversationsLoading } = useConversations(
    { page: 1, page_size: 20 }
  );
  
  const createConversationMutation = useCreateConversation();
  
  const conversations = conversationsData?.items || [];
  
  const handleNewConversation = async () => {
    setIsCreating(true);
    try {
      const conversation = await createConversationMutation.mutateAsync({
        initial_message: '',
        context: {},
      });
      setSelectedConversationId(conversation.id);
      setIsCreating(false);
    } catch (error) {
      console.error('Failed to create conversation:', error);
      setIsCreating(false);
    }
  };
  
  const handleConversationSelect = (conversation: Conversation) => {
    setSelectedConversationId(conversation.id);
    setShowSidebar(false);
  };
  
  return (
    <div className="h-[calc(100vh-4rem)] flex">
      {/* Sidebar - Conversations */}
      <aside className={`w-80 bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ${showSidebar ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Conversations</h2>
          <button className="lg:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100" onClick={() => setShowSidebar(false)}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>
        
        <div className="p-4 border-b border-gray-200">
          <button 
            onClick={handleNewConversation}
            disabled={isCreating}
            className="btn-primary w-full justify-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {isCreating ? 'Creating...' : 'New Chat'}
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversationsLoading ? (
            <div className="p-4 text-center text-gray-500">
              <svg className="w-6 h-6 animate-spin mx-auto text-primary-600" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          ) : conversations.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <svg className="w-12 h-12 mx-auto text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p className="text-sm">No conversations yet</p>
              <p className="text-xs text-gray-400 mt-1">Start a new chat to begin</p>
            </div>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => handleConversationSelect(conv)}
                className={`w-full text-left p-3 rounded-lg transition-colors flex items-start gap-3 ${
                  selectedConversationId === conv.id
                    ? 'bg-primary-50'
                    : 'hover:bg-gray-100'
                }`}
              >
                <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-gray-900 truncate">{conv.title || 'Untitled Conversation'}</p>
                  <p className="text-xs text-gray-500 truncate">
                    {conv.last_message_at 
                      ? new Date(conv.last_message_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : new Date(conv.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </button>
            ))
          )}
        </div>
      </aside>
      
      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedConversationId ? (
          <ChatWindow 
            conversationId={selectedConversationId}
            onNewConversation={(conversation) => {
              setSelectedConversationId(conversation.id);
              setShowSidebar(false);
            }}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
            <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900">Start a Conversation</h3>
            <p className="text-sm text-gray-500 mt-1 text-center max-w-xs">
              Ask me anything about your trip - places to visit, transit routes, weather, or create an itinerary!
            </p>
            <button 
              onClick={handleNewConversation}
              disabled={isCreating}
              className="btn-primary mt-6"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              {isCreating ? 'Creating...' : 'New Chat'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}