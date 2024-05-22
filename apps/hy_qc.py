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
    from qcutils import checkNull, TakeOneEntry, checkDup, create_survival_df
    from plotting import aggridPlotter, plot_km_curve, plot_interactive_visit_month, plot_interactive_first_vs_last

except Exception as e:
    print("Some modules are not installed {}".format(e))

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/iwakih2/Library/CloudStorage/OneDrive-NationalInstitutesofHealth/projects/gp2-manifest-checkupload/secrets/secrets.json"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "secrets/secrets.json"

def jumptwice():
    st.write("##")
    st.write("##")

def app():
    data_file = st.sidebar.file_uploader("Upload Your clinical data (CSV/XLSX)", type=['xlsx', 'csv'])
    study_name = get_studycode() # This will set study_name to None when initialised
    cols = ['clinical_id', 'visit_month', 'visit_name', 'hoehn_and_yahr_stage']
    required_cols =  ['clinical_id', 'visit_month']
    outcomes = ['hoehn_and_yahr_stage']
    template_link = 'https://docs.google.com/spreadsheets/d/1tTkVcfP8l37uN09vGMNWiPQKBESRQGCrTZLdvR7rVQw/edit?usp=sharing'
    st.markdown(f'This is an app to check your data. (modified / original Hoehn and Yahr Scale). Please download [the data dictionary and template]({template_link}). Second tab has the data dictionary.', unsafe_allow_html=True)

    if data_file is not None:
        df = read_file(data_file)

        # merge with genetics data
        # Load genetics data
        dfg = pd.read_csv('secrets/R8_2024-05-17_draft.csv', low_memory=False)
        dfg = dfg.drop_duplicates(subset='GP2ID', keep='first')
        dfg = dfg[dfg.study==study_name].copy()
        df = pd.merge(df, dfg[['GP2ID', 'clinical_id', 'GP2_phenotype', 'study_arm', 'study_type']], on='clinical_id', how='left')
        
        # number review and GP2ID checks
        n = len(df.clinical_id.unique())
        st.write(f'[{n}] unique clinical_ids and [{len(df)}] observations are found in the dataset')
        id_not_in_GP2 = df[df.GP2ID.isnull()]['clinical_id'].unique()
        if len(id_not_in_GP2) == n:
            st.error(f'None of the clinical IDs are in the GP2. Please check the clinical IDs and your GP2_study_code ({study_name}) are correct')
            st.stop()
        elif len(id_not_in_GP2) > 0:
            st.warning(f'Some clinical IDs are not in the GP2 so the dataset. dataset in reveiw is reduced to the ones in the GP2')
            df= df[df.GP2ID.notnull()].copy()
            n = len(df.clinical_id.unique())
            st.warning(f'Reduced to [{n}] unique clinical_ids and [{len(df)}] observations')
            st.text(f'clinical_id not found in the GP2. {id_not_in_GP2}')

        # missing col check
        missing_cols = np.setdiff1d(cols, df.columns)
        if len(missing_cols)>0:
            st.error(f'{missing_cols} are missing. Please use the template sheet')
            st.stop()
        else:
            df_non_miss_check = df[required_cols].copy()


        # required columns checks
        if df_non_miss_check.isna().sum().sum()>0:
            st.error(f'There are some missing entries in the required columns {required_cols}. Please fill the missing cells ')
            st.write('First ~20 columns with missing data in any required fields')
            st.write(df_non_miss_check[df_non_miss_check.isna().sum(1)>0].head(20))
            st.stop()

        # Make sure we get visit_month and sample_ids in the right format
        try:
            df['visit_month'] = df['visit_month'].astype(int)
            stopapp=False
        except:
            st.error(f' We could not convert visit month to integer')
            st.error(f' Please check visit month refers to numeric month from Baseline')
            st.error(f'First ~20 columns with visit_month not converted to integer')
            st.write(df[df['visit_month'].apply(lambda x: not x.isnumeric())].head(20))
            
            stopapp=True
        
        # make sure the clnical_id - visit_month combination is unique (warning if not unique)
        if df.duplicated(subset=['clinical_id', 'visit_month']).sum()>0:
            st.warning(f' We have detected duplicated visit months. Pleaes review if it is true')
            # df.loc[df.duplicated(subset='visit_month', keep=False), 'visit_month'] = df['visit_month'].astype(str) + '_' + df['visit_name']
            if df[['visit_month', 'visit_name']].nunique().values[0] == 1:
                st.error(f' To allow duplicated visit_month, please fill the visit_name')
                stopapp=True

        if stopapp:
            st.stop()
        
        # Make sure clinical vars are integers as well as there are no negative values
        for col in outcomes:
            if not df[df[col] < 0].shape[0] == 0:
                st.error(f' We have detected negative values on column {col}')
                st.error(f' This is likely to be a mistake on the data. Please, go back to the sample manifest anc check')
                st.stop()
        # st.write('Check there are no variables with negative values --> OK')

        
        st.write('Your clinical data passed all initial checkings...')

        if 'data_chunks' not in st.session_state:
            st.session_state['data_chunks'] = []
        if 'btn' not in st.session_state:
            st.session_state['btn'] = False
        if 'variable' not in st.session_state:
           st.session_state['variable'] = outcomes
        
        def callback1():
            st.session_state['btn'] = True
        def callback2():
            st.session_state['btn'] = False
        
        if 'counter' not in st.session_state:
            st.write('Starting QC at the variable level')
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
                                                        on = ['clinical_id', 'visit_month'],
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
                vars = ['GP2ID', 'clinical_id', 'GP2_phenotype', 'study_arm', 'study_type', 'visit_month', get_varname]
                df_subset = df[vars].copy()

                st.write("Checking null values")
                nulls = checkNull(df_subset, get_varname)

                st.write("If this is not what you would expect, please go back and check the clinical data file")

                st.write("Checking duplicates")
                dups = checkDup(df_subset, ['GP2ID', 'visit_month'])
                
                st.write("Taking one entry with less missing values")
                
                df_final =TakeOneEntry(df_subset, 
                                    ['GP2ID', 'visit_month'],
                                    method='less_na')
                
                # st.text(df_final.head())
                selected_strata = st.selectbox("Select Stratifying variable", ['study_arm', 'GP2_phenotype'])
                plot_interactive_visit_month(df_final, get_varname, selected_strata)

                df_sv_temp = create_survival_df(df_final, 3, 'greater', get_varname)
                df_sv_temp = df_sv_temp.drop(columns=['event', 'censored_month'])
                plot_interactive_first_vs_last(df_sv_temp, df_final, selected_strata)


                st.title('Data show')
                # Select a GP2ID from the list
                selected_gp2id = st.selectbox("Select GP2ID", df_final['GP2ID'].unique())

                if selected_gp2id:
                    st.write(f"Selected GP2ID: {selected_gp2id}")
                    st.write("Details:")
                    dft = df_final[df_final['GP2ID'] == selected_gp2id].drop(columns=df_final.filter(regex='_jittered$').columns)
                    st.write(dft)

                # using df_sv, event and censored_months, generate the show KM curve stratifeid by strata
                # take a threshold input
                st.title('Kaplan-Meier Curve for reaching the Threshold Score')
                threshold = st.number_input(min_value=0, max_value=5, step=1, label='threshold', value=3)
                direction = st.radio(label='direction', options=['greater', 'less'])
                df_sv = create_survival_df(df_final, threshold, direction, get_varname)
                plot_km_curve(df_sv, selected_strata, threshold, direction)




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
