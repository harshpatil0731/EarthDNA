CREATE TABLE IF NOT EXISTS aoi_regions (
    region_id VARCHAR(32) PRIMARY KEY,
    study_region_name VARCHAR(128) NOT NULL,
    aoi_name VARCHAR(128) NOT NULL,
    risk_target VARCHAR(32) NOT NULL,
    geometry_version VARCHAR(16) NOT NULL,
    aoi_geometry JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dashboard_placeholders (
    region_id VARCHAR(32) PRIMARY KEY,
    phase_label VARCHAR(64) NOT NULL,
    risk_status VARCHAR(128) NOT NULL,
    health_status VARCHAR(128) NOT NULL,
    status_note VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_dashboard_placeholders_region
        FOREIGN KEY (region_id) REFERENCES aoi_regions(region_id)
        ON DELETE CASCADE
);

INSERT INTO aoi_regions (
    region_id, study_region_name, aoi_name, risk_target, geometry_version, aoi_geometry
) VALUES
    (
        'uttarakhand',
        'Uttarakhand, India',
        'Rajaji landscape',
        'wildfire',
        '1.0',
        JSON_OBJECT(
            'type', 'Polygon',
            'coordinates', JSON_ARRAY(JSON_ARRAY(
                JSON_ARRAY(77.9, 29.95), JSON_ARRAY(78.25, 29.95),
                JSON_ARRAY(78.25, 30.25), JSON_ARRAY(77.9, 30.25),
                JSON_ARRAY(77.9, 29.95)
            ))
        )
    ),
    (
        'california',
        'Southern California, USA',
        'San Bernardino Mountains',
        'wildfire',
        '1.0',
        JSON_OBJECT(
            'type', 'Polygon',
            'coordinates', JSON_ARRAY(JSON_ARRAY(
                JSON_ARRAY(-117.85, 34.1), JSON_ARRAY(-117.35, 34.1),
                JSON_ARRAY(-117.35, 34.45), JSON_ARRAY(-117.85, 34.45),
                JSON_ARRAY(-117.85, 34.1)
            ))
        )
    ),
    (
        'australia',
        'Southeastern Australia',
        'East Gippsland, Victoria',
        'wildfire',
        '1.0',
        JSON_OBJECT(
            'type', 'Polygon',
            'coordinates', JSON_ARRAY(JSON_ARRAY(
                JSON_ARRAY(147.0, -37.55), JSON_ARRAY(147.55, -37.55),
                JSON_ARRAY(147.55, -37.15), JSON_ARRAY(147.0, -37.15),
                JSON_ARRAY(147.0, -37.55)
            ))
        )
    )
ON DUPLICATE KEY UPDATE
    study_region_name = VALUES(study_region_name),
    aoi_name = VALUES(aoi_name),
    risk_target = VALUES(risk_target),
    geometry_version = VALUES(geometry_version),
    aoi_geometry = VALUES(aoi_geometry);

INSERT INTO dashboard_placeholders (
    region_id, phase_label, risk_status, health_status, status_note
) VALUES
    ('uttarakhand', 'Phase 1 placeholder', 'Risk model pending Phase 2', 'Not calculated', 'AOI configuration is connected; no operational prediction is shown.'),
    ('california', 'Phase 1 placeholder', 'Risk model pending Phase 2', 'Not calculated', 'AOI configuration is connected; no operational prediction is shown.'),
    ('australia', 'Phase 1 placeholder', 'Risk model pending Phase 2', 'Not calculated', 'AOI configuration is connected; no operational prediction is shown.')
ON DUPLICATE KEY UPDATE
    phase_label = VALUES(phase_label),
    risk_status = VALUES(risk_status),
    health_status = VALUES(health_status),
    status_note = VALUES(status_note);
