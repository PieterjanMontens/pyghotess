@fixture.api
Feature: Doc OCR

    Scenario: The server starts and I can retrieve some info
      Given the api is available
        When I access the server root
            Then I receive some data
