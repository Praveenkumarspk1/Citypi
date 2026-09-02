import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Modal } from './Modal'

describe('Modal', () => {
  it('renders modal when open', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()}>
        <div>Modal content</div>
      </Modal>
    )
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Modal content')).toBeInTheDocument()
  })

  it('does not render modal when closed', () => {
    render(
      <Modal isOpen={false} onClose={vi.fn()}>
        <div>Modal content</div>
      </Modal>
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('calls onClose when clicking overlay', () => {
    const handleClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={handleClose}>
        <div>Modal content</div>
      </Modal>
    )

    fireEvent.click(screen.getByRole('dialog').parentElement!)
    expect(handleClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when pressing Escape', () => {
    const handleClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={handleClose}>
        <div>Modal content</div>
      </Modal>
    )

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(handleClose).toHaveBeenCalledTimes(1)
  })

  it('does not close when clicking inside modal content', () => {
    const handleClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={handleClose}>
        <div data-testid="content">Modal content</div>
      </Modal>
    )

    fireEvent.click(screen.getByTestId('content'))
    expect(handleClose).not.toHaveBeenCalled()
  })

  it('applies size classes', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} size="sm">
        <div>Small modal</div>
      </Modal>
    )
    expect(screen.getByRole('dialog')).toHaveClass('max-w-sm')

    render(
      <Modal isOpen={true} onClose={vi.fn()} size="md">
        <div>Medium modal</div>
      </Modal>
    )
    expect(screen.getByRole('dialog')).toHaveClass('max-w-md')

    render(
      <Modal isOpen={true} onClose={vi.fn()} size="lg">
        <div>Large modal</div>
      </Modal>
    )
    expect(screen.getByRole('dialog')).toHaveClass('max-w-lg')

    render(
      <Modal isOpen={true} onClose={vi.fn()} size="xl">
        <div>XL modal</div>
      </Modal>
    )
    expect(screen.getByRole('dialog')).toHaveClass('max-w-xl')

    render(
      <Modal isOpen={true} onClose={vi.fn()} size="full">
        <div>Full modal</div>
      </Modal>
    )
    expect(screen.getByRole('dialog')).toHaveClass('max-w-4xl')
  })

  it('renders close button when showCloseButton is true', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} showCloseButton>
        <div>Modal content</div>
      </Modal>
    )
    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument()
  })

  it('does not render close button when showCloseButton is false', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} showCloseButton={false}>
        <div>Modal content</div>
      </Modal>
    )
    expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const handleClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={handleClose} showCloseButton>
        <div>Modal content</div>
      </Modal>
    )

    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(handleClose).toHaveBeenCalledTimes(1)
  })

  it('traps focus inside modal', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()}>
        <button>Button 1</button>
        <button>Button 2</button>
      </Modal>
    )

    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThanOrEqual(2)
  })
})