import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { LoginPage } from './LoginPage'
import { useLogin } from '@shared/hooks/useApi'
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

const mockUseLogin = vi.mocked(useLogin)
const mockUseAuthStore = vi.mocked(useAuthStore)
const mockUseNavigate = vi.mocked(useNavigate)

describe('LoginPage', () => {
  const mockMutateAsync = vi.fn()
  const mockNavigate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseLogin.mockReturnValue({
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

  it('renders login form', () => {
    render(<LoginPage />)
    
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    render(<LoginPage />)
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for invalid email', async () => {
    render(<LoginPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'invalid-email' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
    })
  })

  it('calls login mutation on valid submit', async () => {
    const mockUser = { id: '1', email: 'test@test.com', display_name: 'Test User' }
    const mockTokens = { access_token: 'abc123', refresh_token: 'def456', token_type: 'bearer', expires_in: 3600 }
    mockMutateAsync.mockResolvedValue({ user: mockUser, tokens: mockTokens })
    
    render(<LoginPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        email: 'test@test.com',
        password: 'password123',
        remember_me: false,
      })
    })
  })

  it('navigates to home on successful login', async () => {
    const mockUser = { id: '1', email: 'test@test.com', display_name: 'Test User' }
    const mockTokens = { access_token: 'abc123', refresh_token: 'def456', token_type: 'bearer', expires_in: 3600 }
    mockMutateAsync.mockResolvedValue({ user: mockUser, tokens: mockTokens })
    
    render(<LoginPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true })
    })
  })

  it('shows error message on login failure', async () => {
    mockMutateAsync.mockRejectedValue(new Error('Invalid credentials'))
    
    render(<LoginPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrongpassword' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('toggles password visibility', () => {
    render(<LoginPage />)
    
    const passwordInput = screen.getByLabelText(/password/i)
    expect(passwordInput).toHaveAttribute('type', 'password')
    
    fireEvent.click(screen.getByRole('button', { name: /toggle password visibility/i }))
    expect(passwordInput).toHaveAttribute('type', 'text')
    
    fireEvent.click(screen.getByRole('button', { name: /toggle password visibility/i }))
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('shows loading state during login', async () => {
    let resolvePromise: (value: any) => void
    const promise = new Promise((resolve) => { resolvePromise = resolve })
    mockMutateAsync.mockReturnValue(promise)
    mockUseLogin.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
    } as any)
    
    render(<LoginPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    
    expect(screen.getByRole('button', { name: /signing in.../i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /signing in.../i })).toBeDisabled()
    
    resolvePromise!({ user: { id: '1' }, tokens: { access_token: 'abc', refresh_token: 'def', token_type: 'bearer', expires_in: 3600 } })
    await promise
  })

  it('renders link to register page', () => {
    render(<LoginPage />)
    
    expect(screen.getByRole('link', { name: /sign up/i })).toHaveAttribute('href', '/register')
  })

  it('renders link to forgot password page', () => {
    render(<LoginPage />)
    
    expect(screen.getByRole('link', { name: /forgot password/i })).toHaveAttribute('href', '/forgot-password')
  })
})