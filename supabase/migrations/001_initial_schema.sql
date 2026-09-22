BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    ministry TEXT,
    department TEXT,
    sector TEXT,
    sub_sector TEXT,
    state TEXT,
    district TEXT,
    implementing_agency TEXT,
    location TEXT,
    project_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT projects_project_id_unique UNIQUE (project_id)
);

CREATE INDEX IF NOT EXISTS idx_projects_project_id ON projects(project_id);
CREATE INDEX IF NOT EXISTS idx_projects_ministry ON projects(ministry);
CREATE INDEX IF NOT EXISTS idx_projects_sector ON projects(sector);
CREATE INDEX IF NOT EXISTS idx_projects_state ON projects(state);

CREATE TABLE IF NOT EXISTS project_monthly_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    reporting_month TEXT NOT NULL,
    original_cost NUMERIC(18,2),
    revised_cost NUMERIC(18,2),
    expenditure NUMERIC(18,2),
    physical_progress NUMERIC(5,2),
    financial_progress NUMERIC(5,2),
    original_start_date DATE,
    original_completion_date DATE,
    revised_completion_date DATE,
    reported_status TEXT,
    data_source_id UUID,
    source_page INTEGER,
    extraction_confidence NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT project_monthly_status_unique UNIQUE (project_id, reporting_month)
);

CREATE INDEX IF NOT EXISTS idx_project_monthly_status_project ON project_monthly_status(project_id);
CREATE INDEX IF NOT EXISTS idx_project_monthly_status_month ON project_monthly_status(reporting_month);

CREATE TABLE IF NOT EXISTS project_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    reporting_month TEXT,
    issue_category TEXT,
    issue_description TEXT NOT NULL,
    severity TEXT,
    source_id UUID,
    source_page INTEGER,
    confidence NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_issues_project ON project_issues(project_id);

CREATE TABLE IF NOT EXISTS project_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    milestone_name TEXT NOT NULL,
    planned_date DATE,
    actual_date DATE,
    status TEXT,
    source_id UUID,
    source_page INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_milestones_project ON project_milestones(project_id);

CREATE TABLE IF NOT EXISTS project_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    final_cost NUMERIC(18,2),
    actual_completion_date DATE,
    cost_overrun_percent NUMERIC(8,2),
    time_overrun_months NUMERIC(8,2),
    cost_overrun_label TEXT,
    time_overrun_label TEXT,
    outcome_date DATE,
    source_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_outcomes_project ON project_outcomes(project_id);

CREATE TABLE IF NOT EXISTS risk_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    prediction_date DATE NOT NULL,
    prediction_horizon TEXT,
    cost_risk NUMERIC(5,2),
    schedule_risk NUMERIC(5,2),
    implementation_risk NUMERIC(5,2),
    overall_risk NUMERIC(5,2),
    confidence NUMERIC(5,2),
    model_version TEXT,
    feature_version TEXT,
    dataset_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_predictions_project ON risk_predictions(project_id);
CREATE INDEX IF NOT EXISTS idx_risk_predictions_date ON risk_predictions(prediction_date);

CREATE TABLE IF NOT EXISTS risk_drivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_prediction_id UUID NOT NULL REFERENCES risk_predictions(id) ON DELETE CASCADE,
    feature_name TEXT NOT NULL,
    feature_value TEXT,
    contribution NUMERIC(8,4),
    rank INTEGER,
    explanation_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_drivers_prediction ON risk_drivers(risk_prediction_id);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    evidence JSONB,
    confidence NUMERIC(5,2),
    status TEXT NOT NULL DEFAULT 'OPEN',
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_project ON alerts(project_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);

CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    recommendation_type TEXT,
    action TEXT NOT NULL,
    reason TEXT,
    evidence JSONB,
    expected_impact TEXT,
    confidence NUMERIC(5,2),
    priority TEXT,
    recommendation_version TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recommendations_project ON recommendations(project_id);

CREATE TABLE IF NOT EXISTS simulation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    baseline_snapshot JSONB,
    scenario_input JSONB,
    scenario_output JSONB,
    risk_delta NUMERIC(8,2),
    delay_delta NUMERIC(8,2),
    cost_delta NUMERIC(18,2),
    assumptions TEXT,
    confidence NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_simulation_runs_project ON simulation_runs(project_id);

CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,
    source_name TEXT,
    source_url TEXT,
    document_name TEXT,
    reporting_month TEXT,
    publication_date DATE,
    file_hash TEXT,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_sources_type ON data_sources(source_type);

CREATE TABLE IF NOT EXISTS data_quality (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    reporting_month TEXT,
    field_name TEXT NOT NULL,
    quality_status TEXT NOT NULL,
    quality_score NUMERIC(5,2),
    issue_code TEXT,
    issue_description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_quality_project ON data_quality(project_id);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    document_type TEXT,
    source_type TEXT,
    file_hash TEXT,
    reporting_month TEXT,
    page_count INTEGER,
    processing_status TEXT NOT NULL DEFAULT 'UPLOADED',
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_documents_reporting_month ON documents(reporting_month);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    page_number INTEGER,
    chunk_index INTEGER,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_project ON document_chunks(project_id);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);

CREATE TABLE IF NOT EXISTS model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    dataset_version TEXT,
    feature_version TEXT,
    training_start TIMESTAMPTZ,
    training_end TIMESTAMPTZ,
    metrics JSONB,
    status TEXT NOT NULL DEFAULT 'CANDIDATE',
    artifact_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_versions_name ON model_versions(model_name);

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_monthly_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_drivers ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow read access to all users" ON projects FOR SELECT USING (true);
CREATE POLICY "Allow read access to all users" ON project_monthly_status FOR SELECT USING (true);
CREATE POLICY "Allow read access to all users" ON risk_predictions FOR SELECT USING (true);
CREATE POLICY "Allow read access to all users" ON risk_drivers FOR SELECT USING (true);
CREATE POLICY "Allow read access to all users" ON alerts FOR SELECT USING (true);

COMMIT;
