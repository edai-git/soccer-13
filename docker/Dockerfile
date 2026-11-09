# docker/Dockerfile — 100% Reproducible Build Environment for soccer13 (PS4 HEN)
FROM --platform=linux/amd64 ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55

ARG SNAPSHOT=20261012T000000Z
ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C \
    TZ=UTC \
    SOURCE_DATE_EPOCH=1767225600

# 1. Configure Ubuntu snapshot archive for byte-for-byte reproducibility
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg && \
    sed -i -E "s#^URIs: .*#URIs: https://snapshot.ubuntu.com/ubuntu/$SNAPSHOT/#" /etc/apt/sources.list.d/ubuntu.sources && \
    rm -rf /var/lib/apt/lists/* && apt-get update && \
    ca=$(apt-cache policy ca-certificates | sed -n 's/^ *Candidate: //p') && \
    apt-get install -y --reinstall --allow-downgrades "ca-certificates=$ca" && \
    rm -rf /var/lib/apt/lists/*

# 2. Install LLVM / Clang 19.1.7 (strict requirement for orbis-win ABI-v4)
RUN install -d -m 0755 /etc/apt/keyrings && \
    curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key | tee /etc/apt/keyrings/apt.llvm.org.asc >/dev/null && \
    echo "deb [signed-by=/etc/apt/keyrings/apt.llvm.org.asc] http://apt.llvm.org/noble/ llvm-toolchain-noble-19 main" \
      > /etc/apt/sources.list.d/llvm-19.list && \
    printf 'Package: *\nPin: release o=apt.llvm.org\nPin-Priority: 1001\n' \
      > /etc/apt/preferences.d/llvm-19 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      clang-19 lld-19 llvm-19 libclang-rt-19-dev && \
    for tool in clang clang++ lld ld.lld llvm-ar llvm-ranlib llvm-nm \
                llvm-objcopy llvm-readelf llvm-strip; do \
      ln -sfn "/usr/bin/${tool}-19" "/usr/local/bin/$tool"; \
    done && \
    clang --version | grep -q '19\.' && \
    rm -rf /var/lib/apt/lists/*

# 3. Install core build tools, MinGW-w64 cross-compilers, and host Wine libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential cmake ninja-build meson pkg-config bison flex gettext perl \
      git lftp curl wget zip unzip file patch rsync \
      python3 python3-pip python3-venv python3-yaml \
      gcc-mingw-w64-i686 gcc-mingw-w64-x86-64 g++-mingw-w64-i686 g++-mingw-w64-x86-64 \
      glslang-tools spirv-tools \
      libx11-dev libxext-dev libfreetype-dev libfontconfig-dev libvulkan-dev \
      libgnutls28-dev libasound2-dev libpulse-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# 4. Install isolated OpenSSL 1.1 runtime required by OpenOrbis PkgTool.Core
RUN mkdir -p /opt/openssl11/lib && \
    cd /tmp && \
    curl -fsSL -o libssl1.1.deb http://security.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.24_amd64.deb || \
    curl -fsSL -o libssl1.1.deb https://snapshot.ubuntu.com/ubuntu/20240408T000000Z/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.20_amd64.deb || true && \
    if [ -f libssl1.1.deb ]; then \
      dpkg-deb -x libssl1.1.deb /tmp/ssl-extract && \
      cp -a /tmp/ssl-extract/usr/lib/x86_64-linux-gnu/* /opt/openssl11/lib/ || true && \
      rm -rf /tmp/ssl-extract libssl1.1.deb; \
    fi

# 5. Setup workspace directories, user compatibility links, and git safe directory
RUN mkdir -p /workspace /cache /home/zpeirce && \
    ln -sfn /workspace/runtime/orbis-win /home/zpeirce/ps4-gladius && \
    git config --system --add safe.directory '*'

WORKDIR /workspace

ENV PS4_PKGTOOL_OPENSSL_LIB=/opt/openssl11/lib \
    LD_LIBRARY_PATH=/opt/openssl11/lib:${LD_LIBRARY_PATH:-} \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

CMD ["/bin/bash"]

