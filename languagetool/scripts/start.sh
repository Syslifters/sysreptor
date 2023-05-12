#!/bin/bash
set -e

# Default options
# https://languagetool.org/development/api/org/languagetool/server/HTTPServerConfig.html
languagetool_cacheSize=${languagetool_cacheSize:-1000}
languagetool_cacheTTLSeconds=${languagetool_cacheTTLSeconds:-300}
languagetool_pipelineCaching=${languagetool_pipelineCaching:-true}
languagetool_localApiMode=${languagetool_localApiMode:-true}

languagetool_dbDriver=${languagetool_dbDriver:-org.postgresql.Driver}
languagetool_dbPort=${languagetool_dbPort:-5432}
languagetool_dbUrl=jdbc:postgresql://${languagetool_dbHost}:${languagetool_dbPort}/${languagetool_dbName}
unset languagetool_dbHost languagetool_dbPort languagetool_dbName

Java_Xms=${Java_Xms:-256m}
Java_Xmx=${Java_Xmx:-2g}


# Add languagetool options to config file
for varname in ${!languagetool_*}
do
  echo "${varname#'languagetool_'}="${!varname} >> config.properties
done


java \
  -Xms"${Java_Xms}" -Xmx"${Java_Xmx}" \
  -cp 'languagetool-server.jar:libs/*' org.languagetool.server.HTTPServer \
  --config config.properties --port 8010 --public --allow-origin '*'
