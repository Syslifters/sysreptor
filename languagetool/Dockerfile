FROM erikvl87/languagetool:6.1@sha256:15d8cf64b01a15362fdcd4674054fd6b0cb90ab29e515bcf677cd6c65e089d0e

# PostgreSQL support
USER root
RUN apk add postgresql-client zip unzip \
    && wget https://jdbc.postgresql.org/download/postgresql-42.5.4.jar -P libs --quiet \
    && mkdir -p org/languagetool/server \
    && unzip -p languagetool-server.jar org/languagetool/server/mybatis-config.xml | \
        sed '/^\s*<\/dataSource>/i<property name="driver.prepareThreshold" value="0"\/>' \
        > org/languagetool/server/mybatis-config.xml \
    && zip -u languagetool-server.jar org/languagetool/server/mybatis-config.xml

COPY scripts/* .
COPY wordlists /custom-wordlists/
RUN bash add_wordlists.sh
USER 100
