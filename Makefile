SHELL := bash
PR = poetry run

 ifeq (, $(shell which poetry))
 $(error "ERROR: poetry (python-poetry) is required. please install it and have it available in your PATH: $(PATH)")
 endif

.PHONY: default
default:
	set -euo pipefail

.PHONY: check-copywrite-headers
check-copywrite-headers: default
	copywrite headers --spdx "MIT" --plan

.PHONY: apply-copywrite-headers
apply-copywrite-headers: default
	copywrite headers --spdx "MIT"

.PHONY: dependency
dependency: default
	poetry env info
	poetry install -n

.PHONY: list-tests
list-tests: default
	cd extensions && $(PR) molecule list

.PHONY: test-nomad-modules
test-nomad-modules: default
	cd extensions && $(PR) molecule list --scenario-name nomad_modules
	cd extensions && $(PR) molecule converge --scenario-name nomad_modules
	cd extensions && $(PR) molecule destroy --scenario-name nomad_modules

