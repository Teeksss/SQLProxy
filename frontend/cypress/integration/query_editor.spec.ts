describe('Query Editor', () => {
  beforeEach(() => {
    cy.login('test_user', 'test_password');
    cy.visit('/query');
  });

  it('should execute a query successfully', () => {
    // Select database
    cy.get('[data-testid="database-selector"]')
      .click()
      .type('test_db{enter}');

    // Enter query
    cy.get('.ace_editor')
      .type('SELECT * FROM users LIMIT 5');

    // Execute query
    cy.get('[data-testid="execute-button"]')
      .click();

    // Check results
    cy.get('[data-testid="results-table"]')
      .should('be.visible')
      .find('tr')
      .should('have.length.gt', 1);
  });

  it('should show error for invalid query', () => {
    cy.get('[data-testid="database-selector"]')
      .click()
      .type('test_db{enter}');

    cy.get('.ace_editor')
      .type('SELECT * FROM non_existent_table');

    cy.get('[data-testid="execute-button"]')
      .click();

    cy.get('[data-testid="error-message"]')
      .should('be.visible')
      .and('contain', 'Table not found');
  });
});