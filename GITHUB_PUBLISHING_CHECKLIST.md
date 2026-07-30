# GitHub Publishing Checklist

1. Replace `YOUR-GITHUB-USERNAME` in README.md with your GitHub username.
2. Confirm `.env`, `.venv`, `.idea`, local databases, API keys and secrets are absent.
3. Run:
   - ruff check app tests
   - ruff format --check app tests
   - mypy app
   - pytest -q
   - docker compose build --no-cache
4. Create an empty public repository named `marketpulse-analytics-api`.
5. Do not initialize it with a README, .gitignore or license because the project already contains them.
6. Push the local project to the `main` branch.
7. Open the Actions tab and verify the CI workflow is green.
8. Add repository topics:
   python, fastapi, postgresql, sqlalchemy, docker, jwt, pandas, pytest, backend, rest-api
9. Pin the repository on your GitHub profile.
