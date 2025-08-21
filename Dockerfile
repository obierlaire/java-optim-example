FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV SDKMAN_DIR="/root/.sdkman"
ENV PATH="$PATH:$SDKMAN_DIR/bin"

# Install basic tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    zip \
    unzip \
    build-essential \
    linux-tools-common \
    linux-tools-generic \
    jq \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install codecarbon
RUN pip3 install --break-system-packages codecarbon

# Install async-profiler
RUN ARCH=$(uname -m | sed 's/x86_64/x64/; s/aarch64/arm64/') && \
    OS=$(uname -s | tr '[:upper:]' '[:lower:]') && \
    cd /opt && \
    wget https://github.com/async-profiler/async-profiler/releases/latest/download/async-profiler-4.1-${OS}-${ARCH}.tar.gz && \
    tar -xzf async-profiler-4.1-${OS}-${ARCH}.tar.gz && \
    rm async-profiler-4.1-${OS}-${ARCH}.tar.gz && \
    ln -s /opt/async-profiler-4.1-${OS}-${ARCH}/bin/asprof /usr/local/bin/asprof && \
    ln -s /opt/async-profiler-4.1-${OS}-${ARCH}/lib/libasyncProfiler.so /usr/local/lib/libasyncProfiler.so

# Switch to ubuntu user
# USER ubuntu
ENV SDKMAN_DIR="/home/ubuntu/.sdkman"

# Install SDKMAN as ubuntu user
RUN curl -s "https://get.sdkman.io" | bash

# Install Java versions and tools (default to Java 8 to match former setup)
RUN /bin/bash -c "source $SDKMAN_DIR/bin/sdkman-init.sh && \
    sdk install java 8.0.422-tem && \
    sdk install java 21.0.4-tem && \
    sdk install groovy 4.0.15 && \
    sdk install maven && \
    sdk default java 8.0.422-tem"

# Set up shell to use SDKMAN
RUN echo 'source $SDKMAN_DIR/bin/sdkman-init.sh' >> /home/ubuntu/.bashrc

# Create workspace directory
WORKDIR /workspace

CMD ["/bin/bash"]