CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS ibero;

CREATE TABLE IF NOT EXISTS ibero.campuses (
  campus_id TEXT PRIMARY KEY,
  campus_code TEXT UNIQUE NOT NULL,
  campus_name TEXT NOT NULL,
  city TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ibero.programs (
  program_id TEXT PRIMARY KEY,
  program_code TEXT UNIQUE NOT NULL,
  program_name TEXT NOT NULL,
  academic_level TEXT,
  campus_id TEXT REFERENCES ibero.campuses(campus_id),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ibero.persons (
  person_id TEXT PRIMARY KEY,
  legacy_system TEXT,
  legacy_id TEXT,
  person_type TEXT NOT NULL CHECK (person_type IN ('student','staff','visitor','contractor')),
  institutional_id TEXT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  second_last_name TEXT,
  email TEXT,
  phone TEXT,
  campus_id TEXT REFERENCES ibero.campuses(campus_id),
  program_id TEXT REFERENCES ibero.programs(program_id),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','blocked','graduated','suspended')),
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_persons_inst_id ON ibero.persons(institutional_id);
CREATE INDEX IF NOT EXISTS idx_persons_type_status ON ibero.persons(person_type, status);

CREATE TABLE IF NOT EXISTS ibero.media_assets (
  media_id TEXT PRIMARY KEY,
  person_id TEXT NOT NULL REFERENCES ibero.persons(person_id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN (
    'selfie','face_template','doc_front','doc_back','student_id_front','student_id_back',
    'access_snapshot','entry_evidence','exit_evidence'
  )),
  uri TEXT NOT NULL,
  mime_type TEXT,
  source_system TEXT,
  checksum_sha256 TEXT,
  captured_at_utc TIMESTAMPTZ,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ibero.identities (
  identity_id TEXT PRIMARY KEY,
  person_id TEXT NOT NULL REFERENCES ibero.persons(person_id) ON DELETE CASCADE,
  country TEXT,
  id_type TEXT,
  id_value TEXT,
  id_value_hash TEXT,
  is_primary BOOLEAN DEFAULT true,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_identities_person ON ibero.identities(person_id);
CREATE INDEX IF NOT EXISTS idx_identities_hash ON ibero.identities(id_value_hash);

CREATE TABLE IF NOT EXISTS ibero.identity_extras (
  identity_id TEXT PRIMARY KEY REFERENCES ibero.identities(identity_id) ON DELETE CASCADE,
  ine_ocr TEXT, ine_cic TEXT, ine_idciudadano TEXT, ine_emision TEXT,
  mrz_document_number TEXT, mrz_document_number_cd TEXT,
  mrz_dob TEXT, mrz_dob_cd TEXT,
  mrz_expiry TEXT, mrz_expiry_cd TEXT,
  mrz_composite TEXT, mrz_composite_cd TEXT,
  us_state TEXT, us_dl_number TEXT, us_dob TEXT, us_expiry TEXT, aamva_version TEXT,
  name_family TEXT, name_given TEXT,
  student_program_code TEXT, employee_area_code TEXT, institutional_card_no TEXT
);

CREATE TABLE IF NOT EXISTS ibero.biometric_profiles (
  biometric_profile_id TEXT PRIMARY KEY,
  person_id TEXT NOT NULL REFERENCES ibero.persons(person_id) ON DELETE CASCADE,
  provider_name TEXT NOT NULL,
  provider_profile_ref TEXT,
  template_hash TEXT NOT NULL,
  template_version TEXT,
  liveness_enabled BOOLEAN NOT NULL DEFAULT true,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','revoked')),
  enrolled_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_biometric_profiles_person_status ON ibero.biometric_profiles(person_id, status);

CREATE TABLE IF NOT EXISTS ibero.credentials (
  credential_id TEXT PRIMARY KEY,
  person_id TEXT NOT NULL REFERENCES ibero.persons(person_id) ON DELETE CASCADE,
  credential_type TEXT NOT NULL CHECK (credential_type IN ('face','qr','nfc','barcode','manual')),
  credential_value TEXT,
  credential_value_hash TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','revoked','expired')),
  valid_from_utc TIMESTAMPTZ,
  valid_until_utc TIMESTAMPTZ,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_credentials_person_status ON ibero.credentials(person_id, status);
CREATE INDEX IF NOT EXISTS idx_credentials_value_hash ON ibero.credentials(credential_value_hash);

CREATE TABLE IF NOT EXISTS ibero.access_points (
  access_point_id TEXT PRIMARY KEY,
  campus_id TEXT NOT NULL REFERENCES ibero.campuses(campus_id),
  point_code TEXT UNIQUE NOT NULL,
  point_name TEXT NOT NULL,
  point_type TEXT NOT NULL CHECK (point_type IN ('gate','turnstile','door','parking','lab')),
  is_active BOOLEAN DEFAULT true,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ibero.devices (
  device_id TEXT PRIMARY KEY,
  access_point_id TEXT NOT NULL REFERENCES ibero.access_points(access_point_id),
  device_code TEXT UNIQUE NOT NULL,
  device_type TEXT NOT NULL CHECK (device_type IN ('camera','reader','tablet','qr_scanner','nvr')),
  vendor TEXT,
  serial_number TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','maintenance')),
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ibero.access_policies (
  policy_id TEXT PRIMARY KEY,
  person_id TEXT REFERENCES ibero.persons(person_id) ON DELETE CASCADE,
  person_type TEXT CHECK (person_type IN ('student','staff','visitor','contractor')),
  campus_id TEXT REFERENCES ibero.campuses(campus_id),
  access_point_id TEXT REFERENCES ibero.access_points(access_point_id),
  allowed_start_time TIME,
  allowed_end_time TIME,
  allowed_days INT[],
  min_face_score NUMERIC(6,4) NOT NULL DEFAULT 0.7000,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_access_policies_person_status ON ibero.access_policies(person_id, status);

CREATE TABLE IF NOT EXISTS ibero.validation_results (
  validation_id TEXT PRIMARY KEY,
  person_id TEXT NOT NULL REFERENCES ibero.persons(person_id) ON DELETE CASCADE,
  identity_id TEXT REFERENCES ibero.identities(identity_id),
  validator_provider TEXT,
  validation_type TEXT NOT NULL CHECK (validation_type IN (
    'identity_verification','document_verification','face_enrollment','face_verification'
  )),
  id_valid BOOLEAN,
  id_reasons TEXT,
  selfie_media_id TEXT REFERENCES ibero.media_assets(media_id),
  doc_media_id TEXT REFERENCES ibero.media_assets(media_id),
  face_distance NUMERIC(6,4),
  face_threshold NUMERIC(6,4),
  face_result TEXT CHECK (face_result IN ('MATCH','NO_MATCH','NO_FACE')),
  qc_flags TEXT[],
  decided_status TEXT CHECK (decided_status IN ('OK','REVIEW','REJECT')),
  decided_by TEXT,
  decided_at_utc TIMESTAMPTZ,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_validation_results_person_time ON ibero.validation_results(person_id, created_at_utc DESC);

CREATE TABLE IF NOT EXISTS ibero.access_events (
  access_event_id TEXT PRIMARY KEY,
  person_id TEXT NOT NULL REFERENCES ibero.persons(person_id) ON DELETE CASCADE,
  device_id TEXT NOT NULL REFERENCES ibero.devices(device_id),
  access_point_id TEXT NOT NULL REFERENCES ibero.access_points(access_point_id),
  event_type TEXT NOT NULL CHECK (event_type IN ('entry','exit','attempt')),
  direction TEXT CHECK (direction IN ('in','out')),
  credential_type TEXT CHECK (credential_type IN ('face','qr','nfc','manual')),
  validation_id TEXT REFERENCES ibero.validation_results(validation_id),
  access_result TEXT NOT NULL CHECK (access_result IN ('ALLOW','DENY','REVIEW')),
  deny_reason TEXT,
  snapshot_media_id TEXT REFERENCES ibero.media_assets(media_id),
  occurred_at_utc TIMESTAMPTZ NOT NULL,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_access_events_person_time ON ibero.access_events(person_id, occurred_at_utc DESC);

CREATE TABLE IF NOT EXISTS ibero.audit_log (
  audit_id TEXT PRIMARY KEY,
  aggregate_type TEXT NOT NULL,
  aggregate_id TEXT NOT NULL,
  action TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  actor_ref TEXT,
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ibero.integration_outbox (
  event_id TEXT PRIMARY KEY,
  aggregate_type TEXT NOT NULL,
  aggregate_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  delivery_attempts INTEGER NOT NULL DEFAULT 0,
  occurred_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
  delivered_at_utc TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_outbox_status_time ON ibero.integration_outbox(status, occurred_at_utc);
