/// <reference types="cypress" />

describe('Transit Planner', () => {
  beforeEach(() => {
    cy.visit('/transit')
    
    // Mock transit routes API
    cy.intercept('GET', '/api/v1/transit/routes*', {
      statusCode: 200,
      body: {
        routes: [
          {
            id: 'route-1',
            name: 'Subway Line 1',
            mode: 'subway',
            stops: [
              { id: 'stop-1', name: 'Times Square', coordinates: { latitude: 40.7580, longitude: -73.9855 }, sequence: 1 },
              { id: 'stop-2', name: 'Grand Central', coordinates: { latitude: 40.7527, longitude: -73.9772 }, sequence: 2 },
              { id: 'stop-3', name: 'Union Square', coordinates: { latitude: 40.7359, longitude: -73.9911 }, sequence: 3 },
            ],
            schedule: [
              { stop_id: 'stop-1', departure_time: '08:00' },
              { stop_id: 'stop-2', departure_time: '08:10' },
              { stop_id: 'stop-3', departure_time: '08:20' },
            ],
          },
          {
            id: 'route-2',
            name: 'Bus Route M42',
            mode: 'bus',
            stops: [
              { id: 'stop-4', name: 'Port Authority', coordinates: { latitude: 40.7570, longitude: -73.9900 }, sequence: 1 },
              { id: 'stop-5', name: 'Times Square', coordinates: { latitude: 40.7580, longitude: -73.9855 }, sequence: 2 },
            ],
            schedule: [
              { stop_id: 'stop-4', departure_time: '08:05' },
              { stop_id: 'stop-5', departure_time: '08:15' },
            ],
          },
        ],
      },
    }).as('getRoutes')
    
    // Mock route planning API
    cy.intercept('POST', '/api/v1/transit/plan', {
      statusCode: 200,
      body: {
        routes: [
          {
            id: 'plan-1',
            duration_minutes: 30,
            transfers: 1,
            steps: [
              { type: 'walk', from: 'Origin', to: 'Times Square', duration: 5 },
              { type: 'transit', route: 'Subway Line 1', from: 'Times Square', to: 'Union Square', duration: 20 },
              { type: 'walk', from: 'Union Square', to: 'Destination', duration: 5 },
            ],
            cost: 2.75,
          },
        ],
      },
    }).as('planRoute')
  })

  it('should display transit planner page', () => {
    cy.get('[data-cy=transit-planner]').should('be.visible')
    cy.get('[data-cy=origin-input]').should('be.visible')
    cy.get('[data-cy=destination-input]').should('be.visible')
    cy.get('[data-cy=plan-button]').should('be.visible')
  })

  it('should plan a route', () => {
    cy.get('[data-cy=origin-input]').type('Times Square')
    cy.get('[data-cy=destination-input]').type('Union Square')
    cy.get('[data-cy=plan-button]').click()
    
    cy.wait('@planRoute')
    
    cy.get('[data-cy=route-results]').should('be.visible')
    cy.get('[data-cy=route-option]').should('have.length', 1)
    cy.get('[data-cy=route-option]').first().should('contain', '30 min')
    cy.get('[data-cy=route-option]').first().should('contain', 'Subway Line 1')
  })

  it('should show route details on click', () => {
    cy.get('[data-cy=origin-input]').type('Times Square')
    cy.get('[data-cy=destination-input]').type('Union Square')
    cy.get('[data-cy=plan-button]').click()
    cy.wait('@planRoute')
    
    cy.get('[data-cy=route-option]').first().click()
    
    cy.get('[data-cy=route-detail]').should('be.visible')
    cy.get('[data-cy=route-steps]').should('contain', 'Walk')
    cy.get('[data-cy=route-steps]').should('contain', 'Subway Line 1')
  })

  it('should filter by transport mode', () => {
    cy.get('[data-cy=mode-filter]').select('subway')
    cy.get('[data-cy=plan-button]').click()
    cy.wait('@planRoute')
    
    // Should only show subway routes
    cy.get('[data-cy=route-option]').each(($option) => {
      cy.wrap($option).should('contain', 'subway')
    })
  })

  it('should show transit map', () => {
    cy.get('[data-cy=origin-input]').type('Times Square')
    cy.get('[data-cy=destination-input]').type('Union Square')
    cy.get('[data-cy=plan-button]').click()
    cy.wait('@planRoute')
    
    cy.get('[data-cy=view-map-button]').click()
    
    cy.get('[data-cy=transit-map]').should('be.visible')
    cy.get('[data-cy=map-route-line]').should('be.visible')
  })

  it('should save favorite route', () => {
    cy.login('test@example.com', 'password123')
    
    cy.intercept('POST', '/api/v1/transit/favorites', {
      statusCode: 201,
      body: { id: 'fav-1' },
    }).as('saveFavorite')
    
    cy.get('[data-cy=origin-input]').type('Home')
    cy.get('[data-cy=destination-input]').type('Work')
    cy.get('[data-cy=plan-button]').click()
    cy.wait('@planRoute')
    
    cy.get('[data-cy=save-favorite-button]').click()
    cy.get('[data-cy=favorite-name-input]').type('Commute')
    cy.get('[data-cy=confirm-save-favorite]').click()
    
    cy.wait('@saveFavorite')
    cy.get('[data-cy=success-toast]').should('contain', 'Saved')
  })
})

describe('Weather Display', () => {
  beforeEach(() => {
    cy.visit('/weather')
    
    // Mock weather API
    cy.intercept('GET', '/api/v1/weather/current*', {
      statusCode: 200,
      body: {
        location: 'New York, NY',
        temperature: 22,
        feels_like: 24,
        humidity: 65,
        wind_speed: 10,
        wind_direction: 'NW',
        condition: 'Partly Cloudy',
        icon: 'partly-cloudy',
        uv_index: 5,
        visibility: 10,
        pressure: 1013,
        sunrise: '06:30',
        sunset: '19:45',
      },
    }).as('getCurrentWeather')
    
    // Mock forecast API
    cy.intercept('GET', '/api/v1/weather/forecast*', {
      statusCode: 200,
      body: {
        daily: [
          { date: '2024-06-01', high: 25, low: 18, condition: 'Sunny', icon: 'sunny', precipitation_chance: 10 },
          { date: '2024-06-02', high: 23, low: 17, condition: 'Cloudy', icon: 'cloudy', precipitation_chance: 30 },
          { date: '2024-06-03', high: 21, low: 16, condition: 'Rainy', icon: 'rainy', precipitation_chance: 80 },
          { date: '2024-06-04', high: 24, low: 18, condition: 'Partly Cloudy', icon: 'partly-cloudy', precipitation_chance: 20 },
          { date: '2024-06-05', high: 26, low: 19, condition: 'Sunny', icon: 'sunny', precipitation_chance: 5 },
        ],
        hourly: [
          { time: '09:00', temperature: 20, condition: 'Sunny', icon: 'sunny' },
          { time: '12:00', temperature: 24, condition: 'Sunny', icon: 'sunny' },
          { time: '15:00', temperature: 25, condition: 'Partly Cloudy', icon: 'partly-cloudy' },
          { time: '18:00', temperature: 23, condition: 'Partly Cloudy', icon: 'partly-cloudy' },
          { time: '21:00', temperature: 20, condition: 'Clear', icon: 'clear' },
        ],
      },
    }).as('getForecast')
  })

  it('should display current weather', () => {
    cy.get('[data-cy=current-weather]').should('be.visible')
    cy.get('[data-cy=current-temperature]').should('contain', '22')
    cy.get('[data-cy=current-condition]').should('contain', 'Partly Cloudy')
    cy.get('[data-cy=current-location]').should('contain', 'New York')
  })

  it('should display weather details', () => {
    cy.get('[data-cy=feels-like]').should('contain', '24')
    cy.get('[data-cy=humidity]').should('contain', '65%')
    cy.get('[data-cy=wind]').should('contain', '10')
    cy.get('[data-cy=uv-index]').should('contain', '5')
    cy.get('[data-cy=visibility]').should('contain', '10')
    cy.get('[data-cy=pressure]').should('contain', '1013')
  })

  it('should display daily forecast', () => {
    cy.get('[data-cy=daily-forecast]').should('be.visible')
    cy.get('[data-cy=forecast-day]').should('have.length', 5)
    cy.get('[data-cy=forecast-day]').first().should('contain', '25')
    cy.get('[data-cy=forecast-day]').first().should('contain', '18')
  })

  it('should display hourly forecast', () => {
    cy.get('[data-cy=hourly-forecast]').should('be.visible')
    cy.get('[data-cy=forecast-hour]').should('have.length', 5)
    cy.get('[data-cy=forecast-hour]').first().should('contain', '09:00')
    cy.get('[data-cy=forecast-hour]').first().should('contain', '20')
  })

  it('should switch between Celsius and Fahrenheit', () => {
    cy.get('[data-cy=unit-toggle]').click()
    
    // Temperature should convert to Fahrenheit
    cy.get('[data-cy=current-temperature]').should('contain', '72') // 22°C = 71.6°F ≈ 72
  })

  it('should search for different location', () => {
    cy.intercept('GET', '/api/v1/weather/current*', {
      statusCode: 200,
      body: {
        location: 'London, UK',
        temperature: 15,
        feels_like: 14,
        humidity: 75,
        wind_speed: 15,
        wind_direction: 'SW',
        condition: 'Rainy',
        icon: 'rainy',
        uv_index: 2,
        visibility: 5,
        pressure: 1005,
        sunrise: '05:30',
        sunset: '20:30',
      },
    }).as('getLondonWeather')
    
    cy.get('[data-cy=location-search]').type('London')
    cy.get('[data-cy=location-search-button]').click()
    
    cy.wait('@getLondonWeather')
    
    cy.get('[data-cy=current-location]').should('contain', 'London')
    cy.get('[data-cy=current-temperature]').should('contain', '15')
    cy.get('[data-cy=current-condition]').should('contain', 'Rainy')
  })

  it('should show weather alerts if any', () => {
    cy.intercept('GET', '/api/v1/weather/alerts*', {
      statusCode: 200,
      body: {
        alerts: [
          {
            id: 'alert-1',
            title: 'Heavy Rain Warning',
            description: 'Heavy rainfall expected',
            severity: 'moderate',
            start_time: '2024-06-01T10:00:00Z',
            end_time: '2024-06-01T18:00:00Z',
          },
        ],
      },
    }).as('getAlerts')
    
    cy.visit('/weather?location=Seattle')
    cy.wait('@getAlerts')
    
    cy.get('[data-cy=weather-alerts]').should('be.visible')
    cy.get('[data-cy=alert-item]').should('contain', 'Heavy Rain Warning')
  })
})