#!/bin/bash
set -e

for lang in "de" "en"; do
  for file in "spelling.txt" "ignore.txt" "prohibited.txt"; do
    echo "" >> org/languagetool/resource/${lang}/hunspell/${file}
    if [[ -f "/custom-wordlists/all/${file}" ]]; then
      cat "/custom-wordlists/all/${file}" >> org/languagetool/resource/${lang}/hunspell/${file}
    fi
    if [[ -f "/custom-wordlists/${lang}/${file}" ]]; then
      cat "/custom-wordlists/${lang}/${file}" >> org/languagetool/resource/${lang}/hunspell/${file}
    fi
  done
done

rm -rf /custom-wordlists/
