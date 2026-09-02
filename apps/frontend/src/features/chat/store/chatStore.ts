import { create } from 'zustand';

interface ChatState {
  activeConversationId: string | null;
  isStreaming: boolean;
  streamingContent: string;
  setActiveConversation: (id: string | null) => void;
  setStreaming: (streaming: boolean) => void;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (token: string) => void;
  clearStreamingContent: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  activeConversationId: null,
  isStreaming: false,
  streamingContent: '',
  setActiveConversation: (id) => set({ activeConversationId: id }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setStreamingContent: (content) => set({ streamingContent: content }),
  appendStreamingContent: (token) =>
    set((state) => ({ streamingContent: state.streamingContent + token })),
  clearStreamingContent: () => set({ streamingContent: '' }),
}));
