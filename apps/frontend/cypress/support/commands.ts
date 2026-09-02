/// <reference types="cypress" />

declare global {
  namespace Cypress {
    interface Chainable<Subject = any> {
      login(email: string, password: string): Chainable<void>
      createItineraryWithPois(poiNames: string[]): Chainable<void>
      addItineraryItem(type: string, title: string, startTime: string, endTime: string, cost?: string, currency?: string): Chainable<void>
      drag(selector: string, options?: any): Chainable<Element>
    }
  }
}

Cypress.Commands.add('login', (email: string, password: string) => {
  cy.session([email, password], () => {
    cy.visit('/login')
    cy.get('[data-cy=email-input]').type(email)
    cy.get('[data-cy=password-input]').type(password)
    cy.get('[data-cy=login-button]').click()
    cy.url().should('include', '/')
    cy.get('[data-cy=user-menu]').should('be.visible')
  })
})

Cypress.Commands.add('createItineraryWithPois', (poiNames: string[]) => {
  // Create itinerary
  cy.get('[data-cy=create-itinerary-button]').click()
  cy.get('[data-cy=itinerary-name-input]').type('Test Itinerary')
  cy.get('[data-cy=start-date-input]').type('2024-06-01')
  cy.get('[data-cy=end-date-input]').type('2024-06-05')
  cy.get('[data-cy=save-itinerary-button]').click()
  
  // Wait for creation
  cy.intercept('POST', '/api/v1/itineraries').as('createItinerary')
  cy.wait('@createItinerary')
  
  // Click on the created itinerary
  cy.get('[data-cy=itinerary-item]').first().click()
  
  // Add each POI
  poiNames.forEach((poiName) => {
    cy.get('[data-cy=add-poi-button]').click()
    cy.get('[data-cy=poi-search-input]').type(poiName)
    cy.get('[data-cy=poi-search-button]').click()
    cy.wait('@searchPois')
    cy.get('[data-cy=add-poi-to-itinerary]').first().click()
  })
})

Cypress.Commands.add('addItineraryItem', (type: string, title: string, startTime: string, endTime: string, cost = '0', currency = 'USD') => {
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

export {}
