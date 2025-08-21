.PHONY: setup build run stop shell clean profile energy

REPO_TARGET="https://github.com/obierlaire/txtmark.git"

# Setup environment: install tools, clone repository, and prepare Docker
setup:
	tool/makefile install
	git clone $(REPO_TARGET) target
	docker-compose build

# Build the Docker image
build:
	docker-compose build

# Run the container in detached mode
run:
	docker-compose up -d

# Stop the container
stop:
	docker-compose down

# Shell into the running container
shell:
	docker-compose exec java-optim /bin/bash

# Clean up everything (remove containers, images, volumes, results, and target folder)
clean:
	docker-compose down -v --rmi all
	rm -rf results target

# Rebuild and run
restart: stop build run

# Show container status
status:
	docker-compose ps

# Run profiling script inside Docker container
profile:
	docker-compose exec java-optim /workspace/tools/profile.sh

# Run energy measurement in Docker, then optimization outside
energy:
	docker-compose exec java-optim /workspace/tools/measure_carbon.sh
	./optimise.sh