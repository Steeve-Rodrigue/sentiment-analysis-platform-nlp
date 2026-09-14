install:
	uv sync --extra ml-phases --group dev

#Run tests
test:
	uv run pytest tests/ -v
