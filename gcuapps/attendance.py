import streamlit as st
import pandas as pd

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')
def app():


    header = st.container()
    dataset = st.container()
    #features = st.container()
    #model_training = st.container()

    with header:
        st.header('Attendance Calculation of GCU')
        st.text("It combines the output of Biometric data with the leaves sactioned dataset")

    with dataset:
        biometric = pd.DataFrame()
        uploaded_file = st.file_uploader("Upload the biometric data in excel/csv format")
        if uploaded_file is not None:
            biometric = pd.read_excel(uploaded_file)  # , encoding="ISO-8859-1")
            # st.write(biometric)

            start = 4  # this is to discard the first few rows
            gap = 13

            # Discard the empty row and select only the required rows
            selected_index = list(range(start, len(biometric), gap))
            biometric2 = biometric[biometric.index.isin(selected_index)]
            biometric2.dropna(axis=1, inplace=True)

            # Select only the required columns and then rename
            biometric3 = biometric2[['Monthly Attendance Summary', 'Unnamed: 2', 'Unnamed: 7', 'Unnamed: 9']]
            biometric3.columns = ['Emp ID', 'Name', 'Present', 'Absent']
            biometric3.reset_index(inplace=True, drop=True)
            st.write(biometric3)

        file = st.file_uploader("Upload the leaves detail file", type="xlsx")
        if file is not None:
            all_sheet = pd.ExcelFile(file)
            sheets = all_sheet.sheet_names
            leaves = pd.read_excel(file, sheet_name='Total_leave')

            leaves_cols = leaves.iloc[4]
            leaves.drop(leaves.index[:5], inplace=True)
            leaves.columns = leaves_cols
            # st.write(leaves_cols)
            # st.write(leaves)

            # Sort both the dataset on 'Emp ID'
            biometric3['Emp ID'] = pd.to_numeric(biometric3['Emp ID'])
            sorted_biometric3 = biometric3.sort_values(by=['Emp ID'], ascending=True)

            leaves['Emp ID'] = pd.to_numeric(leaves['Emp ID'])
            sorted_leaves = leaves.sort_values(by=['Emp ID'], ascending=True)

            # Merge the two
            result = pd.merge(sorted_biometric3, sorted_leaves, on='Emp ID')

            result = result.reindex(
                columns=['Sl. No', 'Emp ID', 'Name_y', 'Designation', 'Department', 'Type', 'Total Working Days',
                         'Present', 'Absent', \
                         'No. of leave allowed', 'No. of unauthorized leave', 'Remark'])

            result.fillna(' ', inplace=True)
            result.rename(columns={'Name_y': 'Name', 'No. of leave allowed': 'Leaves allowed',
                                   'No. of unauthorized leave': 'Unauthorized leaves'}, inplace=True)
            result.drop(['Sl. No', 'Type'], inplace=True, axis=1)

            result_csv = convert_df(result)
            st.header('Report Generation')
            st.write(result)
            st.download_button(
                label="Download data as CSV",
                data=result_csv,
                file_name='attendance_report.csv',
                mime='text/csv',
            )



