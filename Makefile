# Makefile for soccer13 (PS4 HEN)

.PHONY: all build test package validate release clean \
        docker-build docker-run-build docker-run-test docker-run-release docker-run-clean

all: build

build:
	bash scripts/build.sh

test:
	bash scripts/test.sh

package:
	bash scripts/package.sh

validate:
	bash scripts/validate.sh

release:
	bash scripts/release.sh

clean:
	bash scripts/build.sh --clean

# Docker CLI Interface
docker-build:
	docker compose build

docker-run-build:
	docker compose run --rm builder build

docker-run-test:
	docker compose run --rm builder test

docker-run-release:
	docker compose run --rm builder release

docker-run-clean:
	docker compose run --rm builder clean

