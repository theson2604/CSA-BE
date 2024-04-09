from enum import Enum


class CustomAnalyzer(Enum):
    STANDARD = "standard"
    AUTOCOMPLETE_VI_TEXT = "autocomplete_vi_text"
    AUTOCOMPLETE_EMAIL = "autocomplete_email"
    AUTOCOMPLETE_PHONENUMBER = "autocomplete_phonenumber"
    AUTOCOMPLETE_SEARCH = "autocomplete_search"