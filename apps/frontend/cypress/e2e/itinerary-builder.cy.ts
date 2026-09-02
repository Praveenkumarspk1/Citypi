/// <reference types="cypress" />

describe('Itinerary Builder E2E Tests', () => {
  beforeEach(() => {
    // Login before each test
    cy.login('test@example.com', 'password123')
    cy.visit('/itinerary')
  })

  it('should display itinerary builder page', () => {
    cy.contains('h1', 'Itinerary Builder').should('be.visible')
    cy.contains('Create New Itinerary').should('be.visible')
  })

  it('should create a new itinerary', () => {
    cy.contains('Create New Itinerary').click()
    
    // Fill in itinerary details
    cy.get('[data-testid="itinerary-title"]').type('Paris Trip')
    cy.get('[data-testid="itinerary-description"]').type('3 days in Paris')
    cy.get('[data-testid="start-date"]').type('2024-06-15')
    cy.get('[data-testid="end-date"]').type('2024-06-17')
    cy.get('[data-testid="timezone"]').select('Europe/Paris')
    
    cy.contains('Create').click()
    
    // Verify itinerary was created
    cy.contains('Paris Trip').should('be.visible')
    cy.contains('3 days in Paris').should('be.visible')
  })

  it('should add a day to itinerary', () => {
    // Assuming we have an existing itinerary
    cy.contains('Paris Trip').click()
    
    cy.contains('Add Day').click()
    cy.get('[data-testid="day-title"]').type('Day 1 - Arrival')
    cy.get('[data-testid="day-date"]').type('2024-06-15')
    cy.get('[data-testid="day-notes"]').type('Arrive in Paris, check into hotel')
    
    cy.contains('Add Day').click()
    
    cy.contains('Day 1 - Arrival').should('be.visible')
    cy.contains('Arrive in Paris').should('be.visible')
  })

  it('should add an item to a day', () => {
    cy.contains('Paris Trip').click()
    cy.contains('Day 1 - Arrival').click()
    
    cy.contains('Add Item').click()
    cy.get('[data-testid="item-type"]').select('poi')
    cy.get('[data-testid="item-title"]').type('Eiffel Tower')
    cy.get('[data-testid="item-description"]').type('Visit the iconic Eiffel Tower')
    cy.get('[data-testid="start-time"]').type('10:00')
    cy.get('[data-testid="end-time"]').type('12:00')
    cy.get('[data-testid="duration"]').type('120')
    cy.get('[data-testid="address"]').type('Champ de Mars, 5 Avenue Anatole France, 75007 Paris')
    cy.get('[data-testid="estimated-cost"]').type('25')
    cy.get('[data-testid="currency"]').select('EUR')
    cy.get('[data-testid="transport-mode"]').select('walking')
    
    cy.contains('Add Item').click()
    
    cy.contains('Eiffel Tower').should('be.visible')
    cy.contains('10:00 - 12:00').should('be.visible')
  })

  it('should reorder items within a day', () => {
    cy.contains('Paris Trip').click()
    cy.contains('Day 1 - Arrival').click()
    
    // Add two items first
    cy.addItineraryItem('poi', 'Eiffel Tower', '10:00', '12:00')
    cy.addItineraryItem('restaurant', 'Lunch at Le Jules Verne', '12:30', '14:00')
    
    // Drag and drop to reorder
    cy.get('[data-testid="item-Eiffel Tower"]').drag('[data-testid="item-Lunch at Le Jules Verne"]')
    
    // Verify order changed
    cy.get('[data-testid="itinerary-items"]').children().first().should('contain', 'Lunch at Le Jules Verne')
  })

  it('should delete an item', () => {
    cy.contains('Paris Trip').click()
    cy.contains('Day 1 - Arrival').click()
    
    cy.addItineraryItem('poi', 'Eiffel Tower', '10:00', '12:00')
    
    cy.get('[data-testid="item-Eiffel Tower"]').find('[data-testid="delete-item"]').click()
    cy.contains('Confirm Delete').click()
    
    cy.contains('Eiffel Tower').should('not.exist')
  })

  it('should share itinerary', () => {
    cy.contains('Paris Trip').click()
    
    cy.contains('Share').click()
    cy.get('[data-testid="share-modal"]').should('be.visible')
    cy.contains('Copy Link').click()
    
    // Verify share token was generated
    cy.get('[data-testid="share-link"]').should('have.value', /share\/[a-zA-Z0-9]+/)
  })

  it('should publish itinerary', () => {
    cy.contains('Paris Trip').click()
    
    cy.contains('Publish').click()
    cy.contains('Confirm Publish').click()
    
    cy.contains('Published').should('be.visible')
    cy.contains('Draft').should('not.exist')
  })

  it('should calculate total duration and cost', () => {
    cy.contains('Paris Trip').click()
    cy.contains('Day 1 - Arrival').click()
    
    cy.addItineraryItem('poi', 'Eiffel Tower', '10:00', '12:00', '25', 'EUR')
    cy.addItineraryItem('restaurant', 'Lunch', '12:30', '14:00', '50', 'EUR')
    
    cy.contains('Total Duration: 210 min').should('be.visible')
    cy.contains('Total Cost: €75.00').should('be.visible')
  })

  it('should filter itineraries by status', () => {
    cy.visit('/itinerary')
    
    cy.get('[data-testid="status-filter"]').select('draft')
    cy.contains('Draft Trip').should('be.visible')
    cy.contains('Published Trip').should('not.exist')
    
    cy.get('[data-testid="status-filter"]').select('published')
    cy.contains('Published Trip').should('be.visible')
    cy.contains('Draft Trip').should('not.exist')
  })

  it('should search itineraries', () => {
    cy.visit('/itinerary')
    
    cy.get('[data-testid="search-input"]').type('Paris')
    cy.contains('Paris Trip').should('be.visible')
    cy.contains('Tokyo Trip').should('not.exist')
  })
})

// Custom commands for itinerary testing
Cypress.Commands.add('addItineraryItem', (type, title, startTime, endTime, cost = '0', currency = 'USD') => {
  cy.contains('Add Item').click()
  cy.get('[data-testid="item-type"]').select(type)
  cy.get('[data-testid="item-title"]').type(title)
  cy.get('[data-testid="start-time"]').type(startTime)
  cy.get('[data-testid="end-time"]').type(endTime)
  if (cost !== '0') {
    cy.get('[data-testid="estimated-cost"]').type(cost)
    cy.get('[data-testid="currency"]').select(currency)
  }
  cy.contains('Add Item').click()
})