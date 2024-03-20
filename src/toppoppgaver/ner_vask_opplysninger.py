# %%
import re
import json
import timeit
from pathlib import Path
import logging

import spacy
import numpy as np
from flashtext import KeywordProcessor

logging.basicConfig(level=logging.INFO)

# %%

patterns_folder = Path("../patterns/")

regex_patterns_file = patterns_folder / "regex_patterns.txt"
regex_patterns = json.loads(regex_patterns_file.read_text())
# %%
nlp = spacy.load(
    "nb_core_news_lg",
    exclude=["tok2vec", "morphologizer", "parser", "attribute_ruler", "lemmatizer"],
)
custom_patterns = [
    {"label": "FNR", "pattern": "[FNR]"},
    {"label": "TLF", "pattern": "[TLF]"},
    {"label": "EPOST", "pattern": "[EPOST]"},
    {"label": "finne", "pattern": [{"lower": "finne"}]},
    {"label": "andre", "pattern": [{"lower": "andre"}]},
]
ruler_config = {
    "phrase_matcher_attr": None,
    "validate": True,
    "overwrite_ents": True,
    "ent_id_sep": "||",
}
ruler = nlp.add_pipe("entity_ruler", config=ruler_config)
ruler.add_patterns(custom_patterns)


# %%
def flashtext_sladd(df, text_col_input, term_liste: list, text_col_output=None):
    """Sladding av navn fra SSB-navnelister vha. flashtext

    parameters:
    -----------
    df: pd.dataframe
        pandas dataframen som skal behandles
    text_col_input: str
        Navnet på kolonnen i dataframen med teksten som skal behandles
    term_liste: list
        Liste med begreper som skal vaskes.
    text_col_output: str
        Eventuelt navn på kolonne for vasket tekst.
        Dersom dette ikke angis legges output i text_col_input-kolonnen.

    """
    replacement = "PER"

    # definerer en tom keywordprocessor
    processor = KeywordProcessor(case_sensitive=False)
    # flashtext sin keywordprocessor splitter ord på 'spesielle tegn' - ønsker her å behandle ord med følgende tegn som enkeltord
    processor.non_word_boundaries.add("-")
    processor.non_word_boundaries.add("æ")
    processor.non_word_boundaries.add("ø")
    processor.non_word_boundaries.add("å")

    keyword_dict = {}
    keyword_dict[replacement] = term_liste

    processor.add_keywords_from_dict(keyword_dict)

    # gjør en replace av alle søketermene med den grupperte versjonen av termen
    if text_col_output:
        df[text_col_output] = (
            df[text_col_input].astype(str).apply(processor.replace_keywords)
        )
    else:
        df[text_col_input] = (
            df[text_col_input].astype(str).apply(processor.replace_keywords)
        )

    return df


# %%
def regex_vask_df(df, entity, text_col_input, text_col_output=None):
    """Sladding av entiteter definert av regex-uttrykk

    parameters:
    -----------
    df: pd.dataframe
        pandas dataframen som skal behandles
    entity:
        Hvilken entity som skal sladdes
        (Definert av filen regex_patterns.txt (FNR, TLF eller EPOST))
    text_col_input: str
        Navnet på kolonnen i dataframen med teksten som skal behandles
    text_col_output: str
        Eventuelt navn på kolonne for vasket tekst.
        Dersom dette ikke angis legges output i text_col_input-kolonnen.

    """

    regex_pattern = regex_patterns[entity]["pattern"]
    regex_pat = re.compile(regex_pattern, flags=re.IGNORECASE)
    tag = regex_patterns[entity]["tag"]

    if text_col_output:
        out_col = text_col_output
    else:
        out_col = text_col_input

    df[out_col] = df[text_col_input].replace(regex_pat, tag, regex=True)

    return df


# %%
def spacy_vask(
    df, text_col_input, text_col_output, ents_list, n_process, print_progress
):
    """Sladder bort personopplysninger fra tekst vha. NER.

    parameters:
    -----------
    df: pd.dataframe
        pandas dataframen som skal behandles
    text_col_input: str
        Navnet på kolonnen i dataframen med teksten som skal behandles
    text_col_output: str
        Eventuelt navn på kolonne for vasket tekst.
        Dersom dette ikke angis legges output i text_col_input-kolonnen.
    ents_list: list
        Hvilke enititetstyper som skal hensyntas. Default:
        "PER" - personnavn
        "LOC" - stedsnavn
        "ORG" - organisasjoner/bedriftsnavn

        følgende entiteter antas at er funnet med regex-først:
        "FNR" - fødselsnummer/d-nummer
        "TLF" - telefonnummer
        "EPOST" - epost
    n_process: int
        Antall parallelle prosesser i spacy-prosesseringen
    print_progress: bool
        True om funksjonen skal printe hvor langt den har kommet underveis

    """

    # velger å la tomme tekst-celler få en tom string
    df["temp_text_col"] = df[text_col_input].fillna("")

    if text_col_output:
        out_col = text_col_output
    else:
        out_col = text_col_input

    df[out_col] = np.empty((len(df), 0)).tolist()

    for ind, doc in enumerate(nlp.pipe(df["temp_text_col"], n_process=n_process)):
        if ind % 5000 == 0 and print_progress == True:
            logging.info(f"Nå på tekst nr: {ind} - {min(ind + 5000-1, len(df))}")
        clean_text = df["temp_text_col"].loc[ind]
        for ent in reversed(doc.ents):
            if ent.label_ in ents_list:
                clean_text = (
                    clean_text[: ent.start_char]
                    + ent.label_
                    + clean_text[ent.end_char :]
                )
        df.at[ind, out_col] = clean_text

    df = df.drop(columns=["temp_text_col"])

    return df


# %%
def sladd_tekster(
    df,
    text_col_input,
    term_liste: list,
    ents_list=["PER", "FNR", "TLF", "LOC", "ORG", "EPOST"],
    ekstra_vask_av_navn=True,
    n_process=1,
    print_progress=True,
    text_col_output=None,
):
    """Sladding av entiteter i fritekst.

    Utfører følgende steg:
    1. regelbasert sladding (regex)
    2. NER-sladding (spacy)
    3. listebasert sladding (navn fra SSB)

    parameters:
    -----------
    df: pd.dataframe
        pandas dataframen som skal behandles
    text_col_input: str
        Navnet på kolonnen i dataframen med teksten som skal behandles
    ents_list: list
        Hvilke enititetstyper som skal hensyntas
            "FNR" - fødselsnummer/d-nummer (regex)
            "TLF" - telefonnummer (regex)
            "EPOST" - epostadresser (regex)
            "PER" - personnavn (spacy + SSB-liste)
            "LOC" - stedsnavn (spacy)
            "ORG" - organisasjoner/bedriftsnavn (spacy)
    term_liste: list
        Liste med begreper som skal vaskes. Videresendes til flashtext_sladd.
    ekstra_vask_av_navn: bool
        True om funksjonen skal kjøre SSB-navnevask i tillegg til NER
    n_process: int
        Antall parallelle prosesser i spacy-prosesseringen
    print_progress: bool
        True om funksjonen skal printe hvor langt den har kommet underveis
    text_col_output: str
        Eventuelt navn på kolonne for vasket tekst.
        Dersom dette ikke angis legges output i text_col_input-kolonnen.
    """
    start = timeit.default_timer()

    if print_progress == True:
        logging.info(f"**Tokenisering og vasking for {len(df)} tekster**")
        logging.info("Starter vasking av følgende entiteter")
        logging.info(
            [
                ent
                for ent in ents_list
                if ent in ["PER", "FNR", "TLF", "LOC", "ORG", "EPOST"]
            ]
        )

    # re-indekserer dataframen for å være sikker på at hver indeksverdi er unik
    df = df.reset_index(drop=True)

    df["temp_text_col"] = df[text_col_input]
    if text_col_output:
        out_col = text_col_output
    else:
        out_col = text_col_input

    # entitetstyper som håndteres med regex først:
    if "FNR" in ents_list:
        if print_progress == True:
            logging.info(f"Kjører regex for FNR...")
        df = regex_vask_df(df, entity="FNR", text_col_input="temp_text_col")
    if "TLF" in ents_list:
        if print_progress == True:
            logging.info(f"Kjører regex for TLF...")
        df = regex_vask_df(df, entity="TLF", text_col_input="temp_text_col")
    if "EPOST" in ents_list:
        if print_progress == True:
            logging.info("Kjører regex for EPOST...")
        df = regex_vask_df(df, entity="EPOST", text_col_input="temp_text_col")

    # entitetstyper som håndteres med spacy NER-modell:
    if print_progress == True:
        logging.info("Starter NER...")
    df = spacy_vask(df, "temp_text_col", out_col, ents_list, n_process, print_progress)

    if ekstra_vask_av_navn == True:
        if print_progress == True:
            logging.info("Starter ekstra vask av personnavn mot SSB-lister...")
        df = flashtext_sladd(df=df, text_col_input=out_col, term_liste=term_liste)

    stop = timeit.default_timer()
    if print_progress == True:
        logging.info(f"  {len(df)} tekster vasket på {'%.3f'%(stop - start)} sek")

    return df


# %%
def flashtext_extract(df, text_col_input, term_liste: list, col_output=None):
    """Uttrekk av treff på navn fra SSB-navnelister vha. flashtext

    parameters:
    -----------
    df: pd.dataframe
        pandas dataframen som skal behandles
    text_col_input: str
        Navnet på kolonnen i dataframen med teksten som skal behandles
    term_liste: list
        Liste med begreper som skal vaskes.
    col_output: str
        Eventuelt navn på kolonne for vasket tekst.
        Dersom dette ikke angis legges output i text_col_input-kolonnen.

    """

    # definerer en tom keywordprocessor
    processor = KeywordProcessor(case_sensitive=False)
    # flashtext sin keywordprocessor splitter ord på 'spesielle tegn' - ønsker her å behandle ord med følgende tegn som enkeltord
    processor.non_word_boundaries.add("-")
    processor.non_word_boundaries.add("æ")
    processor.non_word_boundaries.add("ø")
    processor.non_word_boundaries.add("å")

    processor.add_keywords_from_list(term_liste)

    # gjør en replace av alle søketermene med den grupperte versjonen av termen
    if col_output:
        df[col_output] = (
            df[text_col_input]
            .astype(str)
            .apply(lambda x: list(set(processor.extract_keywords(x))))
        )
    else:
        df[text_col_input] = (
            df[text_col_input]
            .astype(str)
            .apply(lambda x: list(set(processor.extract_keywords(x))))
        )

    return df
