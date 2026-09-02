@echo off
REM Make batch file for Windows - translates make commands to PowerShell

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="dev-up" goto dev-up
if "%1"=="dev-down" goto dev-down
if "%1"=="dev-build" goto dev-build
if "%1"=="run-api" goto run-api
if "%1"=="run-worker" goto run-worker
if "%1"=="test" goto test
if "%1"=="test-backend" goto test-backend
if "%1"=="test-frontend" goto test-frontend
if "%1"=="lint" goto lint
if "%1"=="typecheck" goto typecheck
if "%1"=="db-migrate" goto db-migrate
if "%1"=="db-seed" goto db-seed
if "%1"=="build" goto build
if "%1"=="clean" goto clean
goto help

:help
echo Usage: make [target]
echo.
echo Targets:
echo   help        Show this help
echo   dev-up      Start all services with Docker Compose
echo   dev-down    Stop all services
echo   dev-build   Build and start all services
echo   run-api     Run API service locally
echo   run-worker  Run worker service locally
echo   db-migrate  Run database migrations
echo   db-seed     Seed database with sample data
echo   test        Run all tests
echo   lint        Run all linters
echo   typecheck   Run type checkers
echo   build       Build all Docker images
echo   clean       Remove build artifacts
goto end

:dev-up
docker compose -f docker/docker-compose.yml up -d
goto end

:dev-down
docker compose -f docker/docker-compose.yml down
goto end

:dev-build
docker compose -f docker/docker-compose.yml up -d --build
goto end

:run-api
poetry run python -m apps.api.src.main
goto end

:run-worker
poetry run python -m apps.worker.src.main
goto end

:db-migrate
poetry run alembic upgrade head
goto end

:db-seed
poetry run python -m apps.api.src.infrastructure.seeding.seed
goto end

:test
poetry run pytest apps/api/tests -v
cd apps/frontend && npm run test
goto end

:test-backend
poetry run pytest apps/api/tests -v
goto end

:test-frontend
cd apps/frontend && npm run test
goto end

:lint
poetry run ruff check apps/api/src
cd apps/frontend && npm run lint
goto end

:typecheck
poetry run pyright apps/api/src
cd apps/frontend && npm run typecheck
goto end

:build
docker compose -f docker/docker-compose.yml build
goto end

:clean
Remove-Item -Recurse -Force .pytest_cache, .mypy_cache, .ruff_cache -ErrorAction SilentlyContinue
goto end

:end
