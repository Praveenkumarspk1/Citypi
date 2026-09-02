import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './Card'

describe('Card', () => {
  it('renders card with children', () => {
    render(
      <Card>
        <div>Card content</div>
      </Card>
    )
    expect(screen.getByText('Card content')).toBeInTheDocument()
  })

  it('applies variant classes', () => {
    render(<Card variant="default">Default</Card>)
    expect(screen.getByText('Default').parentElement).toHaveClass('bg-white', 'border', 'border-gray-200')
    
    render(<Card variant="elevated">Elevated</Card>)
    expect(screen.getByText('Elevated').parentElement).toHaveClass('shadow-lg', 'border-none')
    
    render(<Card variant="outlined">Outlined</Card>)
    expect(screen.getByText('Outlined').parentElement).toHaveClass('border-2', 'border-gray-300')
    
    render(<Card variant="filled">Filled</Card>)
    expect(screen.getByText('Filled').parentElement).toHaveClass('bg-gray-50', 'border-none')
  })

  it('applies padding classes', () => {
    render(<Card padding="none">No padding</Card>)
    expect(screen.getByText('No padding').parentElement).not.toHaveClass('p-4')
    
    render(<Card padding="sm">Small padding</Card>)
    expect(screen.getByText('Small padding').parentElement).toHaveClass('p-3')
    
    render(<Card padding="md">Medium padding</Card>)
    expect(screen.getByText('Medium padding').parentElement).toHaveClass('p-4')
    
    render(<Card padding="lg">Large padding</Card>)
    expect(screen.getByText('Large padding').parentElement).toHaveClass('p-6')
  })

  it('renders CardHeader with title and description', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
          <CardDescription>Card description</CardDescription>
        </CardHeader>
      </Card>
    )
    expect(screen.getByText('Card Title')).toBeInTheDocument()
    expect(screen.getByText('Card description')).toBeInTheDocument()
  })

  it('renders CardContent', () => {
    render(
      <Card>
        <CardContent>Content area</CardContent>
      </Card>
    )
    expect(screen.getByText('Content area')).toBeInTheDocument()
  })

  it('renders CardFooter', () => {
    render(
      <Card>
        <CardFooter>Footer area</CardFooter>
      </Card>
    )
    expect(screen.getByText('Footer area')).toBeInTheDocument()
  })

  it('applies hover effect when interactive', () => {
    render(<Card interactive>Interactive</Card>)
    expect(screen.getByText('Interactive').parentElement).toHaveClass('hover:shadow-md', 'cursor-pointer', 'transition-shadow')
  })

  it('applies custom className', () => {
    render(<Card className="custom-class">Custom</Card>)
    expect(screen.getByText('Custom').parentElement).toHaveClass('custom-class')
  })
})