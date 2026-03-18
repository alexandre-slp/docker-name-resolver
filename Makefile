.DEFAULT_GOAL := help

APP_NAME				:=dnr
APP_DIR					:=/${APP_NAME}
DOCKER_SOCKET			:=/var/run/docker.sock
BUILD_IMAGE				:=${APP_NAME}-build
RELEASE_IMAGE			:=${APP_NAME}-release
DOCKER_HUB_IMAGE_NAME	:=alexandreslp/docker-name-resolver
VERSION					:=$(if ${v},${v},latest)
HAS_BUILD_IMAGE			:=$(shell docker images --quiet ${BUILD_IMAGE})
HAS_RELEASE_IMAGE		:=$(shell docker images --quiet ${RELEASE_IMAGE})
PWD						:=$(shell pwd)

.PHONY: welcome
welcome:
	@printf "\033[33m    ____  _   ______  \n"
	@printf "\033[33m   / __ \/ | / / __ \ \n"
	@printf "\033[33m  / / / /  |/ / /_/ / \n"
	@printf "\033[33m / /_/ / /|  / _, _/  \n"
	@printf "\033[33m/_____/_/ |_/_/ |_|   \n"
	@printf "\n"

.PHONY: help
help: welcome
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep ^help -v | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

.PHONY: build
build: welcome  ## Build DNR build image
	@if [ -z '${HAS_BUILD_IMAGE}' ]; \
		then \
			docker build \
				--no-cache \
				--pull \
				--force-rm \
				--target dev \
				--tag ${BUILD_IMAGE} \
				. \
		; \
	fi

.PHONY: build-force
build-force: welcome  ## Build DNR build image
	@docker build \
		--no-cache \
		--pull \
		--force-rm \
		--target dev \
		--tag ${BUILD_IMAGE} \
		.

.PHONY: release
release: welcome  ## Build DNR release image
	@if [ -z '${HAS_RELEASE_IMAGE}' ]; \
		then \
			docker build \
				--no-cache \
				--pull \
				--force-rm \
				--target release \
				--tag ${RELEASE_IMAGE} \
				. \
		; \
	fi

.PHONY: docker-hub-image-push
docker-hub-image-push: welcome release  ## Pushes Docker image to Docker Hub
	@docker tag ${RELEASE_IMAGE} ${DOCKER_HUB_IMAGE_NAME}:${VERSION}
	docker push ${DOCKER_HUB_IMAGE_NAME}:${VERSION}

.PHONY: start
start: welcome build  ## Run DNR container (PWD mounted; code/template changes apply without rebuild)
	@echo 'DNR online'
	@docker run \
			--detach \
			--tty \
			--rm \
			--volume ${DOCKER_SOCKET}:${DOCKER_SOCKET} \
			--volume ${PWD}:${APP_DIR} \
			--publish 80:80 \
			--publish 443:443 \
			--name ${APP_NAME} \
			${BUILD_IMAGE}

.PHONY: test
test: welcome build ## Run tests
	@docker run \
			--interactive \
			--tty \
			--rm \
			--volume ${PWD}:${APP_DIR} \
			--workdir ${APP_DIR} \
			--entrypoint pytest \
			--name ${APP_NAME}-test \
			${BUILD_IMAGE}

.PHONY: rmi
rmi: ## Remove DNR images
	@if [ '${HAS_BUILD_IMAGE}' ]; \
		then \
			docker rmi ${BUILD_IMAGE} \
		; \
	fi
	@if [ '${HAS_RELEASE_IMAGE}' ]; \
		then \
			docker rmi ${RELEASE_IMAGE} \
		; \
	fi

.PHONY: stop
stop: ## Stop DNR
	@docker stop ${APP_NAME}
