.PHONY: install sync get-open-data run clean

install:
	uv pip install -e .

sync:
	uv sync

get-open-data:
	uv run get-open-data

run:
	uv run thi

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.grib" -delete
