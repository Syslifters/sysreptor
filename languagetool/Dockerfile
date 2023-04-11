FROM erikvl87/languagetool:6.0-dockerupdate-3@sha256:e458281667850c4817fa91d718dbd18d0cf70460323fa561e6e77e0cd07e80a8

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
