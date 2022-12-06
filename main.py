# %%
import logging

import pandas as pd

import ner_vask_opplysninger

pd.set_option("max_colwidth", 300)

# %%
df = pd.read_excel("data/final/merged.xlsx")
# %%
kun_fritekst = [
    "Hva kom du til nettstedet for? other",
    "Hvorfor ikke? other",
    "Hva er situasjonen din? other",
    "Hva ville du søke om? other",
    "Hvem er du? other",
    "Hva vil du gjøre i stedet? other",
    "Fortell oss om hva som er vanskelig",
    "Hva ville du finne statistikk, analyse eller forskning om?",
    "Hva prøvde du å finne informasjon om?",
    "Noe mer du vil si om nettsidene våre?"
]
kategoriske = list(set(df.columns) - set(kun_fritekst))
# %%
def kun_fritekstsvar(df, kolonner):
    """
    Lag en dataframe med kun rader som inneholder fritekstsvar
    """
    fritekst = dict(zip(kolonner, [df[~df[x].isna()] for x in kolonner]))
    fritekstsvar = pd.concat(fritekst.values(), ignore_index=True).drop_duplicates()
    return fritekstsvar


fritekstsvar = kun_fritekstsvar(df, kolonner=kun_fritekst)
kategorisvar = (df[~df.id.isin(fritekstsvar.id)])
# %%
ny_df = fritekstsvar.copy()

for i, v in enumerate(kun_fritekst, start=1):
    logging.info(f"Vasker nå spørsmål nr {i}: {v}")
    print(f"Vasker nå spørsmål nr {i}: {v}")
    ny_df = ner_vask_opplysninger.sladd_tekster(
        df=ny_df,
        ents_list=["PER", "FNR", "TLF", "EPOST", "finne", "andre"],
        ekstra_vask_av_navn=True,
        text_col_input=v
    )
logging.info(f"Datasettet er vasket og klart til å hentes")
# %%
# fjern tall som kan representere år, tlfnr eller beløp
for i in kun_fritekst:
    ny_df[i].replace(to_replace="\d{5,}", value="TALL", regex=True, inplace=True)
for i in kun_fritekst:
    ny_df[i].replace(to_replace="\d{4}", value="ÅR", regex=True, inplace=True)
# %%
# slå sammen med kategorisvar
siste = pd.concat([ny_df, kategorisvar], ignore_index=True)
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
treff = find_substring_regex(r"\s(PER|FNR|TLF|EPOST)\s", siste)
# %%
len(treff) / len(siste) * 100 # prosentandel svar med treff på ENTS fra NER