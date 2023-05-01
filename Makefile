PROJECT := frontend-co2
PACKAGE := src
MODULES := $(wildcard $(PACKAGE)/*.py)

# MAIN TASKS ##################################################################

.PHONY: all
all: format check ## Run all tasks that determine CI status

.PHONY: dev
dev: poetry run sniffer ## Continuously run CI tasks when files chanage

# CHECK #######################################################################

.PHONY: format
format:
	poetry run isort $(PACKAGE)
	poetry run black $(PACKAGE)
	@ echo

.PHONY: check
check: format ## Run formaters, linters, and static analysis
ifdef CI
	git diff --exit-code
endif
	poetry run mypy $(PACKAGE)
	poetry run pylint $(PACKAGE) --rcfile=.pylint.ini
	poetry run pydocstyle $(PACKAGE)