# %%
import json

from pyjstat import pyjstat
import pandas as pd

# %%
def find_substring(substring: str, df):
    """
    Finn rader i en dataframe som inneholder en string
    """
    mask = df.applymap(
        lambda x: substring in x.lower() if isinstance(x, str) else False
    ).to_numpy()
    df_results = df.loc[mask]
    return df_results


# %%
def find_substring_index(substring: str, df):
    """
    Finn index for rader som inneholder en string i en dataframe
    """
    mask = df.applymap(
        lambda x: substring in x.lower() if isinstance(x, str) else False
    ).to_numpy()
    df_results = df.loc[mask]
    return df_results


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
def pyjstat_to_df(filsti):
    """
    Last inn json-stat data fra JSON-fil og konvertér til dataframe
    """
    with open(filsti, "r") as f:
        j = json.load(f)
        s = json.dumps(j)
        dataset = pyjstat.Dataset.read(s)
        df = dataset.write("dataframe")
    return df


# %%
fornavn = pyjstat_to_df("data/final/fornavn.json")

# %%
fornavn_liste = list(set(fornavn["fornavn"]))
fornavn_liste_små = [x.lower() for x in fornavn_liste]
fornavn_pattern = "|".join([f"(?i){navn}" for navn in fornavn_liste])
# %%
etternavn = pyjstat_to_df("data/final/etternavn.json")

# %%
etternavn = etternavn[
    ~etternavn["etternavn"].isin(["A-F", "G-K", "L-R", "S-Å"])
]  # drop alfabetrekken
etternavn_liste = list(set(etternavn["etternavn"]))
etternavn_liste_små = [x.lower() for x in etternavn_liste]
etternavn_pattern = "|".join([f"(?i){navn}" for navn in etternavn_liste])
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
len(fritekstsvar) / len(df)  # andel svar med fritekst
# %%
def finn_personer(df):
    """
    Finn rader som kan inneholde personopplysninger og returnér en dataframe med treff
    """
    dfs = []
    df_mvh = find_substring("mvh", df)
    df_hilsen = find_substring("hilsen", df)
    df_epost = find_substring("@", df)
    df_tlfnummer = find_substring_regex(r"^((0047)?|(\+47)?)[4|9]\d{7}$", df, False)
    df_tlfnummer_space = find_substring_regex(r"^[4|9]\d{2} \d{2} \d{3}$", df, False)
    dfs.append(df_mvh)
    dfs.append(df_hilsen)
    dfs.append(df_epost)
    dfs.append(df_tlfnummer)
    dfs.append(df_tlfnummer_space)
    df2 = pd.concat(dfs).drop_duplicates()
    return df2


# %%
df2 = finn_personer(fritekstsvar)
len(df2)  # antall rader som inneholder navn, tlf eller epost med hilsen
# %%
(
    len(df2) / len(df)
) * 100  # andel svar i undersøkelsen som inneholder personopplysninger
# %%
