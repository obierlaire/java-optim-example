.PHONY: install profile carbon clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  install  - Build and install JFR analyzer"
	@echo "  profile  - Run JFR profiling and analysis"
	@echo "  carbon   - Run carbon footprint measurement"
	@echo "  optimise - Optimise code with AI"
	@echo "  clean    - Clean build artifacts"
	@echo "  help     - Show this help message"

# Build and install JFR analyzer
install:
	@echo "🔨 Installing JFR analyzer..."
	./install.sh

# Run JFR profiling
profile:
	@echo "🚀 Running JFR profiling..."
	./profile.sh

# Optimise
optimise:
	@echo "🚀 Optimising..."
	./optimise.sh

# Run carbon measurement
carbon:
	@echo "🌱 Running carbon measurement..."
	./measure_carbon.sh

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf jfr-analyser/target/
	rm -f ../results/profile.jfr
	rm -f ../results/hotspots_*.json