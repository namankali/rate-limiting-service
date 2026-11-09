# rate-limiting-service


<!-- ruff commands -->

ruff check .  // lint the project
ruff format --check .  // check formatting without changing file


<!-- mypy -->

mypy

<!-- Validate .pre-commit-config.yaml -->
pre-commit validate-config



<!-- Run migrations -->
<!-- 1. Generate migration -->
alembic revision --autogenerate -m "........"
<!-- 2. Apply migration -->
alembic upgrade head
<!-- 3. Verify -->
alembic current