PYTHON_PACKAGES := ai-core cli-ux

.PHONY: all install lint format

all: install lint format

install:
	@for pkg in $(PYTHON_PACKAGES); do \
		echo "Installing dependencies for $$pkg..."; \
		cd $$pkg && unset VIRTUAL_ENV && uv lock --upgrade && uv sync --all-extras --all-groups && cd ..; \
	done

lint:
	@for pkg in $(PYTHON_PACKAGES); do \
		echo "Linting $$pkg..."; \
		cd $$pkg && unset VIRTUAL_ENV && uvx ruff check --no-cache --fix . && cd ..; \
	done

format:
	@for pkg in $(PYTHON_PACKAGES); do \
		echo "Formatting $$pkg..."; \
		cd $$pkg && unset VIRTUAL_ENV && uvx ruff format --no-cache . && cd ..; \
	done
