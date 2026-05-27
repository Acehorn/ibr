#!/usr/bin/env bash
set -e

curl -X POST http://localhost:8002/biometrics/enroll \
  -H 'Content-Type: application/json' \
  -d '{
    "personId": "00000000-0000-0000-0000-000000000001",
    "providerName": "legacy_face",
    "providerProfileRef": "FACE-DEMO-1",
    "templateHash": "hash_face_1001",
    "templateVersion": "v1",
    "livenessEnabled": true
  }'

curl -X POST http://localhost:8002/facematch/verify \
  -H 'Content-Type: application/json' \
  -d '{
    "personHint": "A00124567",
    "deviceCode": "CAM-ENT-01",
    "accessPointCode": "AP-01",
    "templateHashCandidate": "hash_face_1001",
    "evidenceUri": "s3://ibero/evidence/demo.jpg"
  }'

curl -X POST http://localhost:8003/access/decision \
  -H 'Content-Type: application/json' \
  -d '{
    "direction": "ENTRY",
    "accessPointCode": "AP-01",
    "deviceCode": "TRN-ENT-01",
    "credentialCode": "QR-A00124567",
    "facematchEventId": "REPLACE_ME"
  }'
