@fixture.api
Feature: Doc OCR

    Scenario: The server starts and I can retrieve some info
      Given the api is available
        When I access the server root
            Then I receive some data

    Scenario: I can connect and disconnect from the websocket
      Given a connection to the websocket
        When I send a simple test message
          Then I receive a response
        When I close the connection
          Then the connection is closed

    Scenario: I can OCR a file with the websocket
      Given a connection to the websocket
        When I send a test file
        And I wait for the results
          Then I receive all 7 pages
