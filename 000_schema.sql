CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS campuses (
  campus_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  legacy_system TEXT,
  legacy_id TEXT,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  city TEXT,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS programs (
  program_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  legacy_system TEXT,
  legacy_id TEXT,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  academic_level TEXT,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS persons (
  person_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  legacy_system TEXT,
  legacy_id TEXT,
  external_ref TEXT UNIQUE,
  institutional_id TEXT UNIQUE,
  person_type TEXT NOT NULL CHECK (person_type IN ('student','staff','visitor')),
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  program_id UUID REFERENCES programs(program_id),
  campus_id UUID REFERENCES campuses(campus_id),
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS credentials (
  credential_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id UUID NOT NULL REFERENCES persons(person_id),
  credential_code TEXT UNIQUE NOT NULL,
  credential_type TEXT NOT NULL DEFAULT 'QR',
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ,
  last_used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS access_points (
  access_point_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campus_id UUID NOT NULL REFERENCES campuses(campus_id),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  building TEXT,
  zone TEXT,
  direction_mode TEXT NOT NULL DEFAULT 'BOTH',
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS devices (
  device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  access_point_id UUID NOT NULL REFERENCES access_points(access_point_id),
  code TEXT UNIQUE NOT NULL,
  device_type TEXT NOT NULL CHECK (device_type IN ('tablet','turnstile','camera','kiosk','reader')),
  serial_number TEXT,
  ip_address TEXT,
  firmware_version TEXT,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  last_seen_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS biometric_profiles (
  biometric_profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id UUID NOT NULL REFERENCES persons(person_id),
  provider_name TEXT NOT NULL DEFAULT 'internal',
  provider_profile_ref TEXT,
  template_hash TEXT NOT NULL,
  template_version TEXT,
  liveness_enabled BOOLEAN NOT NULL DEFAULT true,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS biometric_artifacts (
  artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  biometric_profile_id UUID NOT NULL REFERENCES biometric_profiles(biometric_profile_id),
  artifact_type TEXT NOT NULL CHECK (artifact_type IN ('face_image','embedding','match_snapshot','liveness_video')),
  artifact_uri TEXT,
  artifact_sha256 TEXT,
  pii_level TEXT NOT NULL DEFAULT 'SENSITIVE',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS access_policies (
  policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id UUID NOT NULL REFERENCES persons(person_id),
  access_point_id UUID REFERENCES access_points(access_point_id),
  weekday_mask TEXT NOT NULL DEFAULT '1111111',
  start_time TIME,
  end_time TIME,
  min_face_score NUMERIC(5,2) NOT NULL DEFAULT 0.80,
  allow_entry BOOLEAN NOT NULL DEFAULT true,
  allow_exit BOOLEAN NOT NULL DEFAULT true,
  rule_reason TEXT,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS facematch_events (
  facematch_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id UUID REFERENCES persons(person_id),
  device_id UUID REFERENCES devices(device_id),
  access_point_id UUID REFERENCES access_points(access_point_id),
  provider_name TEXT NOT NULL DEFAULT 'internal',
  provider_request_id TEXT,
  score NUMERIC(6,4),
  threshold NUMERIC(6,4),
  liveness_score NUMERIC(6,4),
  result TEXT NOT NULL CHECK (result IN ('MATCH','NO_MATCH','REVIEW','ERROR')),
  evidence_uri TEXT,
  raw_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS access_events (
  access_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id UUID REFERENCES persons(person_id),
  credential_id UUID REFERENCES credentials(credential_id),
  facematch_event_id UUID REFERENCES facematch_events(facematch_event_id),
  access_point_id UUID NOT NULL REFERENCES access_points(access_point_id),
  device_id UUID REFERENCES devices(device_id),
  direction TEXT NOT NULL CHECK (direction IN ('ENTRY','EXIT')),
  decision TEXT NOT NULL CHECK (decision IN ('ALLOW','DENY','REVIEW')),
  decision_reason TEXT,
  event_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_log (
  audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_type TEXT NOT NULL,
  aggregate_id TEXT NOT NULL,
  action TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  actor_ref TEXT,
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS integration_outbox (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_type TEXT NOT NULL,
  aggregate_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  delivery_attempts INTEGER NOT NULL DEFAULT 0,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  delivered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_persons_type_status ON persons(person_type, status);
CREATE INDEX IF NOT EXISTS idx_credentials_person_status ON credentials(person_id, status);
CREATE INDEX IF NOT EXISTS idx_biometric_profiles_person_status ON biometric_profiles(person_id, status);
CREATE INDEX IF NOT EXISTS idx_access_events_person_time ON access_events(person_id, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_facematch_events_person_time ON facematch_events(person_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_outbox_status_time ON integration_outbox(status, occurred_at);
