FROM erikvl87/languagetool:6.4

USER root
# PostgreSQL support
RUN wget https://github.com/pgjdbc/pgjdbc/releases/download/REL42.7.3/postgresql-42.7.3.jar -P libs --quiet \
    && wget https://github.com/pgjdbc/pgjdbc/archive/refs/tags/REL42.7.3.tar.gz -P /src --quiet \
    && mkdir -p org/languagetool/server \
    && unzip -p languagetool-server.jar org/languagetool/server/mybatis-config.xml | \
        sed '/^\s*<\/dataSource>/i<property name="driver.prepareThreshold" value="0"\/>' \
        > org/languagetool/server/mybatis-config.xml \
    && zip -u languagetool-server.jar org/languagetool/server/mybatis-config.xml

# Add custom wordlists
COPY scripts/* ./
COPY wordlists /custom-wordlists/
RUN /bin/bash add_wordlists.sh

USER 100
