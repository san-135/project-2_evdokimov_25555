.PHONY: install project run build publish package-install p-install activate lint ruff fix

install:
	poetry install

project run:
	poetry run project

build:
	poetry build

publish:
	poetry publish --dry-run

package-install p-install:
	python3 -m pip install dist/*.whl

activate:
	source .venv/bin/activate

lint ruff:
	poetry run ruff check .

fix:
	poetry run ruff check . --fix
