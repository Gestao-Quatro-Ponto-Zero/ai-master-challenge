## ADDED Requirements

### Requirement: Score computation
The system SHALL compute a score from 0–100 for each open deal (Prospecting or Engaging stage) based on weighted features.

#### Scenario: Score computation for Engaging deal
- **WHEN** a deal is in Engaging stage with account revenue > $500M and product price > $1000
- **THEN** the score SHALL reflect contributions from stage weight, account revenue, product price, seller win rate, and sector win rate

#### Scenario: Lost deal score is 0
- **WHEN** a deal has stage "Lost"
- **THEN** its score SHALL be 0

#### Scenario: Won deal score is 100
- **WHEN** a deal has stage "Won"
- **THEN** its score SHALL be 100

#### Scenario: Days in stage penalty
- **WHEN** a deal has been in the same stage for more than 90 days
- **THEN** the score SHALL be penalized proportionally to the excess time

### Requirement: Configurable weights
The system SHALL allow scoring weights to be defined in a single configuration dictionary.

#### Scenario: Weight override
- **WHEN** the configuration dictionary is modified
- **THEN** the score computation SHALL use the new weights without code changes

### Requirement: Feature normalization
The system SHALL normalize continuous features (revenue, employees, price) to 0–1 scale before applying weights.

#### Scenario: Revenue normalization
- **WHEN** computing the account revenue contribution
- **THEN** the value SHALL be min-max normalized across all accounts in the dataset

### Requirement: Historical win rate computation
The system SHALL compute win rates per seller and per sector from historical (Won/Lost) deals.

#### Scenario: Seller win rate
- **WHEN** computing seller win rate for a sales agent
- **THEN** the rate SHALL be `Won deals / (Won + Lost deals)` for that agent

#### Scenario: Insufficient history fallback
- **WHEN** a seller has fewer than 5 closed deals
- **THEN** the system SHALL use the manager's average win rate as fallback
