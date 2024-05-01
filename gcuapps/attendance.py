import streamlit as st
import pandas as pd
import numpy as np
#import xlrd
#import openpyxl
import utility as ut # My utility file


#@st.cache_data
#def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
#    return df.to_csv().encode('utf-8')

def app():
    st.header('Attendance & Leave Calculation of GCU')
    st.text("It combines the output of Biometric data with the leaves sanctioned dataset from ERP")

    # first file reading
    #st.write("Upload the first excel file :")
    uploaded_file = st.file_uploader("Upload the biometric file 1 (GIMT) in excel format", key=1)  # , key=key)  #key=f"{key}"
    if uploaded_file is not None:
        biometric_GCU1 = pd.read_excel(uploaded_file)  # , encoding="ISO-8859-1")  #key=count
    else:
        return None

    # split the dataframe depending on the in-time and out-time and process them
    if biometric_GCU1 is not None:
        df_gcu1_all, df_in1, df_out1 = ut.split_file(biometric_GCU1)
        df_biometric_GCU1 = ut.merge_files(df_in1, df_out1)
        #st.write(df_biometric_GCU1.head())
    else:
        st.write("Ready to create...")
    #st.write(df_biometric1.head())

    # second file reading
    #st.write("Upload the second excel file :")
    uploaded_file = st.file_uploader("Upload the biometric file 2 (GIPS) in excel format", key=2)  # , key=key)  #key=f"{key}"
    if uploaded_file is not None:
        biometric_gips = pd.read_excel(uploaded_file)  # , encoding="ISO-8859-1")  #key=count
    else:
        return None
    # split the dataframe depending on the in-time and out-time
    if biometric_gips is not None:
        df_pharma_all, df_pharma_in, df_pharma_out = ut.split_file(biometric_gips)
        df_biometric_Pharma = ut.merge_files(df_pharma_in, df_pharma_out)
        #st.write(df_biometric_Pharma.head())
    else:
        st.write("Ready to create...")
    df_biometric = pd.concat([df_biometric_GCU1, df_biometric_Pharma], axis=0)
    #df_biometric.head()

    #st.write(f'Number of faculties in GIMT building : {df_biometric_GCU1.shape[0]}')
    #st.write(f'Number of faculties in GIPS building : {df_biometric_Pharma.shape[0]}')

    # Third file reading; admin building
    #
    uploaded_file = st.file_uploader("Upload the biometric file 3 (Admin) in excel format", key=3)
    if uploaded_file is not None:
        biometric_admin = pd.read_excel(uploaded_file)  # , encoding="ISO-8859-1")  #key=count
    else:
        return None
    # split the dataframe depending on the in-time and out-time
    if biometric_admin is not None:
        df_admin_all, df_admin_in, df_admin_out = ut.split_file(biometric_admin)
        df_biometric_admin = ut.merge_files(df_admin_in, df_admin_out)
        # st.write(df_biometric_Pharma.head())
    else:
        st.write("Ready to create...")

    # This section processes the Master Employee data
    df_employee = pd.read_csv('./data/emp_master_data.csv', skiprows=6, encoding='windows-1252')  # ,engine='xlrd')
    # df_employee = pd.read_csv('./data/master_faculty_data.csv', encoding='windows-1252') #,engine='xlrd')
    df_employee = df_employee[4:-6]
    df_employee.reset_index(inplace=True, drop=True)
    df_employee.rename(columns={'Employee ID': 'Emp ID'}, inplace=True)

    # Combining the biometric data with the Master Employee data (teaching staffs)
    df_biometric = pd.merge(df_biometric, df_employee, how='left', on='Emp ID')
    df_biometric = df_biometric[
        ['Emp ID', 'Name', 'Designation', 'Department', 'Present', 'Absent', 'late', 'morn_HD', 'aftern_HD',
         'left_early']]

    # Combining the biometric data with the Master Employee data (non teaching staffs)
    df_biometric_admin = pd.merge(df_biometric_admin, df_employee, how='left', on='Emp ID')
    df_biometric_admin = df_biometric_admin[
        ['Emp ID', 'Name', 'Designation', 'Department', 'Present', 'Absent', 'late', 'morn_HD', 'aftern_HD',
         'left_early']]
    #st.write(df_biometric.head())

    # This section processes the leave data from ERP
    uploaded_file = st.file_uploader("Upload the Leave file in CSV format", key=4)  # , key=key)  #key=f"{key}"
    # encoding='utf-8', encoding="ISO-8859-1", engine="openpyxl"
    if uploaded_file is not None:
        df_erp = pd.read_csv(uploaded_file, encoding="ISO-8859-1")  #key=count
    else:
        return None

    df_erp.columns = list(df_erp.loc[5])
    df_erp = df_erp[6:]

    df_leave_pending, df_leave_approved = ut.preprocess_erp_leaves(df_erp)

    # ----------------------------------------------------------------------------------------------------
    # This section handles the teaching staff
    df_faculty_final = pd.merge(df_biometric, df_leave_approved, how='left', on='Emp ID')
    df_faculty_final.fillna(0, inplace=True)

    # This section handles the non-teaching staff
    df_admin_final = pd.merge(df_biometric_admin, df_leave_approved, how='left', on='Emp ID')
    df_admin_final.fillna(0, inplace=True)
    #df_faculty_final.head()

    # Working with the special adjustments - Bus being late, allowed half day or full etc
    uploaded_file = st.file_uploader("Upload exempted data in Excel format", key=5)  # , key=key)  #key=f"{key}"
    # encoding='utf-8', encoding="ISO-8859-1", engine="openpyxl"
    if uploaded_file is not None:
        df_exempted_late = pd.read_excel(uploaded_file, sheet_name='late')  # key=count, encoding="ISO-8859-1",
        df_exempted_hd = pd.read_excel(uploaded_file, sheet_name='half_day')  # key=count, encoding="ISO-8859-1",
        df_exempted_fd = pd.read_excel(uploaded_file, sheet_name='full_day')  # key=count, encoding="ISO-8859-1",
    else:
        return None

    # with exempted late
    new_cols_late = ut.find_cols(df_exempted_late.columns)
    df_exempted_late = df_exempted_late[new_cols_late]
    df_exempted_late['exempted_late'] = df_exempted_late.count(axis=1) - 2

    # with exempted half day
    new_cols_hd = ut.find_cols(df_exempted_hd.columns)
    df_exempted_hd = df_exempted_hd[new_cols_hd]
    df_exempted_hd['exempted_hd'] = df_exempted_hd.count(axis=1) - 2

    # with exempted full day
    new_cols_fd = ut.find_cols(df_exempted_fd.columns)
    df_exempted_fd = df_exempted_fd[new_cols_fd]
    df_exempted_fd['exempted_fd'] = df_exempted_fd.count(axis=1) - 2

    df_exempted_late = df_exempted_late[['Emp ID','exempted_late']]
    df_exempted_hd = df_exempted_hd[['Emp ID', 'exempted_hd']]
    df_exempted_fd= df_exempted_fd[['Emp ID', 'exempted_fd']]

    if len(df_exempted_late)>0:
        df_faculty_final = pd.merge(df_faculty_final, df_exempted_late, how='left', on='Emp ID')
        df_admin_final = pd.merge(df_admin_final, df_exempted_late, how='left', on='Emp ID')
    if len(df_exempted_hd) > 0:
        df_faculty_final = pd.merge(df_faculty_final, df_exempted_hd, how='left', on='Emp ID')
        df_admin_final = pd.merge(df_admin_final, df_exempted_hd, how='left', on='Emp ID')
    if len(df_exempted_fd) > 0:
        df_faculty_final = pd.merge(df_faculty_final, df_exempted_fd, how='left', on='Emp ID')
        df_admin_final = pd.merge(df_admin_final, df_exempted_fd, how='left', on='Emp ID')
    df_faculty_final.fillna(0, inplace=True)
    df_admin_final.fillna(0, inplace=True)

    # Number of working days and holidays (teaching)
    working_days = df_faculty_final['Present'].mode()[0]
    holidays = df_faculty_final['Absent'].mode()[0]

    # Number of working days and holidays (non teaching)
    working_days_staff = df_admin_final['Present'].mode()[0]
    holidays_staff = df_admin_final['Absent'].mode()[0]

    # late faculties
    df_faculty_final['late'] = df_faculty_final['late'] - df_faculty_final['exempted_late']
    faculty_late = df_faculty_final[df_faculty_final.late > 2]

    # late non-teaching
    df_admin_final['late'] = df_admin_final['late'] - df_admin_final['exempted_late']
    admin_late = df_admin_final[df_faculty_final.late > 2]

    # present-leave mismatch
    df_faculty_final['mismatch'] = df_faculty_final.apply(ut.cal_mismatch, axis=1)
    df_faculty_mismatch = df_faculty_final[df_faculty_final.mismatch == True]

    # present-leave mismatch (non teaching)
    df_admin_final['mismatch'] = df_admin_final.apply(ut.cal_mismatch, axis=1)
    df_admin_mismatch = df_admin_final[df_admin_final.mismatch == True]

    # The final report teaching
    #'Emp ID','Name','Designation','Department','sanctioned leaves'
    df_final_report = df_faculty_final.copy()
    #df_final_report['leave allowed'] = df_final_report['sanctioned leaves']
    df_final_report['leave allowed'] = df_final_report['sanctioned leaves'] + \
                                    df_final_report['exempted_hd']*0.5 + df_final_report['exempted_fd']
    df_final_report['working days'] = int(working_days)
    df_final_report['Absent'] = df_final_report['working days'] - df_final_report['Present']
    df_final_report['unauthorised leave'] = np.abs(df_final_report['Absent'] - df_final_report['leave allowed'])

    df_final_report=df_final_report[['Emp ID','Name','Designation','Department','working days','Present','Absent','leave allowed','unauthorised leave']]
    #'Emp ID','Name','Designation','Department','working days','Present','Absent','leave allowed','unauthorise leave'


    # Saving the final excel
    sheets = ['gimt_details', 'gips_details', 'report_faculty', 'report_late', 'report_mismatch', 'pending_leave', 'final_report']
    writer = pd.ExcelWriter('./output/report_fac.xlsx', engine='xlsxwriter')
    dataframes = [df_gcu1_all, df_pharma_all, df_faculty_final, faculty_late, df_faculty_mismatch, df_leave_pending, df_final_report]
    for i, frame in enumerate(dataframes):
        frame.to_excel(writer, sheet_name=sheets[i], index=False)
    writer.close()

    # teaching staffs
    with open(f'./output/report_fac.xlsx', "rb") as file:
        st.download_button(
            label="Download the faculties report",
            data=file,
            file_name=f'report_fac.xlsx',
            mime="application/zip"
        )

    # The final report non-teaching
    # 'Emp ID','Name','Designation','Department','sanctioned leaves'
    df_final_rep_nt = df_admin_final.copy()
    df_final_rep_nt['leave allowed'] = df_final_rep_nt['sanctioned leaves'] + \
                                           df_final_rep_nt['exempted_hd'] * 0.5 + df_final_rep_nt['exempted_fd']
    df_final_rep_nt['working days'] = int(working_days_staff)
    df_final_rep_nt['Absent'] = df_final_rep_nt['working days'] - df_final_rep_nt['Present']
    df_final_rep_nt['unauthorised leave'] = np.abs(df_final_rep_nt['Absent'] - df_final_rep_nt['leave allowed'])
    #st.write(df_final_rep_nt.head())

    df_final_report_nt = df_final_rep_nt[['Emp ID', 'Name', 'Designation', 'Department', 'working days', 'Present', 'Absent', 'leave allowed',
             'unauthorised leave']]

    # Saving the final excel
    sheets = ['bio_details', 'report_staffs', 'report_late', 'report_mismatch', 'pending_leave', 'final_report']
    writer = pd.ExcelWriter('./output/report_staffs.xlsx', engine='xlsxwriter')
    dataframes = [df_admin_all, df_admin_final, admin_late, df_admin_mismatch, df_leave_pending, df_final_report_nt]
    for i, frame in enumerate(dataframes):
        frame.to_excel(writer, sheet_name=sheets[i], index=False)
    writer.close()

    # Non teaching staffs
    with open(f'./output/report_staffs.xlsx', "rb") as file:
        st.download_button(
            label="Download the Staffs report",
            data=file,
            file_name=f'report_staffs.xlsx',
            mime="application/zip"
        )











