// Global augmentation for Cypress custom commands
declare namespace Cypress {
  interface Chainable<Subject = any> {
    login(email: string, password: string): Chainable<Element>;
    createItineraryWithPois(pois: string[]): Chainable<Element>;
    drag(selector: string, options?: any): Chainable<Element>;
  }
}
export {};
