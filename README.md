# AI-Powered Energy Optimization for Java Projects

This project demonstrates automated energy optimization of Java applications using AI. It uses a fork of the [txtmark](https://github.com/rjeschke/txtmark) project as a use case for illustrative and educational purposes.

> **Note**: This is for demonstration purposes only and is not intended to criticize the original txtmark developers.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)
- Java (via SDKMAN or other installation method)
- Groovy (via SDKMAN or other installation method)
- Python 3.x
- Docker & Docker Compose
- Git

## Quick Start

> **Important**: This repository contains existing results from previous runs. If you want to run the project fresh, clean it first:
> ```bash
> make clean
> ```

### 1. Setup Environment
```bash
make setup
```

This command will:
- Install required tools via `tool/makefile install`
- Clone the target repository into the `target/` folder
- Build and prepare Docker containers

### 2. Optimization Workflow

Run the following commands in sequence:

```bash
# 1. Generate performance profile
make profile

# 2. Measure baseline energy consumption, then run AI optimization
make energy
# This will first measure energy, then run ./optimise.sh outside Docker
# Save the energy measurement output for comparison

# 3. Run energy measurement again to compare results
make energy
# Compare with baseline to verify improvements
```

> **Important**: Check for error logs between measurements to ensure you're measuring successful runs, not failed executions.

## How It Works

### Performance Profiling
The system runs txtmark on a large text file (`test/shakespeare.txt`) with Java Flight Recorder (JFR) enabled to capture detailed performance metrics.

### AI Analysis & Optimization
1. **Hotspot Detection**: JFR reports are analyzed to identify performance bottlenecks, generating `results/hotspots_profile.json`
2. **AI Analysis**: Claude analyzes the codebase and hotspots using `tools/prompts/analyse.txt`
3. **Code Optimization**: The top 3 hotspots are optimized using `tools/prompts/optimise.txt`

### Energy Measurement
Energy consumption is measured before and after optimization to validate the effectiveness of AI-generated improvements.

## Tools Overview

### JFR Analyzer (`tools/jfr-analyser/`)
A Maven-based Groovy application that analyzes Java Flight Recorder (JFR) files to identify performance hotspots.

**Build System**: Maven with Groovy support
- **Language**: Groovy (compiled with Java 21)
- **Dependencies**: 
  - Apache Groovy 4.0.22
  - Google Gson (JSON processing)
  - PicoCLI (command-line interface)
  - Commons IO (file operations)
- **Build**: Uses GMavenPlus plugin for Groovy compilation and Maven Shade plugin to create fat JAR
- **Main Class**: `JfrProfiler`

**Purpose**: Parses JFR profiling data and generates `hotspots_profile.json` containing the most CPU-intensive methods for AI optimization.

### Claude Usage Monitor (`tools/claude-usage/claude-usage`)
A Groovy script that monitors and calculates Claude API usage costs during the optimization process.

**Build System**: Standalone Groovy script (no build required)
- **Language**: Groovy with Grape dependency management
- **Dependencies**: `groovy-json` for JSON processing
- **Execution**: Runs directly via `#!/usr/bin/env groovy`

**Purpose**: Tracks token usage and calculates costs for different Claude models (including Claude Sonnet 4, Claude 3.5 Sonnet, Opus, and Haiku) based on current pricing tiers.

## Available Make Targets

| Target | Description |
|--------|-------------|
| `setup` | Install tools, clone repository, build Docker |
| `build` | Build Docker containers |
| `run` | Start containers in detached mode |
| `profile` | Generate performance profile inside Docker |
| `energy` | Measure energy consumption in Docker, then run optimization outside |
| `shell` | Access running container shell |
| `status` | Show container status |
| `stop` | Stop all containers |
| `clean` | Remove containers, images, volumes, results, and target folders |
| `restart` | Stop, rebuild, and restart containers |

## Project Structure

```
├── target/              # Cloned txtmark repository
├── tools/               # Optimization and profiling scripts
│   ├── prompts/         # AI prompts for analysis and optimization
│   ├── claude-usage/    # Claude API usage monitoring tool
│   ├── profile.sh       # Performance profiling script
│   ├── measure_carbon.sh # Energy measurement script
│   └── jfr-analyser/    # JFR analysis tools
├── results/             # Generated analysis results and profiles
├── test/                # Test files (shakespeare.txt, etc.)
├── optimise.sh          # Main optimization script (runs outside Docker)
└── docker-compose.yml   # Docker configuration
```