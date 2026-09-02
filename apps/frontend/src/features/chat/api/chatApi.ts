import { apiClient } from '@shared/utils/api';
import type { Message, SendMessageParams } from '../types/chat';

export const chatApi = {
  getMessages: async (conversationId: string): Promise<Message[]> => {
    const { data } = await apiClient.get(`/conversations/${conversationId}/messages`);
    return data.items;
  },

  sendMessage: async (conversationId: string, params: SendMessageParams): Promise<Message> => {
    const { data } = await apiClient.post(`/conversations/${conversationId}/messages`, params);
    return data;
  },

  streamMessage: async (
    conversationId: string,
    content: string,
    onToken: (token: string) => void,
    onComplete: () => void,
  ): Promise<void> => {
    const response = await fetch(
      `${apiClient.defaults.baseURL}/conversations/${conversationId}/messages/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ content }),
      },
    );

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (reader) {
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const json = JSON.parse(line.slice(6));
            if (json.type === 'token') onToken(json.content);
            if (json.type === 'done') onComplete();
          }
        }
      }
    }
  },

  transcribeAudio: async (audioBlob: Blob): Promise<{ text: string }> => {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    const { data } = await apiClient.post('/media/transcribe', formData);
    return data;
  },
};
