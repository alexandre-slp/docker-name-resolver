.DEFAULT_GOAL := help
.PHONY: help welcome build unix windows wsl test rmi stop

APP_NAME				:= dnr
APP_DIR					:= /${APP_NAME}
DOCKER_SOCKET			:= /var/run/docker.sock
CONTAINER_HOSTS_PATH	:= /dnr/hosts
UNIX_HOSTS_LOCATION		:= /etc/hosts
WINDOWS_HOSTS_LOCATION	:= C:/Windows/System32/drivers/etc/hosts
BUILD_IMAGE				:= ${APP_NAME}-build
RELEASE_IMAGE			:= ${APP_NAME}-release
DOCKER_HUB_IMAGE_NAME	:= alexandreslp/docker-name-resolver
VERSION					:= $(if ${v}, ${v}, latest)
HAS_BUILD_IMAGE			:= $(shell docker images --quiet ${BUILD_IMAGE})
HAS_RELEASE_IMAGE		:= $(shell docker images --quiet ${RELEASE_IMAGE})
PWD						:= $(shell pwd)

welcome:
	@printf "\033[33m    ____  _   ______  \n"
	@printf "\033[33m   / __ \/ | / / __ \ \n"
	@printf "\033[33m  / / / /  |/ / /_/ / \n"
	@printf "\033[33m / /_/ / /|  / _, _/  \n"
	@printf "\033[33m/_____/_/ |_/_/ |_|   \n"
	@printf "\n"

help: welcome
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep ^help -v | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

build: welcome  ## Build DNR build image
	@if [ -z '${HAS_BUILD_IMAGE}' ]; \
		then \
			docker build \
				--no-cache \
				--pull \
				--force-rm \
				--target build \
				--tag ${BUILD_IMAGE} \
				. \
		; \
	fi

release: welcome build  ## Build DNR release image
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

docker-hub-image-push: welcome release  ## Pushes Docker image to Docker Hub
	@docker tag ${RELEASE_IMAGE} ${DOCKER_HUB_IMAGE_NAME}
	@docker push ${DOCKER_HUB_IMAGE_NAME}:${VERSION}

unix: welcome release  ## Run DNR on unix systems
	@echo 'DNR online'
	@docker run \
			--detach \
			--tty \
			--rm \
			--volume ${DOCKER_SOCKET}:${DOCKER_SOCKET} \
			--volume ${UNIX_HOSTS_LOCATION}:${CONTAINER_HOSTS_PATH} \
			--name ${APP_NAME} \
			${RELEASE_IMAGE} -v

windows: welcome release  ## Run DNR on windows system
	@echo 'DNR online'
	@docker run \
			--detach \
			--tty \
			--rm \
			--volume ${DOCKER_SOCKET}:${DOCKER_SOCKET} \
			--volume ${WINDOWS_HOSTS_LOCATION}:${CONTAINER_HOSTS_PATH} \
			--name ${APP_NAME} \
			${RELEASE_IMAGE} -v

wsl: welcome release  ## Run DNR on wsl system
	@echo 'DNR online'
	@docker run \
			--detach \
			--tty \
			--rm \
			--volume ${DOCKER_SOCKET}:${DOCKER_SOCKET} \
			--volume ${UNIX_HOSTS_LOCATION}:${CONTAINER_HOSTS_PATH} \
			--volume ${WINDOWS_HOSTS_LOCATION}:${CONTAINER_HOSTS_PATH} \
			--name ${APP_NAME} \
			${RELEASE_IMAGE} -v

test: welcome build ## Run tests
	@docker run \
			--interactive \
			--tty \
			--rm \
			--volume ${PWD}:${APP_DIR} \
			--name ${APP_NAME}-test \
			${BUILD_IMAGE} \
			pytest

rmi: ## Remove DNR image
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

stop: ## Stop DNR
	@docker stop ${APP_NAME}
