.DEFAULT_GOAL := help

# Setup
PROJECT_NAME := IconCreationPlugin
WORKSPACE ?= ${PWD}
PLATFORM_LIST = Windows MacOS
VIRTUAL_ENV_DIR = _venv

# Maya
MAYA_VERSION = 2020
BUILD_MAYA := ./scripts/build-maya.sh
DEV_MAYA := ./scripts/dev-maya.sh

# Push the variables to the env.
export MAYA_VERSION WORKSPACE PROJECT_NAME

# Remove all files created by the build command.
.PHONY : clean
clean:
	rm -Rf build dist src/*.egg-info .eggs *.egg
	find . -name "*.pyc" -exec rm -f {} \;

# Build into a useable Maya module in the dist directory at the project root.
.PHONY : build
build: clean build-windows build-mac

build-windows:
	export PLATFORM=Windows; \
	export MAYA_MODULE_PATH=$$WORKSPACE/dist/$$PLATFORM/maya/modules; \
	${BUILD_MAYA} && \
	cd $$WORKSPACE/dist/$$PLATFORM/maya/modules && \
	zip -r $$WORKSPACE/dist/IconCreationPlugin-$$PLATFORM-0.2.0.zip ./*

build-mac:
	export PLATFORM=MacOS; \
	export MAYA_MODULE_PATH=$$WORKSPACE/dist/$$PLATFORM/maya/modules; \
	${BUILD_MAYA} && \
	cd $$WORKSPACE/dist/$$PLATFORM/maya/modules && \
	zip -r $$WORKSPACE/dist/IconCreationPlugin-$$PLATFORM-0.2.0.zip ./*

.PHONY : dev
dev: clean build dev-windows dev-mac

dev-windows:
	export PLATFORM=Windows; \
	export MAYA_MODULE_PATH=$$WORKSPACE/dist/$$PLATFORM/maya/modules; \
	${DEV_MAYA}

dev-mac:
	export PLATFORM=MacOS; \
	export MAYA_MODULE_PATH=$$WORKSPACE/dist/$$PLATFORM/maya/modules; \
	${DEV_MAYA}

.PHONY : install-dev-deps
install-dev-deps:
	virtualenv -p python2.7 --no-setuptools --clear ${VIRTUAL_ENV_DIR}
	source ${VIRTUAL_ENV_DIR}/bin/activate && \
		pip install "setuptools<45"
	source ${VIRTUAL_ENV_DIR}/bin/activate && \
		pip install -r requirements/dev.txt
