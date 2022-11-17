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
df_vask_toppoppgavene = ner_vask_opplysninger.sladd_tekster(df = fritekstsvar, text_col_input= 'Noe mer du vil si om nettsidene våre?', text_col_output= 'om_nettsidene_vasket')
df_vask_toppoppgavene
# %%
