# %%
from pathlib import Path

import pandas as pd


# %%
def get_survey_questions(dataframe: pd.DataFrame):
    """
    Get survey questions from a Task analytics survey as a dictionary

    Questions are stored both in the first and second row, so questions have an key representing the question ID and a value representing the text of the question.

    Parameters:
    -----------
    dataframe: pd.DataFrame
        The dataframe you want to extract questions from

    Returns
    -------
    questions: a dictionary containing question IDs and the text of the questions
    """
    df = dataframe
    questions = dict(zip(df.columns, df.iloc[0]))
    return questions


# %%
df = pd.read_csv(Path("../data/final/survey.csv"))
# %%
q = get_survey_questions(df)


# %%
def return_open_answers(dataframe: pd.DataFrame):
    """
    Returns all variables containing open ended answers

    In Task analytics all variables with the following suffix contain open-ended answers

    .comment

    .freetext

    _o
    """
    df = dataframe
    answers = [i for i in df.columns if i.startswith("answers")]
    openended = [
        x
        for x in answers
        if x.startswith("answers.comment")
        or x.startswith("answers.freetext")
        or x.endswith("_o")
    ]
    return openended


# %%
def clean_survey_headers(dataframe: pd.DataFrame):
    """
    TODO write function to clean up first 2 rows of a task analytics survey so it can be used like a regular dataframe

    Replace columns starting with "answers" with the corresponding question? - DF will contain full question titles
    OR
    Drop the second row, keep only question IDs
    """
    df = dataframe
    data = [i for i in df.columns if i.startswith("answers")]
    df.rename(columns={}, inplace=True)
    return df


# %%
def merge_surveys():
    """
    TODO write function to merge surveys with similar questions for comparison
    """