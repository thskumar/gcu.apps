import pandas as pd
"""
def read_file():
    #key = str(key)
    uploaded_file = st.file_uploader("Upload the biometric file in excel format")#, key=key)  #key=f"{key}"
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file) # , encoding="ISO-8859-1")  #key=count
    else:
        return None
"""

def split_file(df):
        # pinking up the dates
        dates = list(df.loc[6])
        dates = [str(item).zfill(2) for item in dates]
        #dates = dates[2:]
    
        # Calculate all the starting rows and gaps
        gap = 13
        start_name = 4
        start_clock_in = 7
        start_clock_out = 8

        selected_index_name = list(range(start_name, len(df), gap))
        selected_index_clock_in = list(range(start_clock_in, len(df), gap))
        selected_index_clock_out = list(range(start_clock_out, len(df), gap))

        df_biometric = df[df.index.isin(selected_index_name)]
        df_clock_in = df[df.index.isin(selected_index_clock_in)]
        df_clock_out = df[df.index.isin(selected_index_clock_out)]

        # rename columns
        #df_clock_in.columns = [f'clock_in_{i}' for i in range(df_clock_in.shape[1])]
        #df_clock_out.columns = [f'clock_out_{i}' for i in range(df_clock_out.shape[1])]

        # rename columns
        #print("dates")
        #print(dates)
        df_clock_in.columns = [f'clock_in_{d}' for d in dates]
        df_clock_out.columns = [f'clock_out_{d}' for d in dates]

        # drop unwanted columns
        # biometric.drop(['Monthly Attendance Summary'],  inplace=True, axis=1)
        #df_clock_in.drop(['clock_in_0'], inplace=True, axis=1)
        #df_clock_out.drop(['clock_out_0'], inplace=True, axis=1) clock_out_nan
        df_clock_in.drop(['clock_in_nan'], inplace=True, axis=1) 
        df_clock_out.drop(['clock_out_nan'], inplace=True, axis=1) 

        # droping 25 as we don't have data
        #df_clock_in.drop(['clock_in_25'], inplace=True, axis=1) 

        # drop all columns with no entry
        df_biometric.dropna(axis=1, how='all', inplace=True)
        df_clock_in.dropna(axis=1, how='all', inplace=True)
        df_clock_out.dropna(axis=1, how='all', inplace=True)

        # Selecting the required columns
        df_biometric = df_biometric[['Monthly Attendance Summary', 'Unnamed: 2', 'Unnamed: 7', 'Unnamed: 9']]

        # Rename all columns with list
        new_cols = ['Emp ID', 'Names', 'Present', 'Absent']
        df_biometric.columns = new_cols

        # df.reset_index()
        df_biometric.reset_index(inplace=True, drop=True)
        df_clock_in.reset_index(inplace=True, drop=True)
        df_clock_out.reset_index(inplace=True, drop=True)

        #Combining the three datasets into two - 'in coming' and 'out going'
        df_in = pd.concat([df_biometric, df_clock_in], axis=1)
        df_out = pd.concat([df_biometric, df_clock_out], axis=1)
        
        df_in = df_in.fillna(0)
        df_out = df_out.fillna(0)
        df_all = pd.concat([df_in, df_clock_out], axis=1)
        df_all = df_all.fillna(0)

        return df_all, df_in, df_out
# this function merges two dataframes after calculating the late entries
def merge_files(df_in, df_out):
    time_in = (8, 45)
    time_out = (15, 50)

    #late_before_9_15 
    #early_before_3_50 
    #morning_half_absent
    #afternoon_half_absent

    cols_in = df_in.columns[4:]
    cols_out = df_out.columns[4:]
    
    # exclude 25 this time as no data is available
    #cols_in = [col for col in cols_in if col not in ['clock_in_nan','clock_in_25']]
    #cols_out = [col for col in cols_out if col not in ['clock_out_nan']
                
    partial_late, morning_half_absent = calculate_late(df_in, cols_in, time_in)
    
    df_in['late'] = partial_late
    df_in['morn_HD'] = morning_half_absent
    
    df_biometric = df_in[['Emp ID', 'Names', 'Present', 'Absent', 'late', 'morn_HD']]
    #df_biometric = df_in
    #df_biometric = pd.concat([df_in, df_out], axis=1)
    
    left_early, afternoon_half_absent = calculate_early(df_out, cols_out, time_out)
    #df_out['leaving_before_time'] = left_early

    df_biometric['left_early'] = left_early
    df_biometric['aftern_HD'] = afternoon_half_absent

    df_biometric['forgot_punching'] = forgot_punching(df_biometric)
    return df_biometric

def forgot_punching(df):
    cols_forgot = df.columns
    cols_forgot = cols_forgot[4:]
    
    # including 'clock_in_25', as clock_out_25 is not available
    #cols_forgot = [col for col in cols_forgot if col not in ['clock_in_nan','clock_out_nan','clock_in_25']]
    half = int(len(cols_forgot)/2)
    cols_forgot1 = cols_forgot[:half]
    cols_forgot2 = cols_forgot[half:]

    # iterate the dateset
    forgot_punching=[]
    for _, row in df.iterrows():
        fp = 0
        for col1,col2 in cols_forgot1,cols_forgot2:
            if (row[col1] == 0 and row[col2] != 0) or (row[col1] != 0 and row[col2] == 0):
                fp += 1
        forgot_punching.append(fp)
    return forgot_punching
    
def calculate_late(df, cols, time_in):
        emp_id_exempted = ['GCU010013','GCU010017','GCU010025','GCU030010','GCU010005','GCU020004'] 
        partial_late = []
        #full_late = []
        morning_half_absent = []
        for _, row in df.iterrows():
            # for each employee calcuate partial and full late and append in the list
            p_late = 0
            #f_late = 0
            m_absent = 0
            for col in cols:
                if row[col] != 0:
                    hr = str(row[col]).split(':')[0]
                    #min = str(row[col]).split(':')[1]
                    min = 30
                    # time_in = (9, 25); 
                    if row['Emp ID'] in emp_id_exempted:            # from 9:26 till 9:59
                        if (int(hr) == 9 and int(min) > 25) :
                            p_late += 1
                        elif (int(hr) > 9):          # more than 9
                            m_absent += 1
                    # time_in = (8, 45); between 8:45 and 9:15
                    elif (int(hr) == time_in[0] and int(min) > time_in[1]) or (int(hr) == time_in[0]+1 and int(min) < 16):    
                        p_late += 1
                    elif (int(hr) == 9  and int(min) > 15) or (int(hr) > 9):          # 12:30 PM
                        m_absent += 1
                    #else:
                    #    f_late+=1
            partial_late.append(p_late)
            morning_half_absent.append(m_absent)
            #full_late.append(f_late)
        return partial_late, morning_half_absent #, full_late


def calculate_early(df, cols, time_out):
    left_early = []
    afternoon_half_absent = []                                                # Departure : 12:30 or later
    for _, row in df.iterrows():
        # for each employee calcuate partial and full late and append in the list
        l_early = 0
        a_absent = 0
        for col in cols:
            if row[col]!= 0:
                hr = str(row[col]).split(':')[0]
                min = str(row[col]).split(':')[1]
                if (int(hr) == 12 and int(min) > 30) or (int(hr) < 15):
                    a_absent += 1   
                elif (int(hr)== time_out[0] and int(min)< time_out[1]):  # time_out = (15, 50)
                    l_early+=1
        left_early.append(l_early)
        afternoon_half_absent.append(a_absent)
    return left_early, afternoon_half_absent

def modify_employee_id(emp_id):
    emp_id = str(emp_id)
    if len(emp_id)<9:
        return 'GCU'+emp_id.zfill(6)
    else:
        return emp_id
def preprocess_erp_leaves(df):
    # remove unwanted columns and rows
    df.drop(['Serial No.', 'Location', 'Timeline', 'Request Date', 'From Date', 'To Date'], inplace=True, axis=1)
    df.dropna(how="any", inplace=True)
    df = df[:-1]

    # separate into - approved & pending dataset
    df_approved = df[(df['Status'] == 'Approved')]
    df_pending = df[(df['Status'] == 'Pending')]

    # rename columns and convert to numeric
    df_approved.rename(columns={'Total Days': 'sanctioned leaves', 'Employee ID': 'Emp ID'}, inplace=True)
    df_approved["sanctioned leaves"] = pd.to_numeric(df_approved["sanctioned leaves"], errors='coerce')

    # groupby and add all the leaves individually and conver to dataframe
    leave_list = df_approved.groupby('Emp ID')['sanctioned leaves'].sum()
    leave_dict = leave_list.to_dict()
    df_approved_final = pd.DataFrame(leave_dict.items(), columns=['Emp ID', 'sanctioned leaves'])

    return df_pending, df_approved_final

def cal_mismatch(row):
    absent_credit = row['Absent'] + (row['morn_HD'] + row['aftern_HD'])*0.5
    if absent_credit == row['sanctioned leaves']:
        return False
    else:
        return True
        
def find_cols(cols):
    no_cols = int((len(cols)-2)/2)
    exempted_cols = ['Emp ID', 'Name']
    for i in range(1, no_cols+1):
        exempted_cols.append(f'Day{i}')
    return exempted_cols

