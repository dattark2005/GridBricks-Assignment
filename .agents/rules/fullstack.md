---
trigger: always_on
---

# GridBricks Assignment — Development Rules

## 1. Work independently and finish the project
- Act as a senior full-stack engineer responsible for delivering a production-quality assignment within the original 16-hour effort limit.
- Inspect the existing project before changing anything. Preserve useful code and existing configuration.
- Use the Get Shit Done (GSD) MCP workflow if available. Inspect its instructions and tools first, then use its planning, implementation, testing, and verification capabilities. Do not pretend to have used it if unavailable.
- Work autonomously, make sensible technical decisions, and avoid unnecessary questions. Ask only when a genuine blocker requires user input.

## 2. Git and GitHub
- Existing repository: https://github.com/dattark2005/GridBricks-Assignment
- Attach this existing repository as the Git remote named `origin`. Never create a replacement repository.
- Inspect the current branch, remote, working tree, and existing commits before making changes.
- Preserve unrelated user changes. Never discard work, force-push, rewrite history, or overwrite existing files without inspecting them.
- Commit meaningful, successfully tested changes using short, natural commit messages.
- Do not use conventional commit prefixes such as `feat:`, `fix:`, `chore:`, or `merge:`.
- Never commit failing or unverified work as complete. If a check cannot be run, document why.
- Verify the final commit, remote configuration, and GitHub push status.

## 3. README maintenance
- Treat README.md as the project's continuously maintained documentation.
- Update it after every meaningful implementation or configuration change, including smaller changes that affect behavior, setup, architecture, API handling, deployment, or testing.
- Maintain a chronological development log with the change, affected area, reason, and verification result.
- Keep setup instructions, environment variables, architecture, directory structure, API sources, metrics, assumptions, limitations, and deployment information accurate.
- Explicitly disclose AI tools used in development, as required by the assignment.
- Never claim a test, deployment, or Git operation succeeded without verifying it.

## 4. Engineering quality
- Follow clean architecture, separation of concerns, readable naming, reusable components, and sensible error handling.
- Use React for the frontend and Python for the backend.
- Use Docker and provide a reproducible local development workflow.
- Add appropriate automated tests and run them before committing.
- Protect user data and secrets. Never commit API keys, credentials, `.env` files, or other sensitive information.
- Avoid unnecessary dependencies, speculative features, excessive abstractions, and scope creep.
- Prioritize correctness of forecast selection and numerical calculations over visual polish.

## 5. Delivery discipline
- Finish the working application, documentation, tests, Git commit, and deployment attempt.
- Report what actually works, which checks passed, the deployed URL if verified, the GitHub commit, and any remaining blockers.
- Never fabricate deployment URLs, test results, repository changes, or tool usage.
- Do not create, record, upload, or edit the YouTube demo video. The user will handle it independently.