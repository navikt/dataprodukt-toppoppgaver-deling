# %%
import logging

import xlsxwriter
import pandas as pd

logging.basicConfig(level=logging.INFO)

# %%
def new_write_sheets(data, sheet_name, path, hide=False, hide_columns=str):
    """
    Write spreadsheets, hide and adjust columns as options

    TO DO
    support multiple ranges of columns to hide
    support multiple dataframes

    Parameters:
    -----------
    data: df, required
        dataframe to write
    sheet_name: string, required
        name of sheet to write
    path: string, required
        path and filename to write to, f.ex data/demo-align.xlsx
    hide: bool, optional
        do you want to hide some columns
    hide_columns: string, optional
        the range of columns to hide, f.ex A:A hides column A, while A:C hides columns A through C
    """
    writer = pd.ExcelWriter(path, engine="xlsxwriter")

    data.to_excel(writer, sheet_name=sheet_name, startrow=1, header=False, index=False)
    workbook = writer.book

    # alignment and font
    cell_format = workbook.add_format({"valign": "vcenter", "align": "left"})
    cell_format.set_align("left")
    cell_format.set_align("vcenter")
    cell_format.set_text_wrap()
    cell_format.set_font_name("Arial")
    cell_format.set_font_size(14)

    # adjust sheet
    worksheet = writer.sheets[sheet_name]
    (max_row, max_col) = df.shape
    column_settings = [{"header": column} for column in df.columns]

    # format table
    worksheet.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})

    worksheet.set_column("A:Z", None, cell_format)
    worksheet.set_column_pixels(0, len(df.columns), 230)
    worksheet.freeze_panes(1, 0)
    if hide == True:
        worksheet.set_column(hide_columns, None, None, {"hidden": 1})
    writer.close()


# %%
df = pd.read_excel("data/demo.xlsx")
# %%
df2 = df.copy()
df2.fillna("", inplace=True)
df2 = df2.reset_index().to_dict(orient="list")
# %%
def make_workbook(data, path, hide=False):
    """
    Create workbook and sheets with custom styling 

    See writing dicts of data using xlsxwriter at https://xlsxwriter.readthedocs.io/working_with_data.html
    """
    # TO DO
    # * Hide multiple columns
    # * Date format conversion
    # * Label categorical and open ended answers
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
    worksheet.freeze_panes(1, 0)  # frys øverste rad
    # legg til tabell for filtrering?
    # worksheet.set_column('A:Z', None, cell_format)

    col_num = 0
    for key, value in data.items():
        worksheet.write(0, col_num, key, header_format)
        worksheet.write_column(1, col_num, value, cell_format)
        col_num += 1
    if hide == True:
        worksheet.set_column("A:A", None, None, {"hidden": 1})
    workbook.close()


# %%
make_workbook(df2, "data/write_dict.xlsx", hide=True)
