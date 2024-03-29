import streamlit as st
from fpdf import FPDF
import pandas as pd
from datetime import datetime
import zipfile
import numpy as np
import os

def app():
    st.header("Reads students' score and generates score cards in PDFs")
    st.text("The score should be in CSV format")

    # The require paths
    # data_path = '/Users/GUEST123/Data/gcu/results/'
    #results_path = '/Users/GUEST123/pdf/gcu results/'

    uploaded_file = st.file_uploader("Upload the Result data in csv format")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        program_list = df['Program'].unique()
        for program in program_list:
            one_program = df[(program == df['Program'])]  # This extracts records of only one program

            file_names = []
            student_list = one_program['Enrollment No.'].unique()  # This find the students of a program
            for student in student_list:  # Do this for all the students
                one_student = one_program[(one_program['Enrollment No.'] == student)]
                one_student['Remarks'] = one_student['Remarks'].fillna(' ')
                one_student_grade = one_student[
                    ['Course Code', 'Course Name', 'Credit', 'Grade Obtained', 'Grade Point', 'Credit Point', 'Remarks']]
                #create_pdf(one_student, one_student_grade)
                file_names.append(create_pdf(one_student, one_student_grade))

            # Zip the files
            st.write(f"Download zip file for {program}")
            with zipfile.ZipFile(f'temp/{program}.zip', 'w', compression=zipfile.ZIP_DEFLATED) as my_zip:
                for fn in file_names:
                    my_zip.write(f'temp/{fn}')
                    #my_zip.write(f'{fn}')

            # open it as a regular file and supply to the button as shown in the example:
            with open(f'temp/{program}.zip', "rb") as file:
                    st.download_button(
                    label="Download data as ZIP",
                    data=file,
                    file_name=f'{program}.zip',
                    mime="application/zip"
                )
        st.write("Congratulation! Score Card converted to PDFs")
def output_df_to_pdf(pdf, df):
    # A cell is a rectangular area, possibly framed, which contains some text
    # Set the width and height of cell
    cell_height = 6
    cell_width_avg = 20  # originally 25; max width seems to be 200
    cell_width_long = 70  # avg-long-vshort-original-short-short-vshort
    cell_width_short = 15  # 23-70-8-25-15-15-8
    cell_width_vshort = 10
    cell_width_original = 25

    width_sequence = [cell_width_avg, cell_width_long, cell_width_vshort, cell_width_original, cell_width_avg,
                      cell_width_avg, cell_width_short]

    # Select a font as Arial, bold, 8
    pdf.set_font('Arial', 'B', 8)

    # Loop over to print column names
    cols = df.columns

    for width, col in zip(width_sequence, cols):
        pdf.cell(width, cell_height, col, align='C', border=1)

    # Line break
    pdf.ln(cell_height)
    # Select a font as Arial, regular, 10
    pdf.set_font('Arial', '', 8)

    # Loop over to print each data in the table
    for row in range(0, len(df)):
        for width, col in zip(width_sequence, cols):
            value = str((df.iloc[row][col]))
            if width == cell_width_long:
                pdf.cell(width, cell_height, value, align='L', border=1)
            else:
                pdf.cell(width, cell_height, value, align='C', border=1)
        pdf.ln()


def create_pdf(df, df_grades):
    image_path = '/Users/GUEST123/images/gcu/'
    #pdf_path = '/Users/GUEST123/pdf/gcu results/'
    # The headings and Labels
    gcu = "Girijananda Chowdhury University"
    gcu_address = "Hathkhowapara, Azara, Guwahati, Assam 781017"
    report_name = "Grade Card"
    exam_name = "End Semester Examination, Monsoon 2023"

    # 1. Set up the PDF doc basics
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)

    # 2. Layout the PDF doc contents
    pdf.cell(200, 10, gcu, align='C', ln=True)
    # pdf.ln(20)
    pdf.set_font('Arial', '', 10)
    pdf.cell(200, 5, gcu_address, align='C')
    #pdf.image(image_path + 'logo_circle.png', 10, 8, 25)
    pdf.image('images/logo_circle.png', 10, 8, 25)
    pdf.ln(20)

    # Write the report details
    pdf.cell(200, 5, report_name, align='C', ln=True)
    pdf.cell(200, 5, exam_name, align='C', ln=True)
    pdf.ln(10)

    # Get the student's details
    #abc_id = df['ABC ID'].iloc[0]
    if df['ABC ID'].iloc[0] is np.nan:
        abc_id = ' '
    else:
        abc_id = df['ABC ID'].iloc[0]
    enroll_id = df['Enrollment No.'].iloc[0]
    std_name = df['Student Name'].iloc[0]
    program = df['Program'].iloc[0]
    semester = df['Semester'].iloc[0]

    # Calculate SGPA
    credit_point = sum(df_grades['Credit Point'])
    total_credit = sum(df_grades['Credit'])
    SGPA = credit_point / total_credit

    # Get today's date
    #date = datetime.today().strftime('%d-%m-%Y')
    date = '05-01-2024'

    # Write the student's details
    pdf.cell(150, 5,
             f'ABC ID      \t\t\t\t\t\t   : {abc_id}                          \t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t            Date  \t\t\t    : {date}',
             align='L', ln=True)  # , ln=True)
    pdf.cell(150, 5,
             f'Enrollment No. \t\t: {enroll_id}                              \t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t Semester\t: {semester} ',
             align='L', ln=True)  # , ln=True)
    pdf.cell(150, 5, f'Student Name   \t: {std_name}', ln=True)  # , ln=True)
    pdf.cell(150, 5, f'Program       \t\t\t\t\t : {program}', ln=True)  # , ln=True)
    pdf.ln(10)

    ### Use the function defined earlier to print the DataFrame as a table on the PDF
    output_df_to_pdf(pdf, df_grades)
    pdf.ln(5)

    # Calculate totals
    total_credit_earned = sum(df_grades.Credit)
    total_credit_point = sum(df_grades['Credit Point'])
    pdf.set_font('Arial', '', 10)
    pdf.cell(150, 5, f'Total Credit Earned       : {total_credit_earned}', ln=True)
    pdf.cell(150, 5, f'Total Credit Point          : {total_credit_point}', ln=True)
    pdf.cell(150, 5, f'SGPA                            : {SGPA} ', ln=True)

    # Disclaimer
    pdf.ln(5)
    pdf.set_font('Arial', '', 9)
    pdf.cell(150, 5, f'C-Cleared; NC-Not Cleared', ln=True)
    pdf.ln(10)
    pdf.cell(150, 5,
             'Disclaimer: Note that this is a computer generated mark sheet and does not require any signature. At any stage,',
             ln=True)
    pdf.cell(150, 5,
             'if it is found incorrect due to any valid reason, after due verification, this will lead to a change in the grades and ',
             ln=True)
    pdf.cell(150, 5, 'corresponding CGPA and SGPA.', ln=True)

    # Controller
    pdf.ln(20)
    pdf.set_font('Arial', '', 10)
    pdf.cell(160, 5,
             '                                                                                                        Controller',
             'L', ln=True)
    pdf.cell(160, 5, f'                                                                                         {gcu}',
             'RL', ln=True)
    pdf.output(f"temp/{enroll_id}.pdf", 'F')
    return f"{enroll_id}.pdf"
