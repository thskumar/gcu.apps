import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF

def app():
    st.header('Program-wise compilation of Results')
    st.text("It get input from ERP as .csv and compiles in terms of - pass, promotted with backlogs and witheld")
    
    # Getting data from the user ====================================================================================
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    col7, col8 = st.columns(2)

    with col1:
        session = st.selectbox("Select session:", options = ["Monsoon","Winter"])
    with col2:
        year = st.selectbox("Select year:",
            options = ["2023","2024", "2025","2026","2027","2028", "2029","2030","2031","2032", "2033","2034"])
    with col3:
        annual_semester = st.selectbox("Select Academic Type (Year/Semester):", options = ["Year","Semester"])
    with col4:
        type = st.selectbox("Select exam type:", options = ["Regular","Repeater"])
    with col5:
        semester = st.selectbox("Select Annual/Semester No.:", options = ["1","2","3","4","5","6","7","8"])
    with col6:
        date = st.text_input("Result declaration date (dd-mm-yyyy):") 
    with col7:
        program = st.text_input("Enter Program:") 
    # End of getting data from user ============================================================================   
    
    info = {"session": session,
            "year":year,
            "program":program,
            "semester":semester,
            "type":type,
            "date":date,
            "annual_semester":annual_semester}
    
    #st.write(info["annual_semester"])
    #st.write(info["program"])
    # This section processes the leave data from ERP
    
    # Get input data in .CSV format
    uploaded_file = st.file_uploader("Upload the result in CSV format", key=1)  # , key=key)  #key=f"{key}"
    # encoding='utf-8', encoding="ISO-8859-1", engine="openpyxl"
    if uploaded_file is not None:
        result = pd.read_csv(uploaded_file, encoding="ISO-8859-1", skiprows=6)  #key=count
    else:
        return None
    #result = result[5:]
    result = result[:-6]
    #st.write(result.shape)
    #st.write(result.head())
    #st.write(result.tail())
    
    # Extract course code from course variant
    result['course code'] = result['Course Variant'].apply(lambda x: str(x).split('-')[0])
    
    # delete columns
    cols_to_delete = ['Serial No.', 'Course Name', 'Course Variant','Assessment Scheme','Admission ID','Maximum Grades',  \
                  'Effective Marks', 'Grade Obtained','German Grade Scale', 'Grade Point', 'Section Wise Course Rank', 'Course Rank']
    result = result.drop(cols_to_delete, axis=1)
    
    # groups the dataset w.r.t to Students name and picks the first entries
    result['Maximum Marks'] = pd.to_numeric(result['Maximum Marks'], errors='coerce')
    result['Obtained Marks'] = pd.to_numeric(result['Obtained Marks'], errors='coerce')
    result_obtained_marks = result.groupby('Student ID').agg({'Obtained Marks': [lambda x: x.iloc[0], 'sum']})
    
    # this section finds all the student with your total obtained marks
    final_result_obtained_marks = pd.DataFrame(result_obtained_marks['Obtained Marks']['sum'])
    final_result_obtained_marks['Student ID']=result_obtained_marks.index
    final_result_obtained_marks.reset_index(drop=True, inplace=True)
    
    # Total marks of the examination
    total_marks = result.groupby('Student ID')['Maximum Marks'].sum()[0]
    
    final_result_obtained_marks['CGPA'] = final_result_obtained_marks['sum']/total_marks*10
    final_result_obtained_marks['CGPA'] = np.round(final_result_obtained_marks['CGPA'],2)
    
    # This gives students with CGPA - single student multiple entries
    final_result_with_cgpa = pd.merge(result,final_result_obtained_marks, how='right', on='Student ID')
    
    # CGPA is being dropped for the time being
    final_result_with_cgpa.drop('CGPA', axis=1, inplace=True)
    
    # FAILED Studnets
    failed_student_multiple = final_result_with_cgpa[final_result_with_cgpa['Status']=='Fail']
    #failed_students = failed_student_multiple[['Student ID','Student Name','CGPA']]
    failed_students = failed_student_multiple[['Student ID','Student Name']]
    failed_students = failed_students.drop_duplicates()
    no_students_failed = len(failed_students)
    
    fail_students_with_subject = failed_student_multiple.groupby(['Student ID'], as_index = False).agg({'course code': ','.join})
    fail_students_with_subject = pd.merge(failed_students,fail_students_with_subject, how='right', on='Student ID') 
    fail_students_with_subject ################## pass parameter to report
    
    # PASSED Students
    passed_student_multiple = final_result_with_cgpa[final_result_with_cgpa['Status']=='Pass']
    
    # This consists of some student who failed in at least one subject
    #passed_failed_students = passed_student_multiple[['Student ID','Student Name','CGPA']]
    passed_failed_students = passed_student_multiple[['Student ID','Student Name']]
    passed_failed_students = passed_failed_students.drop_duplicates()
    final_passed_student = passed_failed_students[~passed_failed_students.apply(tuple,1).isin(failed_students.apply(tuple,1))]
    no_students_passed = len(final_passed_student)
    
    # WITHELD students
    witheld_student = final_result_with_cgpa[final_result_with_cgpa['Status']=='Witheld']
    witheld_student.drop(['Maximum Marks','Obtained Marks','Status','course code','sum'], axis=1, inplace=True)
    witheld_student = witheld_student.drop_duplicates()
    no_students_witheld = len(witheld_student)
    
    total_students_appeared = no_students_passed + no_students_failed + no_students_witheld
 
    info["total students appeared"]= total_students_appeared
    info["students passed"] = no_students_passed
    info["students failed"] = no_students_failed
    info["students witheld"] = no_students_witheld
    info["pass percent"] = np.round(no_students_passed/total_students_appeared*100, 2)
    
    # This section generates the report in PDF
    def create_pdf(info, df_pass, df_fail, df_witheld):
        image_path = '/Users/GUEST123/images/gcu/'
        #pdf_path = '/Users/GUEST123/pdf/gcu results/'
        # The headings and Labels
        gcu = "Girijananda Chowdhury University"
        gcu_address = "Hathkhowapara, Azara, Guwahati, Assam 781017"
        #report_name = "Grade Card"
        #exam_name = f"End Semester Examination, {batch}"
        exam_name = f"End Semester/Annual Examination, {info['session']}, {info['year']} "

        # 1. Set up the PDF doc basics
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)

        # 2. Heading GCU ADDRESS ======================================
        pdf.cell(200, 10, gcu, align='C', ln=True)
        # pdf.ln(20)
        pdf.set_font('Arial', '', 10)
        pdf.cell(200, 5, gcu_address, align='C')
        #pdf.image(image_path + 'logo_circle.png', 10, 8, 25)
        pdf.image('images/logo_circle.png', 10, 8, 25)
        pdf.ln(5)
    
        # 3. Heading Program and Result Statistics details ====================================
        #pdf.cell(200, 5, report_name, align='C', ln=True)
        pdf.cell(200, 5, exam_name, align='C', ln=True) 
        pdf.ln(10)
        pdf.cell(130, 5, f"Program       \t\t\t\t   : {info['program']}", align='L', ln=False)  # , ln=True)
        
        pdf.cell(50, 5, f"{info['annual_semester']}: {info['semester']} ({info['type']})", align='L', ln=True)  # , ln=True)
        pdf.cell(130, 5, f"Total appeared    : {info['total students appeared']}", align='L', ln=False)  # , ln=True)
        pdf.cell(30, 5, f"All Ceared : {info['students passed']}  ", align='L', ln=True)  # , ln=True)
        pdf.cell(40, 5, f"Passed      \t\t\t\t\t     : {info['pass percent']}% ", align='L', ln=True)  # , ln=True)
        pdf.cell(130, 5, f"Witheld   \t\t\t\t\t\t\t\t\t\t   : {info['students witheld']}", align='L', ln=False)  # , ln=True)
        pdf.cell(30, 5, f"Number of students with backlogs: {info['students failed']} ", align='L', ln=True)  # , ln=True)
        pdf.ln(10)
        
        ### print the DataFrame as a table on the PDF ===================================
        output_df_pass_to_pdf(pdf, df_pass, "The following candidate(s) has/have cleared all the course(s)")
        pdf.ln(10)
        
        output_df_fail_to_pdf(pdf, df_fail)
        pdf.ln(10)

        if (info['students witheld'] !=0 ):
            output_df_pass_to_pdf(pdf, df_witheld, "The following candidate(s)'s result has been witheld:")
            pdf.ln(10)
        
        # Controller of Examinations ========================================================== 
        pdf.ln(20)
        pdf.cell(130, 5, f"Date : {info['date']}", align='L', ln=False)  # , ln=True)  {info['program']}
        pdf.cell(50, 5, 'Controller of Examinations', align='L', ln=True)  # , ln=True)
        pdf.cell(120, 5, '', align='L', ln=False)  # , ln=True)
        pdf.cell(50, 5, f'{gcu}, Assam ', align='L', ln=True)  # , ln=True)
        
        pdf.output(f"./output/result.pdf", 'F')
        
    def output_df_pass_to_pdf(pdf, df, label):
        # A cell is a rectangular area, possibly framed, which contains some text
        # Set the width and height of cell
        cell_height = 6
        cell_width_avg = 20  # originally 25; max width seems to be 200
        cell_width_long = 70  # avg-long-vshort-original-short-short-vshort
        cell_width_short = 15  # 23-70-8-25-15-15-8
        cell_width_vshort = 10
        cell_width_original = 35

        #width_sequence = [cell_width_vshort, cell_width_avg, cell_width_long, cell_width_vshort]
        width_sequence = [cell_width_vshort, cell_width_avg, cell_width_long]


        # Select a font as Arial, bold, 8
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(200, 5, f"{label}                                                    ", align='C', ln=True) 
    
        # Loop over to print column names
        cols = ["SL No."]
        cols.extend(df.columns)

        pdf.cell(cell_width_original, cell_height, " ", align='C', border=0)           # this is a ghost cell - blank cell
        for width, col in zip(width_sequence, cols):
            pdf.cell(width, cell_height, col, align='C', border=1)

        # Line break
        pdf.ln(cell_height)
        # Select a font as Arial, regular, 10
        pdf.set_font('Arial', '', 7)

        # Loop over to print each data in the table
        for row in range(0, len(df)):
            sl_flag = 1
            pdf.cell(cell_width_original, cell_height, " ", align='C', border=0)       # this is a ghost cell - blank cell
            for width, col in zip(width_sequence, cols):
                if sl_flag == 1:
                    value = str(row+1)
                else:
                    value = str((df.iloc[row][col]))
                pdf.cell(width, cell_height, value, align='L', border=1)
                sl_flag = 0
            pdf.ln()
            
    def output_df_fail_to_pdf(pdf, df):
        # A cell is a rectangular area, possibly framed, which contains some text
        # Set the width and height of cell
        cell_height = 6
        cell_width_avg = 16  # originally 25; max width seems to be 200
        cell_width_long = 130  # avg-long-vshort-original-short-short-vshort
        cell_width_short = 15  # 23-70-8-25-15-15-8
        cell_width_vshort = 7
        cell_width_original = 33

        #width_sequence = [cell_width_vshort, cell_width_avg, cell_width_original, cell_width_vshort, cell_width_long]
        width_sequence = [cell_width_vshort, cell_width_avg, cell_width_original, cell_width_long]

        # Select a font as Arial, bold, 8
        pdf.set_font('Arial', 'B', 7)
        pdf.cell(200, 5, f"The following candidate(s) has/have not cleared in the particular course(s) shown:                        ", align='C', ln=True) 
    
        # Loop over to print column names
        cols = ["SL."]
        cols.extend(df.columns)

        #pdf.cell(cell_width_avg, cell_height, " ", align='C', border=0)
        for width, col in zip(width_sequence, cols):
            pdf.cell(width, cell_height, col, align='C', border=1)

        # Line break
        pdf.ln(cell_height)
        # Select a font as Arial, regular, 10
        pdf.set_font('Arial', '', 6)

        # Loop over to print each data in the table
        for row in range(0, len(df)):
            sl_flag = 1
            #pdf.cell(cell_width_avg, cell_height, " ", align='C', border=0)
            for width, col in zip(width_sequence, cols):
                if sl_flag == 1:
                    value = str(row+1)
                else:
                    value = str((df.iloc[row][col]))
                pdf.cell(width, cell_height, value, align='L', border=1)
                sl_flag = 0
            pdf.ln()
    
    # Main report generator        
    create_pdf(info, final_passed_student, fail_students_with_subject, witheld_student)
    
    # Non teaching staffs
    with open(f'./output/result.pdf', "rb") as file:
        st.download_button(
            label="Download the result",
            data=file,
            file_name=f'result.pdf',
            mime="application/zip"
        )
