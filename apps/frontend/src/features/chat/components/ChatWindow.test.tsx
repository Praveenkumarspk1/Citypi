import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { ChatWindow } from './ChatWindow'
import { useConversationMessages, useSendMessage, useCreateConversation } from '@shared/hooks/useApi'
import { queryKeys } from '@shared/utils/api'

// Mock dependencies
vi.mock('@shared/hooks/useApi')
vi.mock('@shared/utils/api', () => ({
  queryKeys: {
    conversations: {
      messages: vi.fn((id, params) => ['conversations', 'messages', id, params]),
    },
  },
}))

const mockUseConversationMessages = vi.mocked(useConversationMessages)
const mockUseSendMessage = vi.mocked(useSendMessage)
const mockUseCreateConversation = vi.mocked(useCreateConversation)

describe('ChatWindow', () => {
  const mockMessages = [
    { id: '1', role: 'user', content: 'Hello', type: 'text', created_at: new Date().toISOString() },
    { id: '2', role: 'assistant', content: 'Hi there!', type: 'text', created_at: new Date().toISOString() },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseConversationMessages.mockReturnValue({
      data: { items: mockMessages, total: 2, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any)
    mockUseSendMessage.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(undefined),
      isPending: false,
    } as any)
    mockUseCreateConversation.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({ id: 'new-conv-id' }),
      isPending: false,
    } as any)
  })

  it('renders empty state when no conversationId and no onNewConversation', () => {
    render(<ChatWindow />)
    
    expect(screen.getByText(/start a conversation/i)).toBeInTheDocument()
    expect(screen.getByText(/ask me anything about your trip/i)).toBeInTheDocument()
  })

  it('renders messages when conversationId is provided', () => {
    render(<ChatWindow conversationId="conv-1" />)
    
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })

  it('shows loading state when loading messages', () => {
    mockUseConversationMessages.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0, has_next: false, has_prev: false },
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    } as any)
    
    render(<ChatWindow conversationId="conv-1" />)
    
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows error message when loading fails', () => {
    mockUseConversationMessages.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Failed to load'),
      refetch: vi.fn(),
    } as any)
    
    render(<ChatWindow conversationId="conv-1" />)
    
    expect(screen.getByText(/failed to load messages/i)).toBeInTheDocument()
  })

  it('sends message in existing conversation', async () => {
    const mockSendMessage = vi.fn().mockResolvedValue(undefined)
    mockUseSendMessage.mockReturnValue({
      mutateAsync: mockSendMessage,
      isPending: false,
    } as any)
    
    render(<ChatWindow conversationId="conv-1" />)
    
    fireEvent.change(screen.getByPlaceholderText(/type a message/i), { target: { value: 'Test message' } })
    fireEvent.click(screen.getByRole('button', { name: /send message/i }))
    
    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith({
        conversationId: 'conv-1',
        data: { content: 'Test message', attachments: [] },
      })
    })
  })

  it('creates new conversation when no conversationId', async () => {
    const mockCreateConversation = vi.fn().mockResolvedValue({ id: 'new-conv-id' })
    const mockSendMessage = vi.fn().mockResolvedValue(undefined)
    const onNewConversation = vi.fn()
    
    mockUseCreateConversation.mockReturnValue({
      mutateAsync: mockCreateConversation,
      isPending: false,
    } as any)
    mockUseSendMessage.mockReturnValue({
      mutateAsync: mockSendMessage,
      isPending: false,
    } as any)
    
    render(<ChatWindow onNewConversation={onNewConversation} />)
    
    fireEvent.change(screen.getByPlaceholderText(/start a new conversation/i), { target: { value: 'First message' } })
    fireEvent.click(screen.getByRole('button', { name: /send message/i }))
    
    await waitFor(() => {
      expect(mockCreateConversation).toHaveBeenCalledWith({
        initial_message: 'First message',
        context: {},
      })
    })
    
    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith({
        conversationId: 'new-conv-id',
        data: { content: 'First message', attachments: [] },
      })
    })
    
    await waitFor(() => {
      expect(onNewConversation).toHaveBeenCalledWith({ id: 'new-conv-id' })
    })
  })

  it('handles file attachments', async () => {
    const mockSendMessage = vi.fn().mockResolvedValue(undefined)
    mockUseSendMessage.mockReturnValue({
      mutateAsync: mockSendMessage,
      isPending: false,
    } as any)
    
    render(<ChatWindow conversationId="conv-1" />)
    
    // Create a file input and simulate file selection
    const fileInput = screen.getByLabelText(/attach files/i)
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    
    fireEvent.change(fileInput, { target: { files: [file] } })
    
    expect(screen.getByText('test.txt')).toBeInTheDocument()
    
    fireEvent.click(screen.getByRole('button', { name: /send message/i }))
    
    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith({
        conversationId: 'conv-1',
        data: { content: '', attachments: [file] },
      })
    })
  })

  it('removes attachment when clicking remove button', () => {
    render(<ChatWindow conversationId="conv-1" />)
    
    const fileInput = screen.getByLabelText(/attach files/i)
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    
    fireEvent.change(fileInput, { target: { files: [file] } })
    expect(screen.getByText('test.txt')).toBeInTheDocument()
    
    fireEvent.click(screen.getByRole('button', { name: /remove attachment/i }))
    expect(screen.queryByText('test.txt')).not.toBeInTheDocument()
  })

  it('disables send button when no message and no attachments', () => {
    render(<ChatWindow conversationId="conv-1" />)
    
    const sendButton = screen.getByRole('button', { name: /send message/i })
    expect(sendButton).toBeDisabled()
  })

  it('enables send button when message is entered', () => {
    render(<ChatWindow conversationId="conv-1" />)
    
    fireEvent.change(screen.getByPlaceholderText(/type a message/i), { target: { value: 'Test' } })
    
    const sendButton = screen.getByRole('button', { name: /send message/i })
    expect(sendButton).not.toBeDisabled()
  })

  it('shows streaming indicator when sending message', async () => {
    let resolveSend: (value: any) => void
    const sendPromise = new Promise((resolve) => { resolveSend = resolve })
    
    mockUseSendMessage.mockReturnValue({
      mutateAsync: vi.fn().mockReturnValue(sendPromise),
      isPending: true,
    } as any)
    
    render(<ChatWindow conversationId="conv-1" />)
    
    fireEvent.change(screen.getByPlaceholderText(/type a message/i), { target: { value: 'Test' } })
    fireEvent.click(screen.getByRole('button', { name: /send message/i }))
    
    expect(screen.getByText(/thinking.../i)).toBeInTheDocument()
    
    resolveSend!(undefined)
    await sendPromise
  })

  it('sends message on Enter key', async () => {
    const mockSendMessage = vi.fn().mockResolvedValue(undefined)
    mockUseSendMessage.mockReturnValue({
      mutateAsync: mockSendMessage,
      isPending: false,
    } as any)
    
    render(<ChatWindow conversationId="conv-1" />)
    
    const textarea = screen.getByPlaceholderText(/type a message/i)
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    
    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalled()
    })
  })

  it('does not send message on Shift+Enter', async () => {
    const mockSendMessage = vi.fn().mockResolvedValue(undefined)
    mockUseSendMessage.mockReturnValue({
      mutateAsync: mockSendMessage,
      isPending: false,
    } as any)
    
    render(<ChatWindow conversationId="conv-1" />)
    
    const textarea = screen.getByPlaceholderText(/type a message/i)
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })
    
    await waitFor(() => {
      expect(mockSendMessage).not.toHaveBeenCalled()
    })
  })
})