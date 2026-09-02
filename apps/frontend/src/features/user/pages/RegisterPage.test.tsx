import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { RegisterPage } from './RegisterPage'
import { useRegister } from '@shared/hooks/useApi'
import { useAuthStore } from '@shared/stores/authStore'
import { useNavigate } from 'react-router-dom'

// Mock dependencies
vi.mock('@shared/hooks/useApi')
vi.mock('@shared/stores/authStore')
vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(),
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}))

const mockUseRegister = vi.mocked(useRegister)
const mockUseAuthStore = vi.mocked(useAuthStore)
const mockUseNavigate = vi.mocked(useNavigate)

describe('RegisterPage', () => {
  const mockMutateAsync = vi.fn()
  const mockNavigate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseRegister.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    } as any)
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    } as any)
    mockUseNavigate.mockReturnValue(mockNavigate)
  })

  it('renders registration form', () => {
    render(<RegisterPage />)
    
    expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/display name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    render(<RegisterPage />)
    
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/display name is required/i)).toBeInTheDocument()
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
      expect(screen.getByText(/please confirm your password/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for invalid email', async () => {
    render(<RegisterPage />)
    
    fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: 'Test User' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'invalid-email' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'Password123' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for weak password', async () => {
    render(<RegisterPage />)
    
    fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: 'Test User' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'weak' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'weak' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for password mismatch', async () => {
    render(<RegisterPage />)
    
    fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: 'Test User' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'Password456' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('calls register mutation on valid submit', async () => {
    const mockUser = { id: '1', email: 'test@test.com', display_name: 'Test User' }
    const mockTokens = { access_token: 'abc123', refresh_token: 'def456', token_type: 'bearer', expires_in: 3600 }
    mockMutateAsync.mockResolvedValue({ user: mockUser, tokens: mockTokens })
    
    render(<RegisterPage />)
    
    fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: 'Test User' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'Password123' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        email: 'test@test.com',
        password: 'Password123',
        display_name: 'Test User',
      })
    })
  })

  it('navigates to home on successful registration', async () => {
    const mockUser = { id: '1', email: 'test@test.com', display_name: 'Test User' }
    const mockTokens = { access_token: 'abc123', refresh_token: 'def456', token_type: 'bearer', expires_in: 3600 }
    mockMutateAsync.mockResolvedValue({ user: mockUser, tokens: mockTokens })
    
    render(<RegisterPage />)
    
    fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: 'Test User' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'Password123' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true })
    })
  })

  it('shows error message on registration failure', async () => {
    mockMutateAsync.mockRejectedValue(new Error('Email already exists'))
    
    render(<RegisterPage />)
    
    fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: 'Test User' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'Password123' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/email already exists/i)).toBeInTheDocument()
    })
  })

  it('toggles password visibility', () => {
    render(<RegisterPage />)
    
    const passwordInput = screen.getByLabelText(/password/i)
    expect(passwordInput).toHaveAttribute('type', 'password')
    
    fireEvent.click(screen.getByRole('button', { name: /toggle password visibility/i }))
    expect(passwordInput).toHaveAttribute('type', 'text')
  })

  it('toggles confirm password visibility', () => {
    render(<RegisterPage />)
    
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    expect(confirmPasswordInput).toHaveAttribute('type', 'password')
    
    fireEvent.click(screen.getByRole('button', { name: /toggle confirm password visibility/i }))
    expect(confirmPasswordInput).toHaveAttribute('type', 'text')
  })

  it('shows loading state during registration', async () => {
    let resolvePromise: (value: any) => void
    const promise = new Promise((resolve) => { resolvePromise = resolve })
    mockMutateAsync.mockReturnValue(promise)
    mockUseRegister.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
    } as any)
    
    render(<RegisterPage />)
    
    fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: 'Test User' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'Password123' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))
    
    expect(screen.getByRole('button', { name: /creating.../i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /creating.../i })).toBeDisabled()
    
    resolvePromise!({ user: { id: '1' }, tokens: { access_token: 'abc', refresh_token: 'def', token_type: 'bearer', expires_in: 3600 } })
    await promise
  })

  it('renders link to login page', () => {
    render(<RegisterPage />)
    
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login')
  })
})