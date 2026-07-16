## ADDED Requirements

### Requirement: Deal list sorted by score
The system SHALL display all open deals sorted descending by score, with highest-priority deals at the top.

#### Scenario: Default view
- **WHEN** the user opens the Pipeline tab
- **THEN** deals SHALL be listed sorted by score descending, showing account name, product, value, seller, stage, and score

### Requirement: Score visualization
Each deal SHALL display its score as a color-coded bar (green ≥70, yellow 40–69, red <40).

#### Scenario: Score color coding
- **WHEN** a deal has score 85
- **THEN** the score SHALL be displayed as a green bar proportional to 85/100

### Requirement: Sidebar filters
The system SHALL provide filters in the sidebar that apply across all tabs.

#### Scenario: Filter by seller
- **WHEN** user selects a seller from the dropdown
- **THEN** only deals assigned to that seller SHALL be shown

#### Scenario: Filter by manager
- **WHEN** user selects a manager from the dropdown
- **THEN** only deals from sellers under that manager SHALL be shown

#### Scenario: Filter by region
- **WHEN** user selects a region from the dropdown
- **THEN** only deals from that regional office SHALL be shown

#### Scenario: Filter by deal stage
- **WHEN** user selects one or more stages
- **THEN** only deals in selected stages SHALL be shown

#### Scenario: Score range slider
- **WHEN** user adjusts the minimum score slider to 50
- **THEN** deals with score below 50 SHALL be hidden

### Requirement: Top-level metrics
The system SHALL display aggregate metrics at the top of the Pipeline tab: total active deals, total pipeline value, average score.

#### Scenario: Metrics update on filter
- **WHEN** a filter is applied
- **THEN** the aggregate metrics SHALL update to reflect only the filtered deals
