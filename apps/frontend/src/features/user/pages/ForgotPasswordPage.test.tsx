import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ForgotPasswordPage } from './ForgotPasswordPage'
import { useForgotPassword } from '@shared/hooks/useApi'
import { useNavigate } from 'react-router-dom'

// Mock dependencies
vi.mock('@shared/hooks/useApi')
vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(),
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}))

const mockUseForgotPassword = vi.mocked(useForgotPassword)
const mockUseNavigate = vi.mocked(useNavigate)

describe('ForgotPasswordPage', () => {
  const mockMutateAsync = vi.fn()
  const mockNavigate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseForgotPassword.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    } as any)
    mockUseNavigate.mockReturnValue(mockNavigate)
  })

  it('renders forgot password form', () => {
    render(<ForgotPasswordPage />)
    
    expect(screen.getByRole('heading', { name: /forgot password/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument()
  })

  it('shows validation error for empty email', async () => {
    render(<ForgotPasswordPage />)
    
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for invalid email', async () => {
    render(<ForgotPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'invalid-email' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
    })
  })

  it('calls forgot password mutation on valid submit', async () => {
    mockMutateAsync.mockResolvedValue(undefined)
    
    render(<ForgotPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith('test@test.com')
    })
  })

  it('shows success state after sending reset link', async () => {
    mockMutateAsync.mockResolvedValue(undefined)
    
    render(<ForgotPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /check your email/i })).toBeInTheDocument()
      expect(screen.getByText(/we've sent a password reset link to test@test.com/i)).toBeInTheDocument()
    })
  })

  it('shows error message on failure', async () => {
    mockMutateAsync.mockRejectedValue(new Error('User not found'))
    
    render(<ForgotPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/user not found/i)).toBeInTheDocument()
    })
  })

  it('shows loading state during request', async () => {
    let resolvePromise: (value: any) => void
    const promise = new Promise((resolve) => { resolvePromise = resolve })
    mockMutateAsync.mockReturnValue(promise)
    mockUseForgotPassword.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
    } as any)
    
    render(<ForgotPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    
    expect(screen.getByRole('button', { name: /sending.../i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sending.../i })).toBeDisabled()
    
    resolvePromise!(undefined)
    await promise
  })

  it('renders link back to login page', () => {
    render(<ForgotPasswordPage />)
    
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login')
  })

  it('allows resending email from success state', async () => {
    mockMutateAsync.mockResolvedValue(undefined)
    
    render(<ForgotPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /check your email/i })).toBeInTheDocument()
    })
    
    fireEvent.click(screen.getByRole('button', { name: /resend/i }))
    
    // Should go back to form state
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /forgot password/i })).toBeInTheDocument()
    })
  })
})