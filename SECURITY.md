# Security and privacy policy

This project observes a user-selected WeChat group through the already logged-in
Windows desktop client. Reports, OCR text, screenshots, employee aliases, and
group names can contain personal or confidential information.

- Never commit `employees.yaml`, `settings.yaml`, `reports/`, `evidence/`,
  screenshots, logs, or exported OCR data.
- The example configuration and scheduled-task installer are dry-run by
  default. Real group delivery requires both configuration changes and the
  explicit `--send` command-line flag.
- Use a dedicated Windows account where practical and keep the workstation
  unlocked only for the minimum required period.
- Do not use this project to bypass WeChat security controls or access messages
  the operator is not already authorized to view.

Please use GitHub's private vulnerability reporting feature for security issues.
Do not include real chat content or identities in a public report.
