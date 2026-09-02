import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ResetPasswordPage } from './ResetPasswordPage'
import { useResetPassword } from '@shared/hooks/useApi'
import { useNavigate, useSearchParams } from 'react-router-dom'

// Mock dependencies
vi.mock('@shared/hooks/useApi')
vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(),
  useSearchParams: vi.fn(),
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}))

const mockUseResetPassword = vi.mocked(useResetPassword)
const mockUseNavigate = vi.mocked(useNavigate)
const mockUseSearchParams = vi.mocked(useSearchParams)

describe('ResetPasswordPage', () => {
  const mockMutateAsync = vi.fn()
  const mockNavigate = vi.fn()
const mockSearchParams = new URLSearchParams()
  const mockSetSearchParams = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseResetPassword.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    } as any)
    mockUseNavigate.mockReturnValue(mockNavigate)
    mockUseSearchParams.mockReturnValue([mockSearchParams, mockSetSearchParams])
    mockSearchParams.set('token', 'valid-reset-token')
  })

  it('renders reset password form when token is present', () => {
    render(<ResetPasswordPage />)
    
    expect(screen.getByRole('heading', { name: /reset password/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reset password/i })).toBeInTheDocument()
  })

  it('shows invalid token page when token is missing', () => {
    mockSearchParams.delete('token')
    
    render(<ResetPasswordPage />)
    
    expect(screen.getByRole('heading', { name: /invalid reset link/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /request new reset link/i })).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    render(<ResetPasswordPage />)
    
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for weak password', async () => {
    render(<ResetPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'weak' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'weak' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for password without uppercase, lowercase, and number', async () => {
    render(<ResetPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'password' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'password' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/password must contain uppercase, lowercase, and number/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for password mismatch', async () => {
    render(<ResetPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'Password456' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('calls reset password mutation on valid submit', async () => {
    mockMutateAsync.mockResolvedValue(undefined)
    
    render(<ResetPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'Password123' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        token: 'valid-reset-token',
        password: 'Password123',
      })
    })
  })

  it('shows success state after password reset', async () => {
    mockMutateAsync.mockResolvedValue(undefined)
    
    render(<ResetPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'Password123' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /password reset successful/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /sign in with new password/i })).toBeInTheDocument()
    })
  })

  it('shows error message on failure', async () => {
    mockMutateAsync.mockRejectedValue(new Error('Invalid or expired token'))
    
    render(<ResetPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'Password123' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/invalid or expired token/i)).toBeInTheDocument()
    })
  })

  it('shows loading state during request', async () => {
    let resolvePromise: (value: any) => void
    const promise = new Promise((resolve) => { resolvePromise = resolve })
    mockMutateAsync.mockReturnValue(promise)
    mockUseResetPassword.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
    } as any)
    
    render(<ResetPasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'Password123' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    
    expect(screen.getByRole('button', { name: /resetting.../i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /resetting.../i })).toBeDisabled()
    
    resolvePromise!(undefined)
    await promise
  })

  it('toggles password visibility', () => {
    render(<ResetPasswordPage />)
    
    const passwordInput = screen.getByLabelText(/new password/i)
    expect(passwordInput).toHaveAttribute('type', 'password')
    
    fireEvent.click(screen.getByRole('button', { name: /toggle password visibility/i }))
    expect(passwordInput).toHaveAttribute('type', 'text')
  })

  it('toggles confirm password visibility', () => {
    render(<ResetPasswordPage />)
    
    const confirmPasswordInput = screen.getByLabelText(/confirm new password/i)
    expect(confirmPasswordInput).toHaveAttribute('type', 'password')
    
    fireEvent.click(screen.getByRole('button', { name: /toggle confirm password visibility/i }))
    expect(confirmPasswordInput).toHaveAttribute('type', 'text')
  })

  it('renders link back to login page', () => {
    render(<ResetPasswordPage />)
    
    expect(screen.getByRole('link', { name: /back to sign in/i })).toHaveAttribute('href', '/login')
  })
})