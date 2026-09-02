import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { VerifyEmailPage } from './VerifyEmailPage'
import { useVerifyEmail } from '@shared/hooks/useApi'
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

const mockUseVerifyEmail = vi.mocked(useVerifyEmail)
const mockUseNavigate = vi.mocked(useNavigate)
const mockUseSearchParams = vi.mocked(useSearchParams)

describe('VerifyEmailPage', () => {
  const mockMutateAsync = vi.fn()
  const mockNavigate = vi.fn()
  const mockSearchParams = new URLSearchParams()
  const mockSetSearchParams = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseVerifyEmail.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    } as any)
    mockUseNavigate.mockReturnValue(mockNavigate)
    mockUseSearchParams.mockReturnValue([mockSearchParams, mockSetSearchParams])
    mockSearchParams.set('token', 'valid-verification-token')
  })

  it('shows verifying state initially', () => {
    render(<VerifyEmailPage />)
    
    expect(screen.getByRole('heading', { name: /verifying your email/i })).toBeInTheDocument()
    expect(screen.getByText(/please wait while we verify your email address/i)).toBeInTheDocument()
  })

  it('shows success state when verification succeeds', async () => {
    mockMutateAsync.mockResolvedValue(undefined)
    
    render(<VerifyEmailPage />)
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /email verified/i })).toBeInTheDocument()
      expect(screen.getByText(/your email address has been successfully verified/i)).toBeInTheDocument()
    })
  })

  it('shows error state when verification fails', async () => {
    mockMutateAsync.mockRejectedValue(new Error('Invalid or expired token'))
    
    render(<VerifyEmailPage />)
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /verification failed/i })).toBeInTheDocument()
      expect(screen.getByText(/invalid or expired token/i)).toBeInTheDocument()
    })
  })

  it('shows missing token page when token is not present', () => {
    mockSearchParams.delete('token')
    
    render(<VerifyEmailPage />)
    
    expect(screen.getByRole('heading', { name: /invalid verification link/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /request new verification link/i })).toBeInTheDocument()
  })

  it('allows resending verification email from error state', async () => {
    mockMutateAsync.mockRejectedValue(new Error('Invalid or expired token'))
    
    render(<VerifyEmailPage />)
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /verification failed/i })).toBeInTheDocument()
    })
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.click(screen.getByRole('button', { name: /resend verification email/i }))
    
    // Alert is shown (mocked)
    expect(window.alert).toHaveBeenCalledWith('Verification email resent to test@test.com')
  })

  it('allows resending verification email from missing token state', () => {
    mockSearchParams.delete('token')
    
    render(<VerifyEmailPage />)
    
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.click(screen.getByRole('button', { name: /resend verification email/i }))
    
    expect(window.alert).toHaveBeenCalledWith('Verification email resent to test@test.com')
  })

  it('renders link back to login page from success state', async () => {
    mockMutateAsync.mockResolvedValue(undefined)
    
    render(<VerifyEmailPage />)
    
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /sign in to your account/i })).toHaveAttribute('href', '/login')
    })
  })

  it('renders link back to login page from error state', async () => {
    mockMutateAsync.mockRejectedValue(new Error('Invalid or expired token'))
    
    render(<VerifyEmailPage />)
    
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /back to sign in/i })).toHaveAttribute('href', '/login')
    })
  })

  it('renders link back to login page from missing token state', () => {
    mockSearchParams.delete('token')
    
    render(<VerifyEmailPage />)
    
    expect(screen.getByRole('link', { name: /back to sign in/i })).toHaveAttribute('href', '/login')
  })
})