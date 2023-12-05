PY_BIN ?= python3

# The virtualenv containing code style tools.
VENV_CODESTYLE = venv.codestyle
VENV_CODESTYLE_BIN = $(VENV_CODESTYLE)/bin

# The virtualenv containing our CI scripts
VENV_TOOLS = venv.tools
VENV_TOOLS_BIN = $(VENV_TOOLS)/bin

# This is what we pass to git ls-files.
LS_FILES_INPUT_STR ?= 'src/*.py'

.PHONY: default
default: format lint

# The same as format, but will throw a non-zero exit code
# if the formatter had to make changes.
.PHONY: ci.format
ci.format: format
	git diff --exit-code

venv.codestyle:
	$(MAKE) venv.codestyle.always-reinstall

# This target will always install the codestyle venv.
# Useful for development cases.
.PHONY: venv.codestyle.always-reinstall
venv.codestyle.always-reinstall:
	$(PY_BIN) -m venv $(VENV_CODESTYLE)
	./$(VENV_CODESTYLE_BIN)/pip install --upgrade \
		black \
		ruff

.PHONY: format
format: venv.codestyle
	./$(VENV_CODESTYLE_BIN)/black \
		--verbose \
		$$(git ls-files $(LS_FILES_INPUT_STR))

.PHONY: lint
lint: venv.codestyle
	./$(VENV_CODESTYLE_BIN)/ruff \
		check \
		$$(git ls-files $(LS_FILES_INPUT_STR))

venv.tools:
	$(MAKE) venv.tools.always-reinstall

# This target will always install the tools at the venv.
# Useful for development cases.
.PHONY: venv.tools.always-reinstall
venv.tools.always-reinstall:
	$(PY_BIN) -m venv $(VENV_TOOLS)
	./$(VENV_TOOLS_BIN)/pip install -r requirements.txt
	./$(VENV_TOOLS_BIN)/pip install .
