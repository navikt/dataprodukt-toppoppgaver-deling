# %%
import os
import json
from pathlib import Path
import logging

import pandas as pd
from dotenv import load_dotenv
from taskanalytics_data_wrapper.taskanalytics_api import download_survey

from navn import hent_fornavn, hent_etternavn, pyjstat_to_df
import ner_vask_opplysninger as ner
from pretty_sheets import make_workbook, transform_dataframe_to_dict
from get_survey_data import (
    get_survey_questions,
    return_open_answers,
    label_questions,
)

# %%
load_dotenv()
email = os.getenv("ta_email")
password = os.getenv("ta_password")
organization = os.getenv("ta_organization")


# %%
def hent_navn():
    """
    Hent lister med fornavn og etternavn fra SSB
    """
    df = hent_fornavn()
    with open("../../data/final/fornavn.json", "w", encoding="utf-8") as f:
        json.dump(df.json(), f, ensure_ascii=False)
    df = hent_etternavn()
    with open("../../data/final/etternavn.json", "w", encoding="utf-8") as f:
        json.dump(df.json(), f, ensure_ascii=False)


def forbered_navn():
    """
    Slår sammen fornavn og etternavn fra SSB og fjerner unntak
    """
    fornavn = pyjstat_to_df(Path("../../data/final/fornavn.json"))
    fornavn_unik = [_ for _ in fornavn["fornavn"].unique()]
    fornavn_små = [item.lower() for item in fornavn_unik]
    etternavn = pyjstat_to_df(Path("../../data/final/etternavn.json"))
    etternavn = etternavn[
        ~etternavn["etternavn"].isin(["A-F", "G-K", "L-R", "S-Å"])
    ]  # drop alfabetrekken
    etternavn_unik = [_ for _ in etternavn["etternavn"].unique()]
    etternavn_små = [item.lower() for item in etternavn_unik]
    navn = fornavn_små + etternavn_små
    # ignorer navn som forveksles med substantiv og verb
    with open("../patterns/unntak.txt") as f:
        unntak = [line.rstrip() for line in f]
    navn = [n for n in navn if n not in unntak]
    return navn


# %%
def kun_fritekstsvar(df, kolonner):
    """
    Lag en dataframe med kun rader som inneholder fritekstsvar
    """
    fritekst = dict(zip(kolonner, [df[~df[x].isna()] for x in kolonner]))
    fritekstsvar = pd.concat(fritekst.values(), ignore_index=True).drop_duplicates()
    return fritekstsvar


# %%
def vask_urler(df, urler=list):
    """
    vask urler i en dataframe. send inn en dataframe og en liste med variabelnavn som inneholder URLer.
    """
    for i in urler:
        df[i].replace(
            to_replace=r"[0-9a-z.-]{36}", value="ANONYMISERT", regex=True, inplace=True
        )
        df[i].replace(
            to_replace=r"\d{5,}", value="ANONYMISERT", regex=True, inplace=True
        )
    return df


# %%
def runde_timer(df, tid=list):
    """
    Aggreger til nærmeste time
    """
    for i in tid:
        df[i] = pd.to_datetime(df[i])
        df[i] = df[i].dt.round("H")
    return df


# %%
def find_substring_regex(regex: str, df, case=False):
    """
    Finn rader i en dataframe der innholdet matcher regulæruttrykket
    """
    textlikes = df.select_dtypes(include=[object, "string"])
    return df[
        textlikes.apply(
            lambda column: column.str.contains(regex, regex=True, case=case, na=False)
        ).any(axis=1)
    ]


# %%
def main():
    """
    Kjører hele programmet i flere steg
    * Laster ned svarene fra spørreundersøkelsen
    * Markerer spørsmålene og svarene som kategoriske eller fritekst
    * Vasker datasettet for kjente navn i SSBs navnelister
    * Vasker datasettet med Name entity recognition (NER) fra Spacy
    * Bytter ut resterende tall som ligner år og beløp
    * Vasker URLer for unike IDer
    * Runder klokkeslett i svarene til nærmeste time
    * Teller treff på navn blant svarene
    * Lager formatert regneark til deling
    """
    logging.info(f"Laster ned navnelister fra SSB 📊")
    hent_navn()
    logging.info(f"Forbereder navnelister for vask")
    navn = forbered_navn()
    logging.info(f"Laster ned svar fra spørreundersøkelsen 💾")
    download_survey(
        username=email,
        password=password,
        survey_id="03381",
        filename="../../data/final/new_survey.csv",
    )
    df = pd.read_csv(Path("../../data/final/new_survey.csv"))
    questions = get_survey_questions(df)
    questions_labelled = label_questions(questions)

    df = df.iloc[1:]
    kun_fritekst = return_open_answers(df)
    kategoriske = list(set(df.columns) - set(kun_fritekst))
    fritekstsvar = kun_fritekstsvar(df, kolonner=kun_fritekst)
    kategorisvar = df[~df.id.isin(fritekstsvar.id)]
    fritekstsvar["inneholder"] = "Ja"
    kategorisvar["inneholder"] = "Nei"
    ny_df = fritekstsvar.copy()
    logging.info("Vask datasettet 🧹")
    for i, v in enumerate(kun_fritekst, start=1):
        logging.info(f"Vasker nå spørsmål nr {i}: {v}")
        ny_df = ner.sladd_tekster(
            df=ny_df,
            ents_list=["PER", "FNR", "TLF", "EPOST", "finne", "andre"],
            ekstra_vask_av_navn=True,
            text_col_input=v,
            term_liste=navn,
        )
    logging.info(f"Datasettet er vasket og klart til å hentes 🧼 🪣")
    # fjern tall som kan representere år, tlfnr eller beløp
    for i in kun_fritekst:
        ny_df[i].replace(to_replace="\d{5,}", value="TALL", regex=True, inplace=True)
    for i in kun_fritekst:
        ny_df[i].replace(to_replace="\d{4}", value="ÅR", regex=True, inplace=True)
    # slå sammen med kategorisvar
    siste = pd.concat([ny_df, kategorisvar], ignore_index=True)
    siste = vask_urler(df=siste, urler=["startUrl", "doneUrl"])
    siste = runde_timer(df=siste, tid=["start", "complete", "done"])

    treff = find_substring_regex(r"\s(PER|FNR|TLF|EPOST)\s", siste)

    logging.info(
        f"Andelen fritekstsvar av alle svar er {len(fritekstsvar) / len(siste) * 100:.3f}%"
    )
    logging.info(
        f"Andelen svar som inneholder treff på NER er {len(treff) / len(siste) * 100:.3f}%"
    )
    logging.info(
        f"Andelen treff blant alle fritekstsvar er {len(treff)/len(fritekstsvar) * 100:.3f}%"
    )

    new_ids = range(1, len(siste) + 1)
    siste["id"] = new_ids
    siste.columns = [
        f"{i} fritekst" if i not in kategoriske else f"{i} kategori"
        for i in siste.columns
    ]
    siste.columns
    siste.rename(
        columns=dict(zip(siste.columns, questions_labelled)), inplace=True
    )  # rename columns after categorization and cleaning

    df2 = transform_dataframe_to_dict(siste)

    make_workbook(
        data=df2,
        path=Path("../../data/write_dict.xlsx"),
        autofilter=True,
        last_row=len(siste),
        last_col=len(siste.columns),
        hide=True,
        hide_columns=["B:E", "AB:AG"],
        background_color="#F8F1EC",
    )
    logging.info(f"Regnearket er klart 🧺")


if __name__ == "__main__":
    main()

# %%
