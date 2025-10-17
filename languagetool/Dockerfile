ARG LANGUAGETOOL_VERSION=6.7
ARG PROD_LANGUAGETOOL_IMAGE=languagetool

FROM --platform=$BUILDPLATFORM debian:bookworm-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openjdk-17-jdk-headless \
        git \
        maven \
        unzip

ARG LANGUAGETOOL_VERSION
RUN git clone https://github.com/languagetool-org/languagetool.git --depth 1 -b v${LANGUAGETOOL_VERSION}
WORKDIR /languagetool

# Add PostgreSQL support and build languagetool
RUN sed -i '/^\s*<\/dataSource>/i<property name="driver.prepareThreshold" value="0"\/>' languagetool-server/src/main/resources/org/languagetool/server/mybatis-config.xml \
    && sed -i '/^\s*<\/dependencies>/i<dependency>\n<groupId>org.postgresql<\/groupId>\n<artifactId>postgresql<\/artifactId>\n<version>42.7.8<\/version>\n<\/dependency>' languagetool-server/pom.xml \
    && mvn --projects languagetool-standalone --also-make package -DskipTests \
    && unzip /languagetool/languagetool-standalone/target/LanguageTool-${LANGUAGETOOL_VERSION}.zip -d /dist \
    && mv /dist/LanguageTool-${LANGUAGETOOL_VERSION} /dist/LanguageTool

# Add scripts and custom wordlists
WORKDIR /dist/LanguageTool
COPY scripts/* .
COPY wordlists /custom-wordlists/
RUN ./add_wordlists.sh


FROM alpine:3.22 AS languagetool

RUN apk add --no-cache \
    curl \
    libc6-compat \
    libhunspell \
    openjdk17-jre-headless \
    zip
RUN addgroup --system languagetool \
    && adduser --system --uid=100 -G languagetool languagetool
COPY --chown=languagetool --from=build /dist/LanguageTool /LanguageTool
WORKDIR /LanguageTool

# Hunspell arm64 workaround
RUN if [ "$(uname -m)" = "aarch64" ]; then \
      mkdir -p /hunspell/linux-aarch64/ \
      && cp /usr/lib/libhunspell-1.7.so.0.0.1 /hunspell/linux-aarch64/libhunspell.so \
      && cd /hunspell \
      && zip /LanguageTool/libs/hunspell.jar linux-aarch64/libhunspell.so \
      && rm -rf /hunspell; \
    fi

USER 100
EXPOSE 8010
HEALTHCHECK --timeout=10s --start-period=5s CMD curl --fail --data "language=en-US&text=a simple test" http://localhost:8010/v2/check || exit 1
CMD ["/LanguageTool/start.sh"]


FROM ${PROD_LANGUAGETOOL_IMAGE} AS languagetool-src
RUN git clone https://github.com/languagetool-org/languagetool.git --depth 1 -b v${LANGUAGETOOL_VERSION} /languagetool-src


FROM languagetool