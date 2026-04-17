import { Log } from './api'

export const SAMPLE_LOGS: Log[] = [
  // Alice – data analyst (lots of reports access, occasional secrets attempt)
  { userId: 'alice', action: 'READ', resource: 's3://corp-data/reports/q1-2026.pdf',    label: 'allowed',      timestamp: '2026-04-01T08:12:00Z' },
  { userId: 'alice', action: 'READ', resource: 's3://corp-data/reports/q2-2026.pdf',    label: 'allowed',      timestamp: '2026-04-01T08:14:00Z' },
  { userId: 'alice', action: 'READ', resource: 's3://corp-data/reports/q3-2026.pdf',    label: 'allowed',      timestamp: '2026-04-02T09:00:00Z' },
  { userId: 'alice', action: 'READ', resource: 's3://corp-data/reports/q4-2026.pdf',    label: 'allowed',      timestamp: '2026-04-02T09:05:00Z' },
  { userId: 'alice', action: 'READ', resource: 's3://corp-data/reports/annual.pdf',     label: 'allowed',      timestamp: '2026-04-03T10:00:00Z' },
  { userId: 'alice', action: 'READ', resource: 's3://corp-data/secrets/api-keys.json',  label: 'over-granted', timestamp: '2026-04-10T11:00:00Z' },
  { userId: 'alice', action: 'READ', resource: 's3://corp-data/finance/payroll.csv',    label: 'over-granted', timestamp: '2026-04-12T14:30:00Z' },

  // Bob – devops (ec2, rarely touches billing)
  { userId: 'bob', action: 'WRITE', resource: 'ec2://instances/i-0a1b2c3d/config',   label: 'allowed',      timestamp: '2026-04-01T07:00:00Z' },
  { userId: 'bob', action: 'WRITE', resource: 'ec2://instances/i-0a1b2c3d/restart',  label: 'allowed',      timestamp: '2026-04-02T07:30:00Z' },
  { userId: 'bob', action: 'WRITE', resource: 'ec2://instances/i-0b2c3d4e/config',   label: 'allowed',      timestamp: '2026-04-03T07:00:00Z' },
  { userId: 'bob', action: 'WRITE', resource: 'ec2://instances/i-0b2c3d4e/restart',  label: 'allowed',      timestamp: '2026-04-04T07:00:00Z' },
  { userId: 'bob', action: 'READ',  resource: 's3://corp-data/billing/march.csv',    label: 'over-granted', timestamp: '2026-04-11T16:00:00Z' },

  // Carol – readonly analytics
  { userId: 'carol', action: 'READ', resource: 's3://analytics/dashboards/main.json',  label: 'allowed',      timestamp: '2026-04-01T09:00:00Z' },
  { userId: 'carol', action: 'READ', resource: 's3://analytics/dashboards/sales.json', label: 'allowed',      timestamp: '2026-04-01T09:05:00Z' },
  { userId: 'carol', action: 'READ', resource: 's3://analytics/dashboards/ops.json',   label: 'allowed',      timestamp: '2026-04-02T09:00:00Z' },
  { userId: 'carol', action: 'READ', resource: 's3://analytics/dashboards/hr.json',    label: 'allowed',      timestamp: '2026-04-03T10:00:00Z' },
  { userId: 'carol', action: 'READ', resource: 's3://analytics/raw/users-dump.csv',    label: 'over-granted', timestamp: '2026-04-13T15:00:00Z' },

  // Dave – db admin
  { userId: 'dave', action: 'DELETE', resource: 'db://prod/records/1001', label: 'allowed',      timestamp: '2026-04-01T10:00:00Z' },
  { userId: 'dave', action: 'DELETE', resource: 'db://prod/records/1002', label: 'allowed',      timestamp: '2026-04-02T10:00:00Z' },
  { userId: 'dave', action: 'DELETE', resource: 'db://prod/records/1003', label: 'allowed',      timestamp: '2026-04-03T10:00:00Z' },
  { userId: 'dave', action: 'DELETE', resource: 'db://prod/records/1004', label: 'allowed',      timestamp: '2026-04-04T10:00:00Z' },
  { userId: 'dave', action: 'WRITE',  resource: 'db://prod/schema/users', label: 'over-granted', timestamp: '2026-04-14T12:00:00Z' },
]

export const SAMPLE_ML_CONFIGS = [
  { id: 'sg-001', name: 'WebServerSG',       userId: 'bob',   action: 'WRITE', resource: 'ec2://sg/0.0.0.0/0-65535', risk: 'critical', issue: 'All ports open to internet' },
  { id: 'iam-001', name: 'DataAnalystRole',  userId: 'alice', action: 'READ',  resource: 's3://corp-data/*',           risk: 'high',     issue: 'Wildcard on sensitive bucket' },
  { id: 'k8s-001', name: 'nginx-deployment', userId: 'dave',  action: 'WRITE', resource: 'k8s://pods/nginx/priv',      risk: 'high',     issue: 'Privileged container' },
  { id: 'iam-002', name: 'ReadOnlyRole',     userId: 'carol', action: 'READ',  resource: 's3://analytics/dashboards/', risk: 'low',      issue: 'Correctly scoped' },
  { id: 'sg-002', name: 'DBSG',             userId: 'dave',  action: 'READ',  resource: 'db://prod/0.0.0.0/5432',     risk: 'high',     issue: 'DB port exposed' },
  { id: 'k8s-002', name: 'api-deployment',  userId: 'bob',   action: 'READ',  resource: 'k8s://pods/api/readonly',    risk: 'low',      issue: 'Secure config' },
]