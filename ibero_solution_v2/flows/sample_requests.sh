#!/usr/bin/env bash
set -e

curl -X POST http://localhost:8001/persons   -H 'Content-Type: application/json'   -d '{
    "person_id":"stu_999",
    "person_type":"student",
    "institutional_id":"A09999999",
    "first_name":"Demo",
    "last_name":"Alumno",
    "email":"demo@ibero.mx",
    "campus_id":"campus_cdmx",
    "program_id":"prog_ds"
  }'

echo

curl -X POST http://localhost:8002/biometrics/enroll   -H 'Content-Type: application/json'   -d '{
    "person_id":"stu_999",
    "provider_name":"internal",
    "template_hash":"tmpl_demo_001"
  }'

echo

curl -X POST http://localhost:8002/facematch/verify   -H 'Content-Type: application/json'   -d '{
    "person_id":"stu_999",
    "device_code":"dev-cam-gate-01",
    "access_point_code":"gate-main",
    "candidate_template_hash":"tmpl_demo_001"
  }'
