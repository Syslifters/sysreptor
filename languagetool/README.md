# LanguageTool Spellcheck

## Customize Wordlists
You can improve the spell checker without touching the dictionary. 
For single words (no spaces), you can add your words to one of these files:

* spelling.txt: words that the spell checker will ignore and use to generate corrections if someone types a similar word
* ignore.txt: words that the spell checker will ignore but not use to generate corrections
* prohibited.txt: words that should be considered incorrect even though the spell checker would accept them

These files exist for each language. 
Words in file of the `all` directory, will be added to each language.

