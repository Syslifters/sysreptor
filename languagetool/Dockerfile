FROM erikvl87/languagetool:5.9

# Add custom words
USER root
COPY all /custom-wordlists/all/
COPY de /custom-wordlists/de/
COPY en /custom-wordlists/en/
RUN ls -alR /custom-wordlists/ && for lang in "de" "en"; do \
      for file in "spelling.txt" "ignore.txt" "prohibited.txt"; do \
        (echo; cat /custom-wordlists/all/${file}; echo; cat /custom-wordlists/${lang}/${file}) >> org/languagetool/resource/${lang}/hunspell/${file}; \
      done; \
    done
USER 1000
