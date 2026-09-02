/// <reference types="cypress" />
/// <reference path="../support/commands.d.ts" />

describe('Itinerary Builder', () => {
  beforeEach(() => {
    // Login first
    cy.login('test@example.com', 'password123')
    cy.visit('/itinerary')
    
    // Mock POI search for adding to itinerary
    cy.intercept('GET', '/api/v1/pois/search*', {
      statusCode: 200,
      body: {
        items: [
          {
            id: '1',
            name: 'Central Park',
            category: 'park',
            address: { street: '59th St', city: 'New York', state: 'NY', postal_code: '10022', country: 'USA' },
            coordinates: { latitude: 40.7829, longitude: -73.9654 },
            rating: { value: 4.8, count: 150000 },
            price_level: 0,
            tags: ['park', 'outdoor', 'free'],
          },
          {
            id: '2',
            name: 'The Metropolitan Museum of Art',
            category: 'museum',
            address: { street: '1000 5th Ave', city: 'New York', state: 'NY', postal_code: '10028', country: 'USA' },
            coordinates: { latitude: 40.7794, longitude: -73.9632 },
            rating: { value: 4.7, count: 50000 },
            price_level: 2,
            tags: ['art', 'museum', 'culture'],
          },
        ],
        total: 2,
        page: 1,
        page_size: 20,
      },
    }).as('searchPois')
    
    // Mock itinerary creation
    cy.intercept('POST', '/api/v1/itineraries', {
      statusCode: 201,
      body: {
        id: 'new-itinerary-id',
        name: 'My NYC Trip',
        description: 'A great trip to NYC',
        start_date: '2024-06-01',
        end_date: '2024-06-05',
        items: [],
        user_id: '1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    }).as('createItinerary')
  })

  it('should display itinerary builder page', () => {
    cy.get('[data-cy=itinerary-builder]').should('be.visible')
    cy.get('[data-cy=create-itinerary-button]').should('be.visible')
  })

  it('should create a new itinerary', () => {
    cy.get('[data-cy=create-itinerary-button]').click()
    
    cy.get('[data-cy=itinerary-name-input]').type('My NYC Trip')
    cy.get('[data-cy=itinerary-description-input]').type('A great trip to NYC')
    cy.get('[data-cy=start-date-input]').type('2024-06-01')
    cy.get('[data-cy=end-date-input]').type('2024-06-05')
    cy.get('[data-cy=save-itinerary-button]').click()
    
    cy.wait('@createItinerary')
    cy.get('[data-cy=itinerary-list]').should('contain', 'My NYC Trip')
  })

  it('should add POIs to itinerary', () => {
    // Create itinerary first
    cy.get('[data-cy=create-itinerary-button]').click()
    cy.get('[data-cy=itinerary-name-input]').type('Test Itinerary')
    cy.get('[data-cy=start-date-input]').type('2024-06-01')
    cy.get('[data-cy=end-date-input]').type('2024-06-05')
    cy.get('[data-cy=save-itinerary-button]').click()
    cy.wait('@createItinerary')
    
    // Click on the created itinerary
    cy.get('[data-cy=itinerary-item]').first().click()
    
    // Search for POIs
    cy.get('[data-cy=add-poi-button]').click()
    cy.get('[data-cy=poi-search-input]').type('park')
    cy.get('[data-cy=poi-search-button]').click()
    cy.wait('@searchPois')
    
    // Add first POI
    cy.get('[data-cy=add-poi-to-itinerary]').first().click()
    
    // Verify POI added
    cy.get('[data-cy=itinerary-poi-list]').should('contain', 'Central Park')
  })

  it('should reorder itinerary items', () => {
    // Setup: create itinerary with multiple POIs
    cy.createItineraryWithPois(['Central Park', 'Metropolitan Museum'])
    
    // Drag and drop to reorder
    cy.get('[data-cy=itinerary-poi-item]').first().drag('[data-cy=itinerary-poi-item]').last()
    
    // Verify order changed
    cy.get('[data-cy=itinerary-poi-item]').first().should('contain', 'Metropolitan Museum')
  })

  it('should remove POI from itinerary', () => {
    cy.createItineraryWithPois(['Central Park'])
    
    cy.get('[data-cy=remove-poi-button]').click()
    
    cy.get('[data-cy=itinerary-poi-list]').should('not.contain', 'Central Park')
  })

  it('should save itinerary changes', () => {
    cy.intercept('PUT', '/api/v1/itineraries/*', {
      statusCode: 200,
      body: { success: true },
    }).as('updateItinerary')
    
    cy.createItineraryWithPois(['Central Park'])
    
    cy.get('[data-cy=save-itinerary-button]').click()
    
    cy.wait('@updateItinerary')
    cy.get('[data-cy=success-toast]').should('contain', 'Saved')
  })

  it('should show itinerary on map', () => {
    cy.createItineraryWithPois(['Central Park', 'Metropolitan Museum'])
    
    cy.get('[data-cy=view-on-map-button]').click()
    
    cy.get('[data-cy=map-container]').should('be.visible')
    cy.get('[data-cy=map-route]').should('be.visible')
    cy.get('[data-cy=map-marker]').should('have.length', 2)
  })

  it('should export itinerary', () => {
    cy.intercept('GET', '/api/v1/itineraries/*/export*', {
      statusCode: 200,
      body: 'data:text/calendar;base64,...',
    }).as('exportItinerary')
    
    cy.createItineraryWithPois(['Central Park'])
    
    cy.get('[data-cy=export-button]').click()
    cy.get('[data-cy=export-ical]').click()
    
    cy.wait('@exportItinerary')
  })

  it('should share itinerary', () => {
    cy.intercept('POST', '/api/v1/itineraries/*/share', {
      statusCode: 200,
      body: { share_url: 'https://app.example.com/shared/abc123' },
    }).as('shareItinerary')
    
    cy.createItineraryWithPois(['Central Park'])
    
    cy.get('[data-cy=share-button]').click()
    cy.get('[data-cy=share-link-input]').should('have.value', 'https://app.example.com/shared/abc123')
    cy.get('[data-cy=copy-link-button]').click()
    
    cy.wait('@shareItinerary')
  })
})

describe('Itinerary List', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123')
    cy.visit('/itinerary')
  })

  it('should display list of itineraries', () => {
    cy.intercept('GET', '/api/v1/itineraries*', {
      statusCode: 200,
      body: {
        items: [
          {
            id: '1',
            name: 'NYC Trip',
            description: 'Summer vacation',
            start_date: '2024-06-01',
            end_date: '2024-06-05',
            items_count: 5,
            created_at: '2024-05-01T10:00:00Z',
          },
          {
            id: '2',
            name: 'Paris Trip',
            description: 'Spring getaway',
            start_date: '2024-04-15',
            end_date: '2024-04-20',
            items_count: 8,
            created_at: '2024-03-01T10:00:00Z',
          },
        ],
        total: 2,
        page: 1,
        page_size: 20,
      },
    }).as('getItineraries')
    
    cy.wait('@getItineraries')
    
    cy.get('[data-cy=itinerary-list-item]').should('have.length', 2)
    cy.get('[data-cy=itinerary-list-item]').first().should('contain', 'NYC Trip')
    cy.get('[data-cy=itinerary-list-item]').last().should('contain', 'Paris Trip')
  })

  it('should filter itineraries by date', () => {
    cy.get('[data-cy=date-filter]').select('upcoming')
    
    cy.intercept('GET', '/api/v1/itineraries*', {
      statusCode: 200,
      body: { items: [], total: 0, page: 1, page_size: 20 },
    }).as('filteredItineraries')
    
    cy.wait('@filteredItineraries').its('request.url').should('include', 'filter=upcoming')
  })

  it('should delete itinerary', () => {
    cy.intercept('DELETE', '/api/v1/itineraries/*', {
      statusCode: 204,
    }).as('deleteItinerary')
    
    cy.get('[data-cy=itinerary-list-item]').first().within(() => {
      cy.get('[data-cy=delete-itinerary-button]').click()
    })
    
    cy.get('[data-cy=confirm-delete-button]').click()
    
    cy.wait('@deleteItinerary')
    cy.get('[data-cy=itinerary-list-item]').should('have.length', 1)
  })
})