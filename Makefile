.DEFAULT_GOAL := help
.PHONY: help welcome build unix windows wsl test rmi stop

APP_NAME:=dnr
APP_DIR:=/${APP_NAME}
DOCKER_SOCKET:=/var/run/docker.sock
UNIX_HOSTS_LOCATION:=/etc/hosts
WINDOWS_HOSTS_LOCATION:=C:/Windows/System32/drivers/etc/hosts
HAS_IMAGE:=$(shell docker images --quiet ${APP_NAME})
PWD:=$(shell pwd)

welcome:
	@printf "\033[33m    ____  _   ______  \n"
	@printf "\033[33m   / __ \/ | / / __ \ \n"
	@printf "\033[33m  / / / /  |/ / /_/ / \n"
	@printf "\033[33m / /_/ / /|  / _, _/  \n"
	@printf "\033[33m/_____/_/ |_/_/ |_|   \n"
	@printf "\n"

help: welcome
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep ^help -v | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

build: welcome  ## Build DNR image
	@if [ -z '${HAS_IMAGE}' ]; \
		then \
			docker build \
				--no-cache \
				--pull \
				--force-rm \
				--tag ${APP_NAME} \
				. \
		; \
	fi

unix: welcome build  ## Run DNR on unix systems
	@echo 'DNR online'
	@docker run \
			--detach \
			--tty \
			--rm \
			--volume ${DOCKER_SOCKET}:${DOCKER_SOCKET} \
			--volume ${UNIX_HOSTS_LOCATION}:${UNIX_HOSTS_LOCATION} \
			--name ${APP_NAME} \
			${APP_NAME}

windows: welcome build  ## Run DNR on windows system
	@echo 'DNR online'
	@docker run \
			--detach \
			--tty \
			--rm \
			--volume ${DOCKER_SOCKET}:${DOCKER_SOCKET} \
			--volume ${WINDOWS_HOSTS_LOCATION}:${WINDOWS_HOSTS_LOCATION} \
			--name ${APP_NAME} \
			${APP_NAME}

wsl: welcome build  ## Run DNR on wsl system
	@echo 'DNR online'
	@docker run \
			--detach \
			--tty \
			--rm \
			--volume ${DOCKER_SOCKET}:${DOCKER_SOCKET} \
			--volume ${UNIX_HOSTS_LOCATION}:${UNIX_HOSTS_LOCATION} \
			--volume ${WINDOWS_HOSTS_LOCATION}:${WINDOWS_HOSTS_LOCATION} \
			--name ${APP_NAME} \
			${APP_NAME}

test: welcome build ## Run tests
	@docker run \
			--interactive \
			--tty \
			--rm \
			--volume ${PWD}:${APP_DIR} \
			--name ${APP_NAME}-test \
			${APP_NAME} \
			pytest

rmi: ## Remove DNR image
	@if [ '${HAS_IMAGE}' ]; \
		then \
			docker rmi ${APP_NAME} \
		; \
	fi

stop: ## Stop DNR
	@docker stop ${APP_NAME}
