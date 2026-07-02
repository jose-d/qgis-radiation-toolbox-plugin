#/***************************************************************************
# RadiationToolbox
#
# Radiation Toolbox
#							 -------------------
#		begin				: 2016-05-25
#		git sha				: $Format:%H$
#		copyright			: (C) 2016-2019 by OpenGeoLabs
#		email				: info@opengeolabs.cz
# ***************************************************************************/
#
#/***************************************************************************
# *																		 *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or	 *
# *   (at your option) any later version.								   *
# *																		 *
# ***************************************************************************/

#################################################
# Edit the following to match your sources lists
#################################################


#Add iso code for any locales you want to support here (space separated)
# default is no locales
# LOCALES = af
LOCALES = radiation_toolbox_cs

# If locales are enabled, set the name of the lrelease binary on your system.
# Override with `make LRELEASE=/path/to/lrelease` if needed.
LRELEASE ?= $(shell command -v /usr/lib/qt6/bin/lrelease 2>/dev/null || command -v lrelease 2>/dev/null)


# translation
SOURCES = \
	__init__.py \
	radiation_toolbox.py radiation_toolbox_dockwidget.py

PLUGINNAME = radiation_toolbox_plugin
PLUGIN_ZIP = $(PLUGINNAME).zip
PACKAGE_BUILD_DIR = zip_build
PACKAGE_PLUGIN_DIR = $(PACKAGE_BUILD_DIR)/$(PLUGINNAME)
READER_PACKAGE = git+https://gitlab.com/opengeolabs/radiation-toolbox/radiation-toolbox-reader.git@ec322170b87a26d2cab1e4666b3277c621b92605

PY_FILES = \
	__init__.py \
	radiation_toolbox.py radiation_toolbox_dockwidget.py \
	resources.py

UI_FILES = radiation_toolbox_dockwidget_base.ui

EXTRAS = metadata.txt LICENSE

EXTRA_DIRS = layer style tools i18n icons

COMPILED_RESOURCE_FILES = resources.rcc

PEP8EXCLUDE=pydev,resources.py,conf.py,third_party,ui


#################################################
# Normally you would not need to edit below here
#################################################

HELP = help/build/html

PLUGIN_UPLOAD = $(c)/plugin_upload.py

RESOURCE_SRC=$(shell grep '^ *<file' resources.qrc | sed 's@</file>@@g;s/.*>//g' | tr '\n' ' ')
RCC ?= $(shell command -v /usr/lib/qt6/libexec/rcc 2>/dev/null || command -v rcc 2>/dev/null)

QGISDIR=.qgis2
PLUGIN_DIR = $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
VERSION ?= HEAD

default: compile

compile: $(COMPILED_RESOURCE_FILES)

resources.rcc: resources.qrc $(RESOURCE_SRC)
	"$(RCC)" --binary -o $@ $<

%.qm : %.ts
	$(LRELEASE) $<

test: compile transcompile
	@echo
	@echo "----------------------"
	@echo "Regression Test Suite"
	@echo "----------------------"

	@# Preceding dash means that make will continue in case of errors
	@-export PYTHONPATH=`pwd`:$(PYTHONPATH); \
		export QGIS_DEBUG=0; \
		export QGIS_LOG_FILE=/dev/null; \
		nosetests -v --with-id --with-coverage --cover-package=. \
		3>&1 1>&2 2>&3 3>&- || true
	@echo "----------------------"
	@echo "If you get a 'no module named qgis.core error, try sourcing"
	@echo "the helper script we have provided first then run make test."
	@echo "e.g. source run-env-linux.sh <path to qgis install>; make test"
	@echo "----------------------"

deploy: compile doc transcompile
	@echo
	@echo "------------------------------------------"
	@echo "Deploying plugin to your .qgis2 directory."
	@echo "------------------------------------------"
	# The deploy  target only works on unix like operating system where
	# the Python plugin directory is located at:
	# $HOME/$(QGISDIR)/python/plugins
	mkdir -p "$(PLUGIN_DIR)"
	cp -vf $(PY_FILES) "$(PLUGIN_DIR)"
	cp -vf $(UI_FILES) "$(PLUGIN_DIR)"
	cp -vf $(COMPILED_RESOURCE_FILES) "$(PLUGIN_DIR)"
	cp -vf $(EXTRAS) "$(PLUGIN_DIR)"
	for dir in $(EXTRA_DIRS); do cp -vfr "$$dir" "$(PLUGIN_DIR)"; done
	cp -vfr "$(HELP)" "$(PLUGIN_DIR)/help"


# The dclean target removes compiled python files from plugin directory
# also deletes any .git entry
dclean:
	@echo
	@echo "-----------------------------------"
	@echo "Removing any compiled python files."
	@echo "-----------------------------------"
	find "$(PLUGIN_DIR)" -iname "*.pyc" -delete
	find "$(PLUGIN_DIR)" -iname ".git" -prune -exec rm -Rf {} \;


derase:
	@echo
	@echo "-------------------------"
	@echo "Removing deployed plugin."
	@echo "-------------------------"
	rm -Rf "$(PLUGIN_DIR)"

zip: deploy dclean
	@echo
	@echo "---------------------------"
	@echo "Creating plugin zip bundle."
	@echo "---------------------------"
	# The zip target deploys the plugin and creates a zip file with the deployed
	# content. You can then upload the zip file on http://plugins.qgis.org
	rm -f "$(PLUGIN_ZIP)"
	cd "$(HOME)/$(QGISDIR)/python/plugins"; zip -9r "$(CURDIR)/$(PLUGIN_ZIP)" "$(PLUGINNAME)"

package: compile doc transcompile
	# Create a QGIS-installable zip package of the plugin.
	@echo
	@echo "------------------------------------"
	@echo "Building plugin zip package.	"
	@echo "------------------------------------"
	rm -rf "$(PACKAGE_BUILD_DIR)" "$(PLUGIN_ZIP)"
	mkdir -p "$(PACKAGE_PLUGIN_DIR)"
	cp -vf $(PY_FILES) "$(PACKAGE_PLUGIN_DIR)"
	cp -vf $(UI_FILES) "$(PACKAGE_PLUGIN_DIR)"
	cp -vf $(COMPILED_RESOURCE_FILES) "$(PACKAGE_PLUGIN_DIR)"
	cp -vf $(EXTRAS) "$(PACKAGE_PLUGIN_DIR)"
	for dir in $(EXTRA_DIRS); do cp -vfr "$$dir" "$(PACKAGE_PLUGIN_DIR)"; done
	cp -vfr "$(HELP)" "$(PACKAGE_PLUGIN_DIR)/help"
	python3 -m pip install --target "$(PACKAGE_PLUGIN_DIR)" --no-deps --no-compile "$(READER_PACKAGE)"
	find "$(PACKAGE_PLUGIN_DIR)" -type d -name "__pycache__" -prune -exec rm -rf {} +
	find "$(PACKAGE_PLUGIN_DIR)" -name "*.pyc" -delete
	cd "$(PACKAGE_BUILD_DIR)"; zip -9r "$(CURDIR)/$(PLUGIN_ZIP)" "$(PLUGINNAME)"
	echo "Created package: $(PLUGIN_ZIP)"

upload: zip
	@echo
	@echo "-------------------------------------"
	@echo "Uploading plugin to QGIS Plugin repo."
	@echo "-------------------------------------"
	$(PLUGIN_UPLOAD) "$(PLUGIN_ZIP)"

transup:
	@echo
	@echo "------------------------------------------------"
	@echo "Updating translation files with any new strings."
	@echo "------------------------------------------------"
	@chmod +x scripts/update-strings.sh
	@scripts/update-strings.sh $(LOCALES)

transcompile:
	@echo
	@echo "----------------------------------------"
	@echo "Compiled translation files to .qm files."
	@echo "----------------------------------------"
	@chmod +x scripts/compile-strings.sh
	@scripts/compile-strings.sh $(LRELEASE) $(LOCALES)

transclean:
	@echo
	@echo "------------------------------------"
	@echo "Removing compiled translation files."
	@echo "------------------------------------"
	rm -f i18n/*.qm

clean:
	@echo
	@echo "------------------------------------"
	@echo "Removing uic and rcc generated files"
	@echo "------------------------------------"
	rm $(COMPILED_UI_FILES) $(COMPILED_RESOURCE_FILES)

doc:
	@echo
	@echo "------------------------------------"
	@echo "Building documentation using sphinx."
	@echo "------------------------------------"
	cd help; make html

pylint:
	@echo
	@echo "-----------------"
	@echo "Pylint violations"
	@echo "-----------------"
	@pylint --reports=n --rcfile=pylintrc . || true
	@echo
	@echo "----------------------"
	@echo "If you get a 'no module named qgis.core' error, try sourcing"
	@echo "the helper script we have provided first then run make pylint."
	@echo "e.g. source run-env-linux.sh <path to qgis install>; make pylint"
	@echo "----------------------"


# Run pep8 style checking
#http://pypi.python.org/pypi/pep8
pep8:
	@echo
	@echo "-----------"
	@echo "PEP8 issues"
	@echo "-----------"
	@pep8 --repeat --ignore=E203,E121,E122,E123,E124,E125,E126,E127,E128 --exclude $(PEP8EXCLUDE) . || true
	@echo "-----------"
	@echo "Ignored in PEP8 check:"
	@echo $(PEP8EXCLUDE)
