from django.db import models


class Language(models.TextChoices):
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
    ITALIAN = 'it-IT', True, 'Italian (it-IT)'
    DUTCH = 'nl-NL', True, 'Dutch (nl-NL)'
    DANISH = 'da-DK', True, 'Danish (da-DK)'
    POLISH = 'pl-PL', True, 'Polish (pl-PL)'
    UKRAINIAN = 'uk-UA', True, 'Ukrainian (uk-UA)'
    # RUSSIAN = 'ru-RU', True, 'Russian (ru-RU)'
    ROMANIAN = 'ro-RO', True, 'Romanian (ro-RO)'
    SLOVAK = 'sk-SK', True, 'Slovak (sk-SK)'
    SLOVENIAN = 'sl-SI', True, 'Slovenian (sl-SI)'
    GREEK = 'el-GR', True, 'Greek (el-GR)'
    SWEDISH = 'sv-SE', True, 'Swedish (sv-SE)'

    # Languages without LanguageTool support
    ALBANIAN = 'sq-AL', False, 'Albanian (sq-AL)'
    BULGARIAN = 'bg-BG', False, 'Bulgarian (bg-BG)'
    CROATIAN = 'hr-HR', False, 'Croatian (hr-HR)'
    CZECH = 'cs-CZ', False, 'Czech (cs-CZ)'
    ESTONIAN = 'et-EE', False, 'Estonian (et-EE)'
    FINNISH = 'fi-FI', False, 'Finnish (fi-FI)'
    HUNGARIAN = 'hu-HU', False, 'Hungarian (hu-HU)'
    LATVIAN = 'lv-LV', False, 'Latvian (lv-LV)'
    LITHUANIAN = 'lt-LT', False, 'Lithuanian (lt-LT)'
    MALTESE = 'mt-MT', False, 'Maltese (mt-MT)'
    NORWEGIAN = 'nb-NO', False, 'Norwegian (nb-NO)'
    SERBIAN = 'sr-SP', False, 'Serbian (sr-SP)'
    TURKISH = 'tr-TR', False, 'Turkish (tr-TR)'

    def __new__(cls, value, spellcheck):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.spellcheck = spellcheck
        return obj
