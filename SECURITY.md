# Security Policy

## Supported Status

AuditAI is an active prototype and is not yet intended for production use.

## Reporting a Vulnerability

Please do not open a public issue for suspected vulnerabilities. Contact the repository owner privately through the LinkedIn profile linked in the project README.

Include:

- a clear description of the issue
- affected component or file
- steps to reproduce
- potential impact
- a suggested remediation, if available

Do not include real credentials, confidential audit evidence, corporate data or personal information in any report.

## Secure Configuration

- Set SESSION_SECRET through a secure environment variable.
- Use a strong, unique ADMIN_PASSWORD.
- Store production secrets in a managed secret store.
- Keep FLASK_DEBUG disabled outside local development.
- Use synthetic or irreversibly anonymized data for demonstrations.
- Review generated exports before sharing them.
