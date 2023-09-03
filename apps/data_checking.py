try:
    import streamlit as st
    from streamlit.components.v1 import html
    import os
    import sys
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    from st_aggrid import AgGrid, GridOptionsBuilder

    sys.path.append('utils')
    import generategp2ids
    from customcss import load_css
    from writeread import read_filev2, to_excelv2, read_file, to_excel

    #from io import BytesIO
    #import xlsxwriter
    #from google.cloud import storage
    #import base64
    #import datetime as dt
    #import ijson
    #import json
except Exception as e:
    print("Some modules are not installed {}".format(e))

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/secrets/secrets.json"
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/secrets/secrets.json"

def jumptwice():
    st.write("##")
    st.write("##")

def aggridPlotter(df):
    df_builder = GridOptionsBuilder.from_dataframe(df)
    df_builder.configure_grid_options(alwaysShowHorizontalScroll = True,
                                        enableRangeSelection=True,
                                        pagination=True,
                                        paginationPageSize=10000,
                                        domLayout='normal')
    godf = df_builder.build()
    AgGrid(df,gridOptions=godf, theme='streamlit', height=300)

def app():
    #load_css("/app/apps/css/css.css")
    load_css("/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/apps/css/css.css")

    st.markdown("""<div id='link_to_top'></div>""", unsafe_allow_html=True)
    st.markdown('<p class="big-font">GP2 sample manifest self-QC</p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> This is a app tab to self-check the sample manifest and clinical data. </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Download the template from the link below. Once you open the link, go to "File"> "Download" > "xlsx" or "csv" format </p>', unsafe_allow_html=True)
    st.markdown('[Access the data dictionary and templates](https://docs.google.com/spreadsheets/d/19L5EgSsvax4qBWa6iPUCSD3FUm7T9Ux3V8Ptdt6Dtuk/edit#gid=520666050)', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Please refer to the second tab (Dictionary) for instructions. </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Please refer to the first tab (sm) to access sample manifest template to fill in. </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Please note all the GP2 required columns must be completed </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Once you have filled in all the columns avavailable in your cohort, please upload the manifest on the side bar to start the QC process </p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font"> Once the QC process completes, please move to the Upload tab of the app to store your sample manifest </p>', unsafe_allow_html=True)

    data_file = st.sidebar.file_uploader("Upload Your Sample manifest (CSV/XLSX)", type=['xlsx', 'csv'])
    menu = ["For Fulgent", "For NIH", "For LGC", "For UCL", "For DZNE"]
    choice = st.sidebar.selectbox("Genotyping site",menu)

    ph_conf=''
    sex_conf=''
    race_conf = ''
    fh_conf=''
    cols = ['study', 'sample_id', 'sample_type',
            'DNA_volume', 'DNA_conc', 'r260_280',
            'Plate_name', 'Plate_position', 'clinical_id',
            'study_arm', 'diagnosis', 'sex', 'race',
            'age', 'age_of_onset', 'age_at_diagnosis', 'age_at_death', 'age_at_last_follow_up',
            'family_history', 'region', 'comment', 'alternative_id1', 'alternative_id2']
    required_cols = ['study', 'sample_id', 'sample_type', 'clinical_id','study_arm', 'diagnosis', 'sex']
    allowed_samples = ['Blood (EDTA)', 'Blood (ACD)', 'Blood', 'DNA',
                        'DNA from blood', 'DNA from FFPE', 'RNA', 'Saliva',
                        'Buccal Swab', 'T-25 Flasks (Amniotic)', 'FFPE Slide',
                        'FFPE Block', 'Fresh tissue', 'Frozen tissue',
                        'Bone Marrow Aspirate', 'Whole BMA', 'CD3+ BMA', 'Other']
    fulgent_cols = ['DNA_volume', 'DNA_conc', 'Plate_name', 'Plate_position']

    allowed_samples_strp = [samptype.strip().replace(" ", "") for samptype in allowed_samples]

    if data_file is not None:
        jumptwice()
        df = read_file(data_file)
        df.index = df.index +2
        jumptwice()

        st.markdown('<p class="big-font">Sample manifest QC </p>', unsafe_allow_html=True)
        df['Genotyping_site'] = choice.replace('For ', '')
        if choice=='For Fulgent':
            required_cols = required_cols + fulgent_cols

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

        # sample type check
        st.text('sample_type check')
        st.write(df.sample_type.astype('str').value_counts())
        not_allowed = np.setdiff1d(df.sample_type.unique(), allowed_samples)
        if len(not_allowed)>0:
            sampletype = df.sample_type
            sampletype = sampletype.str.strip().replace(" ", "")
            not_allowed_v2 = np.setdiff1d(sampletype.unique(), allowed_samples_strp)

            if len(not_allowed_v2) < len(not_allowed):
                st.text('We have found some undesired whitespaces in some sample type values.')
                st.text('Processing whitespaces found in certain sample_type entries')
                stype_map = dict(zip(allowed_samples_strp, allowed_samples))
                newsampletype = sampletype.replace(stype_map)
                df['sample_type'] = newsampletype
                st.text('sample type count after removing undesired whitespaces')
                st.write(df.sample_type.astype('str').value_counts())

                if len(not_allowed_v2)>0:
                    st.text('In addition, we have found unknown sample types')
                    st.error(f'sample_type: {not_allowed_v2} not allowed.')
                    sample_list = '\n * '.join(allowed_samples)
                    st.text('Writing entries with sample_type not allowed')
                    st.write(df[df['sample_type'].isin(not_allowed_v2)])
                    st.text(f'Allowed sample list - \n * {sample_list}')
                    st.stop()

        # Convert sample and clinical id to strings
        df[['sample_id', 'clinical_id']] = df[['sample_id','clinical_id']].astype(str)
        sample_id_dup = df.sample_id[df.sample_id.duplicated()].unique()
        # sample dup check
        if len(sample_id_dup)>0:
            st.text(f'Duplicated sample_id:{sample_id_dup}')
            st.error(f'Unique sample IDs are required (clinical IDs can be duplicated if replicated)')
            st.stop()
        else:
            st.text(f'Check sample_id duplicaiton --> OK')
            st.text(f'N of sample_id (entries):{df.shape[0]}')
            st.text(f'N of unique clinical_id : {len(df.clinical_id.unique())}')
        
        
        
        # GENERATE GP2 IDs #
        jumptwice()
        st.subheader('GP2 IDs assignment...')
        studynames = list(df['study'].unique())

        if st.session_state['master_get'] == None: # TO ONLY RUN ONCE
            #ids_tracker = generategp2ids.master_key(studies = studynames)
            ids_tracker = generategp2ids.master_keyv2(studies = studynames)
            study_subsets = []
            log_new = []
            df['GP2sampleID'] = None
            # GP2 ID ASSIGNMENT CODE BLOCK
            for study in studynames:
                st.write(f"Getting GP2IDs for {study} samples")
                df_subset = df[df.study==study].copy()
                try:
                    #study_tracker = st.session_state['store_tracker'][study]
                    study_tracker = ids_tracker[study]
                    study_tracker_df = pd.DataFrame.from_dict(study_tracker,
                                                            orient='index',
                                                            columns = ['master_GP2sampleID','clinical_id'])\
                                                    .rename_axis('master_sample_id').reset_index()\
                                                    .astype(str)

                    # Check if any sample ID exists in df_subset.
                    sample_id_unique = pd.merge(study_tracker_df, df_subset,
                                                left_on=['master_sample_id'], right_on=['sample_id'], how='inner')
                    if not sample_id_unique.empty:
                        st.error('We have detected sample ids submitted on previous versions')
                        st.error('Please, correct these sample IDs so that they are unique and resubmit the sample manifest.')
                        sample_id_unique = sample_id_unique.rename(columns={"clinical_id_y": "clinical_id"})
                        st.dataframe(
                        sample_id_unique[['study','sample_id','clinical_id']].style.set_properties(**{"background-color": "brown", "color": "lawngreen"})
                        )
                        stopapp=True
                    else:
                        stopapp=False
                except:
                    study_tracker = None
                    stopapp = False
                if stopapp:
                    st.stop()

                if bool(study_tracker):
                    # WORK ON DUPLICATED IDS
                    df_subset = df_subset.reset_index()
                    data_duplicated = pd.merge(df_subset, study_tracker_df, on=['clinical_id'], how='inner')
                    df_subset = df_subset.set_index('index')
                    df_subset.index.name = None

                    if data_duplicated.shape[0]>0:
                        new_clinicaldups = True
                        newids_clinicaldups = data_duplicated.groupby('clinical_id')\
                                                        .apply(lambda x: generategp2ids.assign_unique_gp2clinicalids(df_subset,x))

                        if newids_clinicaldups.shape[0]>0:
                            newids_clinicaldups = newids_clinicaldups.reset_index(drop=True)[['study','clinical_id','sample_id','GP2sampleID']]
                            log_new.append(newids_clinicaldups)
                    else:
                        new_clinicaldups = False
                        newids_clinicaldups = pd.DataFrame()

                    # GET GP2 IDs METADATA for new CLINICAL-SAMPLE ID pairs
                    df_newids = df_subset[df_subset['GP2sampleID'].isnull()].reset_index(drop = True).copy()
                    if not df_newids.empty: # Get new GP2 IDs
                        df_wids = df_subset[~df_subset['GP2sampleID'].isnull()].reset_index(drop = True).copy()
                        df_wids['GP2ID'] = df_wids['GP2sampleID'].apply(lambda x: ("_").join(x.split("_")[:-1]))
                        df_wids['SampleRepNo'] = df_wids['GP2sampleID'].apply(lambda x: x.split("_")[-1])#.replace("s",""))

                        n=int(max(study_tracker_df['master_GP2sampleID'].to_list()).split("_")[1])+1
                        df_newids = generategp2ids.getgp2idsv2(df_newids, n, study)
                        df_subset = pd.concat([df_newids, df_wids], axis = 0)
                        study_subsets.append(df_subset)
                        log_new.append(df_newids[['study','clinical_id','sample_id','GP2sampleID']])
                        
                    else: # TO CONSIDER THE CASE IN WHICH WE ONLY HAD DUPLICATE IDS MAPPED ON THE MASTER FILE
                        df_subset['GP2ID'] = df_subset['GP2sampleID'].apply(lambda x: ("_").join(x.split("_")[:-1]))
                        df_subset['SampleRepNo'] = df_subset['GP2sampleID'].apply(lambda x: x.split("_")[-1])#.replace("s",""))
                        study_subsets.append(df_subset)

                # Brand new data - NO STUDY TRACKER FOR THIS COHORT
                else:
                    study = study
                    new_clinicaldups = False # Duplicates from master key json are treated differently to brand new data
                    n = 1
                    df_newids = generategp2ids.getgp2idsv2(df_subset, n, study)
                    study_subsets.append(df_newids)


                # CODE TO UPDATE THE GET FILE WE WILL USE TO UPDATE MASTER JSON
                if (new_clinicaldups) and (newids_clinicaldups.shape[0]>0):
                    tmp = pd.concat([df_newids[['study','clinical_id','sample_id','GP2sampleID']], newids_clinicaldups])
                    tmp['master_value'] = list(zip(tmp['GP2sampleID'],
                                                    tmp['clinical_id']))
                    ids_log = tmp.groupby('study').apply(lambda x: dict(zip(x['sample_id'],
                                                                            x['master_value']))).to_dict()
                else:
                    df_update_master = df_newids.copy()
                    df_update_master['master_value'] = list(zip(df_update_master['GP2sampleID'],
                                                            df_update_master['clinical_id']))
                    ids_log = df_update_master.groupby('study').apply(lambda x: dict(zip(x['sample_id'],
                                                                                    x['master_value']))).to_dict()

                #generategp2ids.update_masterids(ids_log, study_tracker) # THIS WILL BE UPDATED ONCE THE USET CONFIRMS THE QC ( AT THE END)
                
                #if st.session_state['master_get'] == None:
                if (isinstance(st.session_state['all_ids'], list)):
                    st.session_state['all_ids'].append( [ids_log, study_tracker] )
                if st.session_state['all_ids'] == None:
                    st.session_state['all_ids'] = [ [ids_log, study_tracker] ]
            

            # OUT OF FOR LOOP // END OF GP2 IDS ASSIGNMENT. LET'S RESUME df.
            df = pd.concat(study_subsets, axis = 0)
            df = df[list(df)[-3:] + list(df)[:-3]]
            st.write("GPS IDs assignment... OK")

            #if st.session_state['master_get'] == None:
            st.session_state['df_copy'] = df
            if len(log_new) > 0:
                allnew = pd.concat(log_new, axis = 0).reset_index(drop=True)
                st.write("Thanks for uploading a new version of the sample manifest")
                st.write(f'We have detected a total of {allnew.shape[0]} new samples')
                st.write("We have assigned new GP2IDs to those. Showing them below...")
                st.dataframe(
                allnew.style.set_properties(**{"background-color": "brown", "color": "lawngreen"})
                #allnew.style.set_properties(**{"background-color": "brown", "color": "lawngreen"})
                )
            else:
                aggridPlotter(df)

            st.session_state['df_finalids'] = df
            st.session_state['master_get'] = 'DONE'

        else:
            df = st.session_state['df_finalids']
            aggridPlotter(df)
            # df_builder = GridOptionsBuilder.from_dataframe(st.session_state['df_copy'])
            # df_builder.configure_grid_options(alwaysShowHorizontalScroll = True,
            #                                     enableRangeSelection=True,
            #                                     pagination=True,
            #                                     paginationPageSize=10000,
            #                                     domLayout='normal')
            # godf = df_builder.build()
            # AgGrid(st.session_state['df_copy'],gridOptions=godf, theme='streamlit', height=300)
            #df = st.session_state['df_finalids']
        #st.session_state['master_get'] = 'DONE'

        jumptwice()
        # diagnosis --> Phenotype
        st.subheader('Create "Phenotype"')
        st.text('Show study arm versus diagnosis')
        # Add xtab for diagnosis vs study arm
        xtab = df.pivot_table(index='study_arm', columns='diagnosis', margins=True,
                            values='sample_id', aggfunc='count', fill_value=0)
        st.write(xtab)

        jumptwice()
        st.text('Count per diagnosis')
        st.write(df.diagnosis.astype('str').value_counts())

        jumptwice()
        diag = df.diagnosis.dropna().unique()
        n_diag = st.columns(len(diag))
        phenotypes={}
        for i, x in enumerate(n_diag):
            with x:
                mydiag = diag[i]
                phenotypes[mydiag]=x.selectbox(f"[{mydiag}]: For QC, please pick the closest Phenotype",["PD", "Control", "Prodromal", \
                                                                                                        "Other", "Not Reported", "MSA", \
                                                                                                        "PSP", "DLB", "CBS", "AD", "FTD", "VSC"],
                                                                                                        key=i)

        df['Phenotype'] = df.diagnosis.map(phenotypes)
        # cross-tabulation of diagnosis and Phenotype
        st.text('=== Phenotype x diagnosis===')
        xtab = df.pivot_table(index='Phenotype', columns='diagnosis', margins=True,
                                values='sample_id', aggfunc='count', fill_value=0)
        st.write(xtab)

        ph_conf = st.checkbox('Confirm Phenotype?')
        if ph_conf:
            st.info('Thank you')

        # Get QCed Phenotype and map it to PD, Control, Other
        pattern_other = '|'.join(['Prodromal', 'NotReported', 'MSA', 'PSP', 'DLB', 'CBS', 'AD'])
        df['phenotype_for_qc'] = df['Phenotype'].str.replace(" ", "").str.replace(pattern_other, 'Other')


        # sex for qc
        jumptwice()
        st.subheader('Create "biological_sex_for_qc"')
        st.text('Count per sex group')
        st.write(df.sex.astype('str').value_counts())

        jumptwice()
        sexes=df.sex.dropna().unique()
        n_sexes = st.columns(len(sexes))
        mapdic={}
        for i, x in enumerate(n_sexes):
            with x:
                sex = sexes[i]
                mapdic[sex]=x.selectbox(f"[{sex}]: For QC, please pick a word below",
                                    ["Male", "Female", "Other/Unknown/Not Reported"], key=i)
        df['biological_sex_for_qc'] = df.sex.replace(mapdic)

        # cross-tabulation
        st.text('=== biological_sex_for_qc x sex ===')
        xtab = df.pivot_table(index='biological_sex_for_qc', columns='sex', margins=True,
                                values='sample_id', aggfunc='count', fill_value=0)
        st.write(xtab)

        sex_conf = st.checkbox('Confirm biological_sex_for_qc?')
        if sex_conf:
            st.info('Thank you')

            if 'Other/Unknown/Not Reported' in df['biological_sex_for_qc'].unique():
                sex_count = df['biological_sex_for_qc'].value_counts()
                unknown_rate = sex_count['Other/Unknown/Not Reported'] / df.shape[0]
                if unknown_rate > 0.01:
                    st.text("The number of samples with \"Other/Unknown/Not Reported\" sex category is higher than 1% ")
                    st.warning("Please check that you selected the right sex values for your samples above ")


        # race for qc
        jumptwice()
        st.subheader('Create "race_for_qc"')
        st.text('Count per race (Not Reported = missing)')
        df['race_for_qc'] = df.race.fillna('Not Reported')
        st.write(df.race_for_qc.astype('str').value_counts())

        jumptwice()
        races = df.race.dropna().unique()
        nmiss = sum(pd.isna(df.race))

        if nmiss>0:
            st.text(f'{nmiss} entries missing race...')

        mapdic = {'Not Reported':'Not Reported'}
        for race in races:
            mapdic[race]=st.selectbox(f"[{race}]: For QC purppose, select the best match from the followings",
            ["American Indian or Alaska Native", "Asian", "White", "Black or African American",
            "Multi-racial", "Native Hawaiian or Other Pacific Islander", "Other", "Unknown", "Not Reported"])
        df['race_for_qc'] = df.race_for_qc.map(mapdic)


        # cross-tabulation
        st.text('=== race_for_qc X race ===')
        dft = df.copy()
        dft['race'] = dft.race.fillna('_Missing')
        xtab = dft.pivot_table(index='race_for_qc', columns='race', margins=True,
                                values='sample_id', aggfunc='count', fill_value=0)
        st.write(xtab)

        race_conf = st.checkbox('Confirm race_for_qc?')
        if race_conf:
            st.info('Thank you')


        # family history for qc
        jumptwice()
        st.subheader('Create "family_history_for_qc"')
        st.text('Count per family_history category (Not Reported = missing)')
        df['family_history_for_qc'] = df.family_history.fillna('Not Reported')
        st.write(df.family_history_for_qc.astype('str').value_counts())
        family_historys = df.family_history.dropna().unique()
        nmiss = sum(pd.isna(df.family_history))

        if nmiss>0:
            st.text(f'{nmiss} entries missing family_history')
        mapdic = {'Not Reported':'Not Reported'}
        jumptwice()

        if len(family_historys)>0:
            n_fhs = st.columns(len(family_historys))
            for i, x in enumerate(n_fhs):
                with x:
                    fh = family_historys[i]
                    mapdic[fh]=x.selectbox(f'[{fh}]: For QC, any family history?',['Yes', 'No', 'Not Reported'], key=i)
        df['family_history_for_qc'] = df.family_history_for_qc.map(mapdic).fillna('Not Assigned')


        # cross-tabulation
        st.text('=== family_history_for_qc X family_history ===')
        dft = df.copy()
        dft['family_history'] = dft.family_history.fillna('_Missing')
        xtab = dft.pivot_table(index='family_history_for_qc', columns='family_history', margins=True,
                                values='sample_id', aggfunc='count', fill_value=0)
        st.write(xtab)

        fh_conf = st.checkbox('Confirm family_history_for_qc?')
        if fh_conf:
            st.info('Thank you')


        # Region for qc
        jumptwice()
        st.subheader('Create "region_for_qc"')
        st.text('Count per region (Not Reported = missing)')
        df['region_for_qc'] = df.region.fillna('Not Reported')
        st.write(df.region_for_qc.astype('str').value_counts())
        regions = df.region.dropna().unique()
        nmiss = sum(pd.isna(df.region))

        if nmiss>0:
            st.text(f'{nmiss} entries missing for region')
        mapdic = {'Not Reported':'Not Reported'}
        jumptwice()

        if len(regions)>0:
            st.text('if ISO 3166-3 is available for the region, please provide')
            st.write('https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3')
            n_rgs = st.columns(len(regions))
            for i, x in enumerate(n_rgs):
                with x:
                    region = regions[i]
                    region_to_map = x.text_input(f'[{region}] in 3 LETTER (or NA)')
                    if len(region_to_map)>1:
                        mapdic[region]=region_to_map
        df['region_for_qc'] = df.region_for_qc.map(mapdic).fillna('Not Assigned')

        # cross-tabulation
        st.text('=== region_for_qc X region ===')
        dft = df.copy()
        dft['region'] = dft.region.fillna('_Missing')
        xtab = dft.pivot_table(index='region_for_qc', columns='region', margins=True,
                                values='sample_id', aggfunc='count', fill_value=0)
        st.write(xtab)

        rg_conf = st.checkbox('Confirm region_for_qc?')
        if rg_conf:
            if len(regions)!=(len(mapdic)-1):
                st.error('region not assigned.')
                st.text("Please, assing the region, and re upload the sample manifest")
                st.stop()
            else:
                st.info('Thank you')

        # Plate Info
        jumptwice()
        st.subheader('Plate Info')
        dft = df.copy()
        dft['Plate_name'] = dft.Plate_name.fillna('_Missing')
        xtab = dft.pivot_table(index='Plate_name',
                            columns='diagnosis', margins=True,
                            values='sample_id', aggfunc='count', fill_value=0)
        st.write(xtab)

        for plate in dft.Plate_name.unique():
            df_plate = dft[dft.Plate_name==plate].copy()
            df_plate_pos = df_plate.Plate_position
            # duplicated position check
            if plate!='_Missing':
                if len(df_plate_pos)>96:
                    st.error('Please make sure, N of samples on plate [{plate}] is =<96')
                    st.stop()
                dup_pos = df_plate_pos[df_plate_pos.duplicated()].unique()
                if len(dup_pos)>0:
                    st.error(f' !!!SERIOUS ERROR!!!  Plate position duplicated position {dup_pos} on plate [{plate}]')
                    st.stop()

        # Numeric values
        jumptwice()
        st.subheader('Numeric Values')
        numerics_cols = ['DNA_volume', 'DNA_conc', 'r260_280','age', 'age_of_onset', 'age_at_diagnosis', 'age_at_last_follow_up','age_at_death']
        for v in numerics_cols:
            if df.dtypes[v] not in ['float64', 'int64']:
                st.error(f'{v} is not numeric')
                st.text("Please, make sure expected numeric columns are stored on a numeric format")
                st.text(f'Expected columns in numeric format - \n * {numerics_cols}')
                st.stop()
        st.text('Numeric chek --> OK.')
        st.text('You can check the distribution with the button below')
        if st.button("Check Distribution"):
            for v in numerics_cols:
                nmiss = df[v].isna().sum()
                vuniq = df[v].dropna().unique()
                nuniq = len(vuniq)
                if nuniq==0:
                    st.text(f'{v} - All missing')
                elif nuniq==1:
                    st.text(f'{v} - One value = {vuniq[0]}, ({nmiss} entries missing)')
                elif nuniq <6:
                    st.write(df[v].value_counts(dropna=False))
                else:
                    st.text(f'{v} - histogram ({nmiss} entries missing)')
                    fig, ax_hist = plt.subplots(
                        figsize = (6,4)
                    )
                    ax_hist.grid(True)
                    sns.histplot(data = df, x = v,
                                    kde=True, color = "green",
                                    ax = ax_hist)
                    fig.set_tight_layout(True)
                    st.write(fig)
                    #st.pyplot(fig)

                jumptwice()

        if st.button("Finished?"):
            #if not (clinical_conf & ph_conf & sex_conf & race_conf & fh_conf & rg_conf):
            if not (ph_conf & sex_conf & race_conf & fh_conf & rg_conf):
                st.error('Did you forget to confirm any of the steps above?')
                st.error("Please, tick all the boxes on the previous steps if the QC to meet GP2 standard format was successful")
            else:
                # Update json file with master IDs
                #generategp2ids.update_masterids(ids_log, study_tracker)
                for idslog_tracker in st.session_state['all_ids']:
                    generategp2ids.update_masterids(idslog_tracker[0], idslog_tracker[1])

                df = df.reset_index(drop=True)
                #df_final = clin.merge(df, how = 'inner', on =  ['sample_id', 'study'])
                # Add data to session state
                #st.session_state['allqc'] = df_final
                st.session_state['smqc'] = df
                #st.session_state['clinqc'] = clin
                #st.session_state['dct_tmplt'] = dct

                # Generate excel sheet for download
                st.markdown('<p class="medium-font"> CONGRATS, your sample manifest meets all the GP2 requirements. </p>', unsafe_allow_html=True )
                #writeexcel = to_excelv2(df, clin, dct)
                writeexcel = to_excel(df, datatype = 'sm')
                #qcmanifest = output_create(df_final, filetype=output_choice)
                
                #from streamlit import caching
                from streamlit import legacy_caching
                import time
                #from streamlit.scriptrunner import RerunException
                def cach_clean():
                    time.sleep(1)
                    legacy_caching.clear_cache()

                
                st.download_button(label='📥 Download your QC sample manifest',
                                   data = writeexcel[0],
                                   file_name = writeexcel[1],
                                   on_click = cach_clean())
                
                
                # Set session state for master files to None
                #st.session_state['master_get'] = None

        jumptwice()
        st.markdown("<a href='#link_to_top'>Link to top</a>", unsafe_allow_html=True)
