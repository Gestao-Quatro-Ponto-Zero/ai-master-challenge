## ADDED Requirements

### Requirement: Win rate by seller
The system SHALL display a bar chart of win rates for each sales agent with at least 5 closed deals.

#### Scenario: Win rate chart
- **WHEN** user is on the Analytics tab
- **THEN** a bar chart SHALL show each seller's win rate sorted descending, with a horizontal line at the company average

### Requirement: Stage distribution
The system SHALL display the distribution of deals by stage (Prospecting, Engaging, Won, Lost) as a pie or donut chart.

#### Scenario: Stage distribution chart
- **WHEN** user opens the Analytics tab
- **THEN** a pie chart SHALL show the count of deals in each stage with percentages

### Requirement: Average time by stage
The system SHALL compute and display the average time deals spend in each stage.

#### Scenario: Stage duration table
- **WHEN** user views the Analytics tab
- **THEN** a table SHALL show the average, median, and max days spent in Prospecting and Engaging stages for closed deals

### Requirement: Pipeline value by region
The system SHALL display total pipeline value grouped by regional office.

#### Scenario: Regional pipeline value
- **WHEN** user views the Analytics tab
- **THEN** a bar chart SHALL show total close_value for open deals grouped by regional_office

### Requirement: Filters apply to analytics
The system SHALL apply sidebar filters to all analytics charts.

#### Scenario: Filtered analytics
- **WHEN** user selects a specific manager in the sidebar
- **THEN** all charts and tables in the Analytics tab SHALL reflect only that manager's team
