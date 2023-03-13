FROM erikvl87/languagetool:6.0-dockerupdate-3

# PostgreSQL support
USER root
RUN apk add postgresql-client
RUN wget https://jdbc.postgresql.org/download/postgresql-42.5.4.jar -P libs

COPY scripts/* .
COPY wordlists /custom-wordlists/
RUN bash add_wordlists.sh
USER 100
