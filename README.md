# FastAPI MongoDB Template
Based on https://github.com/fastapi/full-stack-fastapi-template/

## Technology Stack and Features
- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
    - 🧰 [Beanie](http://beanie-odm.dev) for the Python NoSQL database interactions (ODM).
    - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
    - 💾 [MongoDB](https://www.mongodb.com/) as the NoSQL database.
- 🚀 [React](https://react.dev) for the frontend.
    - 💃 Using TypeScript, hooks, Vite, and other parts of a modern frontend stack.
    - 🎨 [Chakra UI](https://chakra-ui.com) for the frontend components.
    - 🤖 An automatically generated frontend client.
    - 🧪 [Playwright](https://playwright.dev) for End-to-End testing.
    - 🦇 Dark mode support.
- 🐋 [Docker Compose](https://www.docker.com) for development and production.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email based password recovery.
- ✅ Asyncs tests with [Pytest_asyncio](https://pytest-asyncio.readthedocs.io).
- 📞 [Traefik](https://traefik.io) as a reverse proxy / load balancer.
- 🚢 Deployment instructions using Docker Compose, including how to set up a frontend Traefik proxy to handle automatic HTTPS certificates.
- 🏭 ~~CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.~~

## For dev & deployment pleaser refer to:
- https://github.com/fastapi/full-stack-fastapi-template/blob/33b379bd467d778f96c26abfa8e668f3e4c6af18/development.md
- https://github.com/fastapi/full-stack-fastapi-template/blob/33b379bd467d778f96c26abfa8e668f3e4c6af18/deployment.md

## How To Use It
You can **just fork or clone** this repository and use it as is.

## Release Notes
Check the file [release-notes.md](./release-notes.md).

## License
The FARM Template is licensed under the terms of the MIT license.