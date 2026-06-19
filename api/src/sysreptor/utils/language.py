from django.db import models


class Language(models.TextChoices):
    # Languages with good spellcheck support in LanguageTool
    ENGLISH_US = 'en-US', True, 'English (en-US)'
    ENGLISH_GB = 'en-GB', True, 'English (en-GB)'
    ENGLISH_AU = 'en-AU', True, 'English (en-AU)'
    ENGLISH_CA = 'en-CA', True, 'English (en-CA)'
    ENGLISH_NZ = 'en-NZ', True, 'English (en-NZ)'
    ENGLISH_ZA = 'en-ZA', True, 'English (en-ZA)'
    GERMAN_DE = 'de-DE', True, 'German (de-DE)'
    GERMAN_AT = 'de-AT', True, 'German (de-AT)'
    GERMAN_CH = 'de-CH', True, 'German (de-CH)'
    SPANISH = 'es-ES', True, 'Spanish (es-ES)'
    FRENCH_FR = 'fr-FR', True, 'French (fr-FR)'
    FRENCH_CA = 'fr-CA', True, 'French (fr-CA)'
    FRENCH_BE = 'fr-BE', True, 'French (fr-BE)'
    FRENCH_CH = 'fr-CH', True, 'French (fr-CH)'
    PORTUGUESE_PT = 'pt-PT', True, 'Portuguese (pt-PT)'
    PORTUGUESE_BR = 'pt-BR', True, 'Portuguese (pt-BR)'
    DUTCH = 'nl-NL', True, 'Dutch (nl-NL)'

    # Languages with basic spellcheck support in LanguageTool
    ITALIAN = 'it-IT', True, 'Italian (it-IT)'
    DANISH = 'da-DK', True, 'Danish (da-DK)'
    POLISH = 'pl-PL', True, 'Polish (pl-PL)'
    UKRAINIAN = 'uk-UA', True, 'Ukrainian (uk-UA)'
    # RUSSIAN = 'ru-RU', True, 'Russian (ru-RU)'
    ROMANIAN = 'ro-RO', True, 'Romanian (ro-RO)'
    SLOVAK = 'sk-SK', True, 'Slovak (sk-SK)'
    SLOVENIAN = 'sl-SI', True, 'Slovenian (sl-SI)'
    GREEK = 'el-GR', True, 'Greek (el-GR)'
    SWEDISH = 'sv-SE', True, 'Swedish (sv-SE)'

    # Languages without official LanguageTool support, but supported via hunspell dictionaries
    ALBANIAN = 'sq-AL', 'sq', 'Albanian (sq-AL)'
    BULGARIAN = 'bg-BG', 'bg', 'Bulgarian (bg-BG)'
    CROATIAN = 'hr-HR', 'hr', 'Croatian (hr-HR)'
    CZECH = 'cs-CZ', 'cs', 'Czech (cs-CZ)'
    ESTONIAN = 'et-EE', 'et', 'Estonian (et-EE)'
    HUNGARIAN = 'hu-HU', 'hu', 'Hungarian (hu-HU)'
    LATVIAN = 'lv-LV', 'lv', 'Latvian (lv-LV)'
    LITHUANIAN = 'lt-LT', 'lt', 'Lithuanian (lt-LT)'
    NORWEGIAN = 'nb-NO', 'nb', 'Norwegian (nb-NO)'
    SERBIAN = 'sr-SP', 'sr', 'Serbian (sr-SP)'
    TURKISH = 'tr-TR', 'tr', 'Turkish (tr-TR)'

    # Languages without spellcheck support
    FINNISH = 'fi-FI', False, 'Finnish (fi-FI)'
    MALTESE = 'mt-MT', False, 'Maltese (mt-MT)'

    def __new__(cls, value, spellcheck):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.spellcheck = bool(spellcheck)
        obj.spellcheck_code = value if spellcheck is True else None if spellcheck is False else spellcheck
        return obj
