try:
    import streamlit as st
    import os
    import sys
    import pandas as pd
    import numpy as np
    from functools import reduce
    import re

    sys.path.append('utils')
    from customcss import load_css
    from writeread import read_file, to_excel, get_studycode
    from generategp2ids import master_keyv2
    from qcutils import checkNull, TakeOneEntry, checkDup
    from plotting import aggridPlotter

except Exception as e:
    print("Some modules are not installed {}".format(e))

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "secrets/secrets.json"

def jumptwice():
    st.write("##")
    st.write("##")

def app():
    load_css("apps/css/css.css")
    st.markdown("""<div id='link_to_top'></div>""", unsafe_allow_html=True)
    st.markdown('<p class="big-font">GP2 clinical data self-QC</p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> This is a app tab to self-check the sample manifest and clinical data. </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Download the template from the link below. Once you open the link, go to "File"> "Download" > "xlsx" or "csv" format </p>', unsafe_allow_html=True)
    st.markdown('[Access the data dictionary and templates](https://docs.google.com/spreadsheets/d/1sWFPm-i9YACP4IXAMW_asykwwZHZfKOOzG2Q8i7_B-4)', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Please refer to the second tab (Dictionary) for instructions. </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Please refer to the first tab (clinical) to access sample manifest template to fill in. </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Please note all the GP2 required columns must be completed </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Once you have filled in all the columns avavailable in your cohort, please upload the manifest on the side bar to start the QC process </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Once the QC process completes, please move to the Upload tab of the app to store your sample manifest </p>', unsafe_allow_html=True)

    data_file = st.sidebar.file_uploader("Upload Your clinical data (CSV/XLSX)", type=['xlsx', 'csv'])

    study_name = get_studycode() # This will set study_name to None when initialised
    if 'keepcode' in st.session_state:
        if len(re.findall(r'-', st.session_state['keepcode']))>0:
            study_name = st.session_state['keepcode'].split('-')[0]
    
    cols = ['study', 'sample_id', 'visit_month',
            'mds_updrs_part_iii_summary_score',
            'moca_total_score', 'hoehn_and_yahr_stage',
            'mmse_total_score']

    required_cols = ['study', 'sample_id', 'visit_month']


    if data_file is not None:
        st.markdown('<p class="big-font">Clinical data QC </p>', unsafe_allow_html=True)
        jumptwice()
        df = read_file(data_file)

        # missing col check
        missing_cols = np.setdiff1d(cols, df.columns)
        if len(missing_cols)>0:
            st.error(f'{missing_cols} are missing. Please use the template sheet')
            st.stop()
        else:
            st.text('Check column names--> OK')
            df_non_miss_check = df[required_cols].copy()


        # required columns checks
        if df_non_miss_check.isna().sum().sum()>0:
            st.error('There are some missing entries in the required columns. Please fill the missing cells ')
            st.text('First ~30 columns with missing data in any required fields')
            st.write(df_non_miss_check[df_non_miss_check.isna().sum(1)>0].head(20))
            st.stop()
        else:
            st.text('Check missing data in the required fields --> OK')


        # Make sure we get visit_month and sample_ids in the right format
        try:
            df['visit_month'] = df['visit_month'].astype(int)
            stopapp=False
        except:
            st.error(f' We could not convert visit month to integer')
            st.error(f' Please check visit month refers to numeric month from Baseline')
            stopapp=True
        if stopapp:
            st.stop()
        
        df['sample_id'] = df['sample_id'].astype(str)


        # Make sure clinical vars are integers as well as there are no negative values
        for col in df.iloc[:, 3:].columns:
            if not df[df[col] < 0].shape[0] == 0:
                st.error(f' We have detected negative values on column {col}')
                st.error(f' This is likely to be a mistake on the data. Please, go back to the sample manifest anc check')
                st.stop()
        st.text('Check there are no variables with negative values --> OK')


        # Check that the sample IDs are already in the json file
        if 'ids_tracker' not in st.session_state:
            st.text('Checking that the sample manifest is already on our system...')
            studynames = list(df['study'].unique())
            ids_tracker = master_keyv2(studies = studynames)
            for study in studynames:
                try:
                    study_tracker = ids_tracker[study]
                except:
                    st.error(f'We could not find sample ids for study {study} in our system')
                    st.error('Please make sure you have uploaded the sample manifest to the GP2 storage system before QC the clinical data')
                    st.stop()

                df_subset = df[df['study']==study].copy()
                df_ids_list = df_subset['sample_id'].to_list()
                master_study_ids = list(study_tracker.keys())

                checkdiff = np.setdiff1d(df_ids_list, master_study_ids)

                if len(checkdiff) == 0:
                    continue
                else:
                    st.error(f'We have detected some sample ids for study {study} that are not on the system')
                    st.error('Please, make sure the sample manifest have been QCed and uploaded to the system first')
                    st.error('Printing the conflicting sample IDs....')
                    st.error(checkdiff)
                    st.stop()
            st.text('We managed to track your sample manifest... Thanks')
            st.session_state['ids_tracker'] = 'DONE'
            jumptwice()
        else:
            st.text('Checking that the sample manifest is already on our system...')
            st.text('We managed to track your sample manifest... Thanks')
            jumptwice()
        
        
        st.text('Your clinical data passed all initial checkings...')
        if 'data_chunks' not in st.session_state:
            st.session_state['data_chunks'] = []
        if 'btn' not in st.session_state:
            st.session_state['btn'] = False
        if 'variable' not in st.session_state:
           st.session_state['variable'] = [col for col in cols[3:]]
        
        def callback1():
            st.session_state['btn'] = True
        def callback2():
            st.session_state['btn'] = False
        
        if 'counter' not in st.session_state:
            st.text('Starting QC at the variable level')
            st.session_state['counter'] = 0
            st.selectbox("Choose a variable", st.session_state['variable'])
            get_varname = None
        else:
            st.session_state['counter'] += 1
            if len(st.session_state['variable'])>=1:
                get_varname = st.selectbox("Choose a variable", st.session_state['variable'], on_change=callback2)

            else:
                st.markdown('<p class="medium-font"> THANKS. YOU HAVE SUCCESFULLY QCED all the CLINICAL VARIABLES</p>', unsafe_allow_html=True )

                final_df = reduce(lambda x, y: pd.merge(x, y, 
                                                        on = ['study', 'sample_id', 'visit_month'],
                                                        how = 'outer'), st.session_state['data_chunks'])
                
                st.session_state['clinqc'] = final_df

                aggridPlotter(final_df)
                # df_builder = GridOptionsBuilder.from_dataframe(final_df)
                # df_builder.configure_grid_options(alwaysShowHorizontalScroll = True,
                #                                     enableRangeSelection=True,
                #                                     pagination=True,
                #                                     paginationPageSize=10000,
                #                                     domLayout='normal')
                # godf = df_builder.build()
                # AgGrid(final_df,gridOptions=godf, theme='streamlit', height=300)

                writeexcel = to_excel(final_df, st.session_state['keepcode'], datatype = 'clinical')
                st.download_button(label='📥 Download your QC clinical data',
                                   data = writeexcel[0],
                                   file_name = writeexcel[1],)
                
                st.stop()
        

        jumptwice()        
        if get_varname is not None:
            b1 = st.button("QC variable?", on_click=callback1)
            if st.session_state['btn']:
            #if st.button("QC variable?", on_click=callback1):
                st.subheader(f"Starting QC for {get_varname}")
                vars = ['study', 'sample_id', 'visit_month', get_varname]
                df_subset = df[vars].copy()

                st.write("Checking null values")
                nulls = checkNull(df_subset, get_varname)

                st.write("If this is not what you would expect, please go back and check the clinical data file")

                st.write("Checking duplicates")
                dups = checkDup(df_subset, ['sample_id', 'visit_month'])
                
                st.write("Taking the entry with less missing values")
                df_final =TakeOneEntry(df_subset, 
                                    ['sample_id', 'visit_month'],
                                    method='less_na')

                # I have not managed to fir the contenct 
                # https://discuss.streamlit.io/t/is-there-a-way-to-autosize-all-columns-by-default-on-rendering-with-streamlit-aggrid/31841/4
                aggridPlotter(df_final)
                # df_builder = GridOptionsBuilder.from_dataframe(df_final)
                # df_builder.configure_grid_options(alwaysShowHorizontalScroll = True,
                #                                     enableRangeSelection=True,
                #                                     pagination=True,
                #                                     paginationPageSize=10000,
                #                                     domLayout='normal')
                
                # godf = df_builder.build()
                # AgGrid(df_final,gridOptions=godf, theme='streamlit', height=300)

                #qc_yesno = st.selectbox("Does the variable QC look correct?", [" ", "YES", "NO"] )
                qc_yesno = st.selectbox("Does the variable QC look correct?", 
                                        ["YES", "NO"],
                                        index=None)
                if qc_yesno == 'YES':
                    st.info('Thank you')
                    st.session_state['data_chunks'].append(df_final)
                    st.session_state['variable'].remove(get_varname)# = [col for col in cols[3:]]
                    st.button("QC another variable", on_click=callback2)
                if qc_yesno == 'NO':
                    st.error('Please go back to your clinical data and change unexpected values')
                    st.error('Please get in touch with with Cohort Integration Working Group if needed')
                    st.stop()
