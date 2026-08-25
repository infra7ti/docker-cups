# @file Makefile
# @brief Automation tasks for building and pushing Infra7 CUPS container images
#
# SPDX-FileCopyrightText: 2007-2026 Infra7 Serviços em TI
# SPDX-License-Identifier: GPL-2.0-or-later

.PHONY: all proxy full check-docker check-buildx

DOCKER := $(shell command -v docker 2>/dev/null)
PUSH ?= false
PLATFORM ?=

ifeq ($(PUSH),true)
	ACTION_FLAG = --push
	INFO_MSG = building and pushing (multi-arch)
	DEFAULT_PLATFORMS = linux/amd64,linux/arm64
else
	ACTION_FLAG = --load
	INFO_MSG = building locally for testing
	DEFAULT_PLATFORMS =
endif

ifneq ($(PLATFORM),)
	BUILD_PLATFORMS = $(PLATFORM)
else
	BUILD_PLATFORMS = $(DEFAULT_PLATFORMS)
endif

CUPS_VERSION ?= $(shell docker run --rm debian:stable-slim bash -c \
	"apt-get update -qq >/dev/null 2>&1 && apt-cache policy cups | \
	grep -iPo 'Candidate:\s+\K[0-9.]+'")

CUPS_SERIE ?= $(shell echo "$(CUPS_VERSION)" | cut -d'.' -f1-2)

all: full

check-docker:
ifndef DOCKER
	$(error "Docker is required but not installed or not in PATH.")
endif
	@echo "-> Docker is available."

check-buildx: check-docker
	@docker buildx version >/dev/null 2>&1 || \
		{ echo "Error: docker buildx plugin is required."; exit 1; }
	@if ! docker buildx inspect default | grep -q "platforms.*linux/arm64"; then \
		echo "-> Setting up multi-arch 'multiarch' builder instance..."; \
		docker buildx inspect multiarch >/dev/null 2>&1 || \
			docker buildx create --name multiarch --driver docker-container \
			--bootstrap >/dev/null 2>&1; \
		docker buildx use multiarch >/dev/null 2>&1; \
	fi
	@echo "-> Docker buildx multi-arch environment is ready."

proxy: check-buildx
	@echo "Mode: $(INFO_MSG)"
	@echo "CUPS Version: $(CUPS_VERSION)-proxy (Series: $(CUPS_SERIE))"
	docker buildx build \
		$(if $(BUILD_PLATFORMS),--platform $(BUILD_PLATFORMS),) \
		--build-arg VARIANT=proxy \
		-t infra7/cups:$(CUPS_VERSION)-proxy \
		-t infra7/cups:$(CUPS_SERIE)-proxy \
		-t infra7/cups:latest-proxy \
		$(ACTION_FLAG) .

full: check-buildx
	@echo "Mode: $(INFO_MSG)"
	@echo "CUPS Version: $(CUPS_VERSION) (Series: $(CUPS_SERIE))"
	docker buildx build \
		$(if $(BUILD_PLATFORMS),--platform $(BUILD_PLATFORMS),) \
		--build-arg VARIANT=full \
		-t infra7/cups:$(CUPS_VERSION) \
		-t infra7/cups:$(CUPS_SERIE) \
		-t infra7/cups:latest \
		$(ACTION_FLAG) .
