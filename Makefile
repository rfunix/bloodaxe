test:
	pipenv run pytest -sx

check-dead-fixtures:
	pipenv run pytest --dead-fixtures

pyformat:
	pipenv run black .

lint:
	pipenv run pre-commit install && pipenv run pre-commit run -a -v
