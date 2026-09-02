/// <reference types="cypress" />
/// <reference path="../support/commands.d.ts" />

describe('Authentication', () => {
  beforeEach(() => {
    cy.visit('/login')
  })

  it('should display login form', () => {
    cy.get('[data-cy=email-input]').should('be.visible')
    cy.get('[data-cy=password-input]').should('be.visible')
    cy.get('[data-cy=login-button]').should('be.visible')
  })

  it('should show validation errors for empty fields', () => {
    cy.get('[data-cy=login-button]').click()
    cy.get('[data-cy=email-error]').should('contain', 'Email is required')
    cy.get('[data-cy=password-error]').should('contain', 'Password is required')
  })

  it('should show error for invalid email format', () => {
    cy.get('[data-cy=email-input]').type('invalid-email')
    cy.get('[data-cy=password-input]').type('password123')
    cy.get('[data-cy=login-button]').click()
    cy.get('[data-cy=email-error]').should('contain', 'Invalid email format')
  })

  it('should login successfully with valid credentials', () => {
    // Mock API response
    cy.intercept('POST', '/api/v1/auth/login', {
      statusCode: 200,
      body: {
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        user: {
          id: '1',
          email: 'test@example.com',
          username: 'testuser',
          first_name: 'Test',
          last_name: 'User',
        },
      },
    }).as('loginRequest')

    cy.get('[data-cy=email-input]').type('test@example.com')
    cy.get('[data-cy=password-input]').type('password123')
    cy.get('[data-cy=login-button]').click()

    cy.wait('@loginRequest')
    cy.url().should('include', '/')
    cy.get('[data-cy=user-menu]').should('be.visible')
  })

  it('should show error for invalid credentials', () => {
    cy.intercept('POST', '/api/v1/auth/login', {
      statusCode: 401,
      body: { detail: 'Invalid credentials' },
    }).as('loginRequest')

    cy.get('[data-cy=email-input]').type('wrong@example.com')
    cy.get('[data-cy=password-input]').type('wrongpassword')
    cy.get('[data-cy=login-button]').click()

    cy.wait('@loginRequest')
    cy.get('[data-cy=error-toast]').should('contain', 'Invalid credentials')
  })

  it('should navigate to register page', () => {
    cy.get('[data-cy=register-link]').click()
    cy.url().should('include', '/register')
  })

  it('should navigate to forgot password page', () => {
    cy.get('[data-cy=forgot-password-link]').click()
    cy.url().should('include', '/forgot-password')
  })
})

describe('Registration', () => {
  beforeEach(() => {
    cy.visit('/register')
  })

  it('should display registration form', () => {
    cy.get('[data-cy=email-input]').should('be.visible')
    cy.get('[data-cy=username-input]').should('be.visible')
    cy.get('[data-cy=password-input]').should('be.visible')
    cy.get('[data-cy=confirm-password-input]').should('be.visible')
    cy.get('[data-cy=register-button]').should('be.visible')
  })

  it('should show validation errors', () => {
    cy.get('[data-cy=register-button]').click()
    cy.get('[data-cy=email-error]').should('be.visible')
    cy.get('[data-cy=username-error]').should('be.visible')
    cy.get('[data-cy=password-error]').should('be.visible')
    cy.get('[data-cy=confirm-password-error]').should('be.visible')
  })

  it('should show error when passwords do not match', () => {
    cy.get('[data-cy=email-input]').type('test@example.com')
    cy.get('[data-cy=username-input]').type('testuser')
    cy.get('[data-cy=password-input]').type('password123')
    cy.get('[data-cy=confirm-password-input]').type('differentpassword')
    cy.get('[data-cy=register-button]').click()
    cy.get('[data-cy=confirm-password-error]').should('contain', 'Passwords do not match')
  })

  it('should register successfully', () => {
    cy.intercept('POST', '/api/v1/auth/register', {
      statusCode: 201,
      body: {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
      },
    }).as('registerRequest')

    cy.get('[data-cy=email-input]').type('test@example.com')
    cy.get('[data-cy=username-input]').type('testuser')
    cy.get('[data-cy=password-input]').type('password123')
    cy.get('[data-cy=confirm-password-input]').type('password123')
    cy.get('[data-cy=register-button]').click()

    cy.wait('@registerRequest')
    cy.url().should('include', '/')
  })
})

describe('Protected Routes', () => {
  it('should redirect to login when accessing protected route', () => {
    cy.visit('/profile')
    cy.url().should('include', '/login')
  })

  it('should allow access to protected route when authenticated', () => {
    // Login first
    cy.login('test@example.com', 'password123')
    
    cy.visit('/profile')
    cy.url().should('include', '/profile')
    cy.get('[data-cy=profile-page]').should('be.visible')
  })
})