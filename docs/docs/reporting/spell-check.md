# Spell Check
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

We provide spell checking via the Open Source version of [LanguageTool](https://github.com/languagetool-org/languagetool). Language Tool runs isolated from other processes in separate container. The application reaches LanguageTool via REST-API.

## Add Words to Dictionary
Users can add words to the LanguageTool dictionary.

<figure markdown>
  ![Add to dictionary](/images/add_to_dictionary.png){ width="250" }
  <figcaption>Add to dictionary</figcaption>
</figure>

This updates the dictionary for all users by default. You can configure your installation to add words to a per-user dictionary.  
Per-user dictionaries are not shared between users. When one user adds an unknown word to his dictionary, it will still be unknown for other users. This is even when they are working on the same project and the same finding.

This is an installation-wide setting. It cannot be configured per user or project.

:octicons-cloud-24: Cloud · Please [contact us](https://docs.syslifters.com/contact-us/){ target=_blank } and we will reconfigure your installation.

:octicons-server-24: Self-Hosted · Set the `SPELLCHECK_DICTIONARY_PER_USER` in your `app.env` to true.