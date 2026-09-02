/// <reference types="cypress" />

describe('POI Search', () => {
  beforeEach(() => {
    cy.visit('/')
    
    // Mock POI search API
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
          {
            id: '3',
            name: 'Joe\'s Pizza',
            category: 'restaurant',
            address: { street: '1435 Broadway', city: 'New York', state: 'NY', postal_code: '10018', country: 'USA' },
            coordinates: { latitude: 40.7589, longitude: -73.9851 },
            rating: { value: 4.5, count: 5000 },
            price_level: 1,
            tags: ['pizza', 'italian', 'cheap'],
          },
        ],
        total: 3,
        page: 1,
        page_size: 20,
      },
    }).as('searchRequest')
  })

  it('should display search input', () => {
    cy.get('[data-cy=search-input]').should('be.visible')
    cy.get('[data-cy=search-button]').should('be.visible')
  })

  it('should search for POIs', () => {
    cy.get('[data-cy=search-input]').type('pizza')
    cy.get('[data-cy=search-button]').click()
    
    cy.wait('@searchRequest')
    
    cy.get('[data-cy=poi-card]').should('have.length', 3)
    cy.get('[data-cy=poi-card]').first().should('contain', 'Central Park')
  })

  it('should filter by category', () => {
    cy.get('[data-cy=category-filter]').select('restaurant')
    cy.get('[data-cy=search-button]').click()
    
    cy.wait('@searchRequest')
    
    // Should filter results
    cy.get('[data-cy=poi-card]').each(($card) => {
      cy.wrap($card).should('contain', 'restaurant')
    })
  })

  it('should show POI details on click', () => {
    cy.get('[data-cy=search-button]').click()
    cy.wait('@searchRequest')
    
    cy.get('[data-cy=poi-card]').first().click()
    
    cy.url().should('include', '/pois/')
    cy.get('[data-cy=poi-detail]').should('be.visible')
    cy.get('[data-cy=poi-name]').should('contain', 'Central Park')
  })

  it('should show loading state during search', () => {
    cy.intercept('GET', '/api/v1/pois/search*', {
      delay: 1000,
      statusCode: 200,
      body: { items: [], total: 0, page: 1, page_size: 20 },
    }).as('slowSearch')
    
    cy.get('[data-cy=search-input]').type('coffee')
    cy.get('[data-cy=search-button]').click()
    
    cy.get('[data-cy=loading-spinner]').should('be.visible')
    cy.wait('@slowSearch')
    cy.get('[data-cy=loading-spinner]').should('not.exist')
  })

  it('should handle empty search results', () => {
    cy.intercept('GET', '/api/v1/pois/search*', {
      statusCode: 200,
      body: { items: [], total: 0, page: 1, page_size: 20 },
    }).as('emptySearch')
    
    cy.get('[data-cy=search-input]').type('nonexistentplace')
    cy.get('[data-cy=search-button]').click()
    
    cy.wait('@emptySearch')
    cy.get('[data-cy=empty-state]').should('be.visible')
    cy.get('[data-cy=empty-state]').should('contain', 'No results found')
  })

  it('should paginate results', () => {
    cy.intercept('GET', '/api/v1/pois/search*', {
      statusCode: 200,
      body: {
        items: Array.from({ length: 20 }, (_, i) => ({
          id: String(i + 1),
          name: `POI ${i + 1}`,
          category: 'restaurant',
          address: { street: `${i + 1} Main St`, city: 'New York', state: 'NY', postal_code: '10001', country: 'USA' },
          coordinates: { latitude: 40.7128, longitude: -74.0060 },
          rating: { value: 4.0, count: 100 },
          price_level: 1,
          tags: ['food'],
        })),
        total: 50,
        page: 1,
        page_size: 20,
      },
    }).as('paginatedSearch')
    
    cy.get('[data-cy=search-button]').click()
    cy.wait('@paginatedSearch')
    
    cy.get('[data-cy=pagination]').should('be.visible')
    cy.get('[data-cy=page-2]').click()
    
    cy.wait('@paginatedSearch').its('request.url').should('include', 'page=2')
  })
})

describe('Map Integration', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('should display map', () => {
    cy.get('[data-cy=map-container]').should('be.visible')
  })

  it('should show POI markers on map', () => {
    cy.get('[data-cy=search-button]').click()
    cy.wait('@searchRequest')
    
    cy.get('[data-cy=map-marker]').should('have.length', 3)
  })

  it('should center map on selected POI', () => {
    cy.get('[data-cy=search-button]').click()
    cy.wait('@searchRequest')
    
    cy.get('[data-cy=poi-card]').first().click()
    
    // Map should center on the POI
    cy.get('[data-cy=map-container]').should('have.attr', 'data-center', '40.7829,-73.9654')
  })
})