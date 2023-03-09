# %%
import logging

import xlsxwriter

logging.basicConfig(level=logging.INFO)

# %%
def transform_dataframe_to_dict(data):
    """
    Returns a dict from dataframe. Does not modify dataframe.

    Replace all empty cells with empty string
    Convert dtypes from datetime to string
    Drop index column before converting to dict
    """
    df = data.copy()
    df.fillna("", inplace=True)
    df = df.assign(**data.select_dtypes(["datetime"]).astype(str))
    df = df.reset_index().to_dict(orient="list")
    del df["index"]
    return df


# %%
def make_workbook(
    data: dict,
    path: str,
    autofilter=False,
    last_row=0,
    last_col=0,
    hide=False,
    hide_columns=list,
):
    """
    Create workbook and sheets with custom styling

    Supports:

    * Adds autofilter to all columns
    * Freeze top row
    * Hide multiple columns

    See writing dicts of data using xlsxwriter at https://xlsxwriter.readthedocs.io/working_with_data.html

    Parameters:
    ----------
    data: dict, required
        The dictionary to create a workbook from
    path: string, required
        Set path to write the workbook
    autofilter: bool, optional
        Add autofilter to a range of columns in workbook, starting from the first column and row
    last_row: int, required if autofilter is True
        Specify the last row the autofilter is set to
    last_col: int, required if autofilter is True
        Specify the last column the autofilter is set to
    hide: bool, optional
        Set True if you want to hide columns
    hide_columns: list, required if hide is True
        Pass a list of strings representing the range of columns to hide, f.ex 'A:A' hides only column A while 'A:Z' hides all columns from A to Z
    """
    workbook = xlsxwriter.Workbook(path)
    worksheet = workbook.add_worksheet()

    header_format = workbook.add_format(
        {"font_name": "Arial", "font_size": 14, "bold": True}
    )
    header_format.set_text_wrap()
    header_format.set_align("left")
    header_format.set_align("vcenter")

    cell_format = workbook.add_format({"font_name": "Arial", "font_size": 14})
    cell_format.set_text_wrap()
    cell_format.set_align("left")
    cell_format.set_align("vcenter")
    worksheet.set_column_pixels(0, 37, 230)
    worksheet.freeze_panes(1, 0)
    if autofilter == True:
        worksheet.autofilter(0, 0, last_row, last_col)

    col_num = 0
    for key, value in data.items():
        worksheet.write(0, col_num, key, header_format)
        worksheet.write_column(1, col_num, value, cell_format)
        col_num += 1
    if hide == True:
        for i in hide_columns:
            worksheet.set_column(i, None, None, {"hidden": 1})
    workbook.close()
