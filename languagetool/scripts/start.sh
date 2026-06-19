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

# Add hunspell dictionaries for languages without official LanguageTool support
cat >> config.properties <<'EOF'
lang-sq=Albanian
lang-sq-dictPath=/LanguageTool/org/languagetool/resource/sq_AL/hunspell/sq_AL.dic
lang-bg=Bulgarian
lang-bg-dictPath=/LanguageTool/org/languagetool/resource/bg_BG/hunspell/bg_BG.dic
lang-cs=Czech
lang-cs-dictPath=/LanguageTool/org/languagetool/resource/cs_CZ/hunspell/cs_CZ.dic
lang-hr=Croatian
lang-hr-dictPath=/LanguageTool/org/languagetool/resource/hr_HR/hunspell/hr_HR.dic
lang-hu=Hungarian
lang-hu-dictPath=/LanguageTool/org/languagetool/resource/hu_HU/hunspell/hu_HU.dic
lang-et=Estonian
lang-et-dictPath=/LanguageTool/org/languagetool/resource/et_EE/hunspell/et_EE.dic
lang-lv=Latvian
lang-lv-dictPath=/LanguageTool/org/languagetool/resource/lv_LV/hunspell/lv_LV.dic
lang-lt=Lithuanian
lang-lt-dictPath=/LanguageTool/org/languagetool/resource/lt_LT/hunspell/lt.dic
lang-nb=Norwegian
lang-nb-dictPath=/LanguageTool/org/languagetool/resource/no/hunspell/nb_NO.dic
lang-sr=Serbian
lang-sr-dictPath=/LanguageTool/org/languagetool/resource/sr/hunspell/sr.dic
lang-tr=Turkish
lang-tr-dictPath=/LanguageTool/org/languagetool/resource/tr_TR/hunspell/tr_TR.dic
EOF

# Add languagetool options to config file
env | grep '^languagetool_' | while IFS='=' read -r key value; do
  echo "${key#languagetool_}=${value}" >> config.properties
done

java \
  -Xms"${Java_Xms}" -Xmx"${Java_Xmx}" \
  -cp 'languagetool-server.jar:libs/*' org.languagetool.server.HTTPServer \
  --config config.properties --port 8010 --public --allow-origin '*'
