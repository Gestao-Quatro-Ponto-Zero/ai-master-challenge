// JourneyGraph analytical indexes
CREATE INDEX event_type_name IF NOT EXISTS FOR (n:EventType) ON (n.event_type);
CREATE INDEX pattern_stability IF NOT EXISTS FOR (n:Pattern) ON (n.stability_status);
CREATE INDEX pattern_scope IF NOT EXISTS FOR (n:Pattern) ON (n.journey_scope);
CREATE INDEX journey_scope IF NOT EXISTS FOR (n:Journey) ON (n.journey_scope);
CREATE INDEX taxonomy_name IF NOT EXISTS FOR (n:Taxonomy) ON (n.name);
