## ADDED Requirements

### Requirement: Score breakdown per deal
The system SHALL display the contribution of each factor (stage, days in stage, account revenue, product price, seller win rate, sector win rate) to the total score.

#### Scenario: Expandable breakdown in Pipeline
- **WHEN** user clicks to expand a deal row in the Pipeline tab
- **THEN** a horizontal bar chart SHALL show each factor's contribution as a segment of the total score

### Requirement: Factor direction indication
The system SHALL indicate whether each factor contributed positively or negatively relative to the average.

#### Scenario: Below-average account
- **WHEN** a deal's account revenue is below the dataset median
- **THEN** the revenue contribution SHALL be marked as "negative" or "below average"

### Requirement: Deal Detail tab
The system SHALL provide a dedicated Deal Detail tab with a selector to pick any deal and see its full score breakdown.

#### Scenario: Select deal by account name
- **WHEN** user selects a deal from the dropdown in the Deal Detail tab
- **THEN** the system SHALL display the score, each factor's raw value, normalized value, weighted contribution, and a comment explaining the impact

#### Scenario: Radar or bar chart
- **WHEN** viewing a deal's breakdown
- **THEN** the system SHALL display a Plotly horizontal bar chart with each factor and its contribution score (0–100 sub-score)
