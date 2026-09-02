import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '../api/chatApi';
import type { Message, SendMessageParams } from '../types/chat';

export function useChat(conversationId: string | undefined) {
  const queryClient = useQueryClient();

  const messagesQuery = useQuery({
    queryKey: ['chat', conversationId, 'messages'],
    queryFn: () => chatApi.getMessages(conversationId!),
    enabled: !!conversationId,
  });

  const sendMessageMutation = useMutation({
    mutationFn: (params: SendMessageParams) =>
      chatApi.sendMessage(conversationId!, params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', conversationId, 'messages'] });
    },
  });

  return {
    messages: messagesQuery.data ?? [],
    isLoading: messagesQuery.isLoading,
    sendMessage: sendMessageMutation.mutateAsync,
    isSending: sendMessageMutation.isPending,
  };
}

export function useStreamingChat(conversationId: string | undefined) {
  const queryClient = useQueryClient();

  const startStream = async (content: string, onToken: (token: string) => void) => {
    return chatApi.streamMessage(conversationId!, content, onToken, () => {
      queryClient.invalidateQueries({ queryKey: ['chat', conversationId, 'messages'] });
    });
  };

  return { startStream };
}

export function useVoiceInput() {
  const transcribeMutation = useMutation({
    mutationFn: (audioBlob: Blob) => chatApi.transcribeAudio(audioBlob),
  });

  return {
    transcribe: transcribeMutation.mutateAsync,
    isTranscribing: transcribeMutation.isPending,
  };
}
