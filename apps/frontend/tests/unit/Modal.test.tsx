import { test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Modal } from '@concierge/ui-components';

describe('Modal', () => {
  test('renders when open', () => {
    render(<Modal isOpen={true} onClose={() => {}} title="Test">Content</Modal>);
    expect(screen.getByText('Test')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  test('does not render when closed', () => {
    render(<Modal isOpen={false} onClose={() => {}} title="Test">Content</Modal>);
    expect(screen.queryByText('Test')).not.toBeInTheDocument();
  });
});
