// WebSocket Hook
// Real-time communication hooks for the frontend

import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuthStore } from '../stores/authStore';
import { createWebSocketUrl } from '../utils/api';
import type { WSMessage, WSChatMessage, WSLocationUpdate, WSTransitUpdate, WSItineraryUpdate, WSNotification } from '../types';

// WebSocket connection state
interface UseWebSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  error: string | null;
  sendMessage: (event: string, data: any) => void;
  onMessage: (event: string, handler: (data: any) => void) => () => void;
}

// Main WebSocket hook
export function useWebSocket(path: string = '/ws'): UseWebSocketReturn {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const handlersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  const token = useAuthStore.getState().tokens?.access_token;

  useEffect(() => {
    if (!token) {
      setError('No authentication token');
      return;
    }

    const wsUrl = createWebSocketUrl(path);
    const socket = io(wsUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      setIsConnected(true);
      setError(null);
    });

    socket.on('disconnect', (reason) => {
      setIsConnected(false);
      if (reason === 'io server disconnect') {
        setError('Disconnected by server');
      }
    });

    socket.on('connect_error', (err) => {
      setError(err.message);
    });

    socket.on('error', (err: any) => {
      setError(err.message || 'WebSocket error');
    });

    // Handle all incoming messages
    socket.onAny((event, data) => {
      const handlers = handlersRef.current.get(event);
      if (handlers) {
        handlers.forEach(handler => handler(data));
      }
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
// Chat-specific WebSocket hook
export function useChatWebSocket(conversationId: string) {
  const { sendMessage, onMessage, isConnected, error } = useWebSocket('/ws/chat');
  const [messages, setMessages] = useState<WSChatMessage[]>([]);
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!conversationId) return;

    // Join conversation room
    sendMessage('join_conversation', { conversation_id: conversationId });

    // Listen for new messages
    const unsubscribeMessage = onMessage('new_message', (data: WSChatMessage) => {
      setMessages(prev => [...prev, data]);
    });

    // Listen for typing indicators
    const unsubscribeTyping = onMessage('user_typing', (data: { user_id: string; is_typing: boolean }) => {
      setTypingUsers(prev => {
        const next = new Set(prev);
        if (data.is_typing) {
          next.add(data.user_id);
        } else {
          next.delete(data.user_id);
        }
        return next;
      });
    });

    // Listen for read receipts
    const unsubscribeRead = onMessage('message_read', (data: { message_id: string; user_id: string }) => {
      setMessages(prev => prev.map(msg => 
        msg.message_id === data.message_id 
          ? { ...msg, read_by: [...(msg.read_by || []), data.user_id] }
          : msg
      ));
    });

    return () => {
      unsubscribeMessage();
      unsubscribeTyping();
      unsubscribeRead();
      sendMessage('leave_conversation', { conversation_id: conversationId });
    };
  }, [conversationId, sendMessage, onMessage]);

  const sendChatMessage = useCallback((content: string, attachments?: any[]) => {
    sendMessage('send_message', {
      conversation_id: conversationId,
      content,
      attachments,
    });
  }, [conversationId, sendMessage]);

  const sendTyping = useCallback((isTyping: boolean) => {
    sendMessage('typing', {
      conversation_id: conversationId,
      is_typing: isTyping,
    });
  }, [conversationId, sendMessage]);

  const markAsRead = useCallback((messageId: string) => {
    sendMessage('mark_read', {
      conversation_id: conversationId,
      message_id: messageId,
    });
  }, [conversationId, sendMessage]);

  return {
    isConnected,
    error,
    messages,
    typingUsers: Array.from(typingUsers),
    sendMessage: sendChatMessage,
    sendTyping,
    markAsRead,
  };
}
      setIsConnected(false);
    };
  }, [token, path]);

  const sendMessage = useCallback((event: string, data: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, []);

  const onMessage = useCallback((event: string, handler: (data: any) => void) => {
    if (!handlersRef.current.has(event)) {
      handlersRef.current.set(event, new Set());
    }
    handlersRef.current.get(event)!.add(handler);

    // Return cleanup function
    return () => {
      handlersRef.current.get(event)?.delete(handler);
    };
  }, []);

  return {
    socket: socketRef.current,
    isConnected,
    error,
    sendMessage,
    onMessage,
  };
}