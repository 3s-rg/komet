CERTS_DIR := $(PWD)/certs
FRED_VERSION := 0.2.19

.PHONY: all simulation

all: simulation

simulation: simple-full.zip iot-full.zip iot-extreme.zip cdn-full.zip
	./simulation.py

%.zip: %.toml
	@docker run --rm -v $(PWD):/app satgen-docker /app/$< /app/$@
