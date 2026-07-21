// JourneyGraph constraints — run before import
CREATE CONSTRAINT account_key IF NOT EXISTS FOR (n:Account) REQUIRE n.account_key IS UNIQUE;
CREATE CONSTRAINT journey_key IF NOT EXISTS FOR (n:Journey) REQUIRE n.journey_key IS UNIQUE;
CREATE CONSTRAINT event_instance_key IF NOT EXISTS FOR (n:EventInstance) REQUIRE n.event_instance_key IS UNIQUE;
CREATE CONSTRAINT pattern_key IF NOT EXISTS FOR (n:Pattern) REQUIRE n.pattern_key IS UNIQUE;
CREATE CONSTRAINT quality_profile_key IF NOT EXISTS FOR (n:QualityProfile) REQUIRE n.quality_profile_key IS UNIQUE;
CREATE CONSTRAINT finding_id IF NOT EXISTS FOR (n:Finding) REQUIRE n.finding_id IS UNIQUE;
