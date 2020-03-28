test:
	poetry run pytest -sx

check-dead-fixtures:
	poetry run pytest --dead-fixtures

pyformat:
	poetry run black .

lint:
	poetry run pre-commit install && poetry run pre-commit run -a -v
