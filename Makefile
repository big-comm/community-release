PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE = 1

.PHONY: all locales pot po check pkg

all: locales

locales:
	$(PYTHON) tools/build-locales.py

pot:
	$(PYTHON) tools/update-locales.py --pot-only

po:
	$(PYTHON) tools/update-locales.py

check: locales
	bash -n usr/bin/comm-release usr/bin/comm-release-gtk pkgbuild/PKGBUILD pkgbuild/pkgbuild.install
	$(PYTHON) -m unittest discover -s tests -v

# Like big-ai-agents: build the committed tree, never an unreviewed work copy.
pkg:
	$(PYTHON) tools/build-package.py
