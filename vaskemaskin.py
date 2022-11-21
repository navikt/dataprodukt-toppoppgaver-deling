# %%
import pandas as pd

pd.set_option("max_colwidth", 300)

import ner_vask_opplysninger

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
    "Noe mer du vil si om nettsidene våre?",
]
# %%
def kun_fritekstsvar(df, kolonner):
    """
    Lag en dataframe med kun rader som inneholder fritekstsvar
    """
    dikt = dict(zip(kolonner, [df[~df[x].isna()] for x in kolonner]))
    fritekstsvar = pd.concat(dikt.values(), ignore_index=True).drop_duplicates()
    return fritekstsvar


fritekstsvar = kun_fritekstsvar(df, kolonner=kun_fritekst)
# %%
df_vask_toppoppgavene = ner_vask_opplysninger.sladd_tekster(
    df=fritekstsvar,
    ents_list=["PER", "FNR", "TLF", "EPOST", "finne", "andre"],
    ekstra_vask_av_navn=True,
    text_col_input="Noe mer du vil si om nettsidene våre?",
    text_col_output="om_nettsidene_vasket",
)
df_vask_toppoppgavene
# %%
# prøv uten ML kun regex og sladding
df_regex_toppoppgavene = ner_vask_opplysninger.flashtext_sladd(
    df=fritekstsvar,
    text_col_input="Noe mer du vil si om nettsidene våre?",
    text_col_output="om_nettsidene_vasket",
)
df_regex_toppoppgavene
# %%
# vis treff fra NER og sladding
df_vask_treff = ner_vask_opplysninger.flashtext_extract(
    df=fritekstsvar,
    text_col_input="Noe mer du vil si om nettsidene våre?",
    col_output="noe_mer_treff",
)
df_vask_treff
# %%
df_kunspacy = ner_vask_opplysninger.spacy_vask(
    df=fritekstsvar,
    text_col_input="Noe mer du vil si om nettsidene våre?",
    text_col_output="om_nettsidene_vasket",
    ents_list=["PER", "FNR", "TLF", "EPOST", "finne"],
    n_process=1,
    print_progress=True,
)

df_kunspacy
# %%
def fjern_ider(df, col):
    """
    Dersom en tallrekke på 5 eller flere tall er i en string, bytt det ut med TALL
    
    Dersom en tallrekke på 4 tall er med, bytt det ut med ÅR
    """
    df_out = df.copy()
    df_out[col].replace(to_replace="\d{5,}", value="TALL", regex=True, inplace=True)
    df_out[col].replace(to_replace="\d{4}", value="ÅR", regex=True, inplace=True)
    return df_out

df_tørketrommel = fjern_ider(df_vask_toppoppgavene, "om_nettsidene_vasket")
# %%
