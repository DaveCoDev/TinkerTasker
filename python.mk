.DEFAULT_GOAL ?= install

UV_SYNC_INSTALL_ARGS ?= --all-extras --all-groups
PYTHON_PACKAGES ?= ai-core cli-ux

.PHONY: all install lint format
all: install lint format

# If we have a pyproject.toml in current directory, we're in a package
# Otherwise, we're in the root and should run across all packages
ifneq ($(wildcard pyproject.toml),)
# Single package targets
install:
	uv lock --upgrade && uv sync $(UV_SYNC_INSTALL_ARGS)

lint:
	uvx ruff check --no-cache --fix .

format:
	uvx ruff format --no-cache .
else
# Multi-package targets (for root directory)
install:
	@for pkg in $(PYTHON_PACKAGES); do \
		$(MAKE) -C $$pkg install; \
	done

lint:
	@for pkg in $(PYTHON_PACKAGES); do \
		$(MAKE) -C $$pkg lint; \
	done

format:
	@for pkg in $(PYTHON_PACKAGES); do \
		$(MAKE) -C $$pkg format; \
	done
endif