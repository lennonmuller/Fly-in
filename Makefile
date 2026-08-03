PYTHON = python3
VENV = .venv
BIN = $(VENV)/bin
PIP = pip
MAIN = src/main.py
MAP = maps/easy/01_linear_path.txt

install:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install flake8 mypy pygame
	@clear
	@echo "\033[0;32mInstalled with success!\033[0m"

run: install
	$(BIN)/python3 $(MAIN) $(MAP)

debug:
	$(PYTHON) -m pdb $(MAIN) $(MAP)

clean:
	@rm -rf .mypy_cache .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "\033[0;32mCleaned!\033[0m"

fclean: clean
	@rm -rf $(VENV)

lint:
	@$(BIN)/flake8 .
	@$(BIN)/mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@flake8 .
	@mypy . --strict

help:
	@echo "Help Makefile Commands:"
	@echo ""
	@echo "make install: Install all of the project"
	@echo "make run: Run the project"
	@echo "make debug: Debug using pdb"
	@echo "make clean: Clan all unecessary path"
	@echo "make fclean: clean + clean venv"
	@echo "make lint: check flake8 and mypy"
	@echo "make lint-strict: check lint strict"

.PHONY: install run debug clean fclean lint lint-strict help