# Security policy

## Supported version

Security fixes are applied to the latest revision of the `main` branch.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting feature instead of opening a
public issue. Include reproduction steps, the affected revision, and the impact.

## Data handling

- Uploaded PDFs and their embeddings are held in process memory for the active
  Streamlit session; the application does not intentionally persist them.
- The top retrieved passages are sent to the configured LLM provider.
- API keys are read from environment variables, Streamlit Secrets, or a password
  input. They must never be committed to the repository.
- This demo is not designed for confidential, personal, or regulated information.
