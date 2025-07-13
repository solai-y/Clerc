Clerc.
======

Document Tagging System\
Classify, view, and edit tags of documents with a modern frontend and robust backend.

Overview
--------

Clerc. is a document tagging system designed to help users classify, view, and edit tags associated with documents. It features a modern frontend and a microservice-based backend, supporting robust document management and tagging workflows.

Features
--------

-   Tagging and classification of documents

-   View and edit tags in an intuitive UI

-   Microservices architecture with Docker support

-   CI/CD pipeline using GitHub Actions

-   Integration with Supabase for data storage

Architecture
------------

text

`Clerc. ├── frontend/                # React or similar frontend app ├── backend/ │   ├── company-service/     # Microservice for company data │   └── categories-service/  # Microservice for category/tag data ├── .github/workflows/       # CI/CD pipeline definitions └── README.md `

-   Frontend: Modern JavaScript framework (e.g., React)

-   Backend: Python Flask microservices, containerized with Docker

-   Database: Supabase (PostgreSQL)

-   CI/CD: Automated with GitHub Actions

Getting Started
---------------

Frontend
--------

1.  Navigate to the frontend directory:

    bash

    `cd frontend `

2.  Install dependencies:

    bash

    `npm  install  `

3.  Start the development server:

    bash

    `npm run dev `

4.  Open [http://localhost:3000](http://localhost:3000/) in your browser.

Backend
-------

1.  Navigate to the backend directory:

    bash

    `cd backend `

2.  Build and start all backend services with Docker Compose:

    bash

    `docker compose up --build `

    This will spin up all microservices defined in your `docker-compose.yml`.

3.  Each service will be available on its respective port (e.g., `company-service` on 5001, `categories-service` on 5002).

Development
-----------

-   Environment Variables:\
    Secrets and API keys are managed via `.env` files (not committed to git). For local development, copy `.env.example` to `.env` and fill in your values.

-   Microservices:\
    Each backend service has its own directory, dependencies, and tests.

Testing
-------

-   Backend:\
    Each microservice contains a `tests/` folder with integration and unit tests using `pytest`.

    bash

    `cd backend/company-service pytest -v `

-   Frontend:\
    Run frontend tests with:

    bash

    `npm  test  `

CI/CD
-----

-   GitHub Actions are used for continuous integration.

-   On each push or PR to `dev` or `main`, the pipeline:

    -   Builds Docker images for backend services

    -   Runs backend and frontend tests

    -   Blocks merging if tests fail or if PR is not from the correct source branch

-   Branch protection rules are recommended for `main` and `dev` to require passing CI and code review before merging.

Contributing
------------

1.  Fork the repo and create your feature branch:

    bash

    `git checkout -b feature/YourFeature `

2.  Commit your changes:

    bash

    `git commit -am 'Add new feature'  `

3.  Push to the branch:

    bash

    `git push origin feature/YourFeature `

4.  Open a pull request

Acknowledgements
----------------

-   [Supabase](https://supabase.com/)

-   [Flask](https://flask.palletsprojects.com/)

-   [React](https://react.dev/) (or your frontend framework)

For more details, see the code and comments in each service directory.