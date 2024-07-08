FROM erikvl87/languagetool:6.4

# Add custom CA certificates
ARG CA_CERTIFICATES=""
USER root
RUN mkdir -p /usr/local/share/ca-certificates/ && \
    echo "${CA_CERTIFICATES}" | tee -a /usr/local/share/ca-certificates/custom-user-cert.crt /etc/ssl/certs/ca-certificates.crt && \
    apk add --no-cache ca-certificates && \
    update-ca-certificates

# PostgreSQL support
RUN apk add postgresql-client zip unzip wget \
    && wget https://jdbc.postgresql.org/download/postgresql-42.7.3.jar -P libs --quiet \
    && mkdir -p org/languagetool/server \
    && unzip -p languagetool-server.jar org/languagetool/server/mybatis-config.xml | \
        sed '/^\s*<\/dataSource>/i<property name="driver.prepareThreshold" value="0"\/>' \
        > org/languagetool/server/mybatis-config.xml \
    && zip -u languagetool-server.jar org/languagetool/server/mybatis-config.xml

# Add custom wordlists
COPY scripts/* ./
COPY wordlists /custom-wordlists/
RUN bash add_wordlists.sh

USER 100
