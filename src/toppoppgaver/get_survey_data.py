# %%
from pathlib import Path

import pandas as pd


# %%
def get_survey_questions(dataset_path: Path):
    """
    Get survey questions from a Task analytics survey as a dictionary

    Questions are stored both in the first and second row, so questions have an key representing the question ID and a value representing the text of the question.

    Parameters:
    -----------
    dataset_path: Path
        Path to the dataframe
    dataframe: pd.DataFrame
        A dataframe to be analysed

    Returns
    -------
    questions: a dataframe
    """
    df = pd.read_csv(dataset_path)
    questions = dict(zip(df.columns, df.iloc[0]))
    return questions


# %%
