# %%
import os
import re

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
df = pd.read_excel("data/final/merged.xlsx")
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
df2 = finn_personer(df)
len(df2)  # antall rader som inneholder navn, tlf eller epost med hilsen
# %%
(len(df2) / len(df))*100 # andel svar i undersøkelsen som inneholder personopplysninger
# %%
