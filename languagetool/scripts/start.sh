#!/bin/sh
set -e

# Default options
# https://languagetool.org/development/api/org/languagetool/server/HTTPServerConfig.html
export languagetool_cacheSize=${languagetool_cacheSize:-1000}
export languagetool_cacheTTLSeconds=${languagetool_cacheTTLSeconds:-300}
export languagetool_pipelineCaching=${languagetool_pipelineCaching:-true}
export languagetool_localApiMode=${languagetool_localApiMode:-true}

export languagetool_dbDriver=${languagetool_dbDriver:-org.postgresql.Driver}
export languagetool_dbPort=${languagetool_dbPort:-5432}
export languagetool_dbUrl=jdbc:postgresql://${languagetool_dbHost}:${languagetool_dbPort}/${languagetool_dbName}
unset languagetool_dbHost languagetool_dbPort languagetool_dbName

Java_Xms=${Java_Xms:-256m}
Java_Xmx=${Java_Xmx:-2g}


# Add languagetool options to config file
env | grep '^languagetool_' | while IFS='=' read -r key value; do
  echo "${key#languagetool_}=${value}" >> config.properties
done


java \
  -Xms"${Java_Xms}" -Xmx"${Java_Xmx}" \
  -cp 'languagetool-server.jar:libs/*' org.languagetool.server.HTTPServer \
  --config config.properties --port 8010 --public --allow-origin '*'
