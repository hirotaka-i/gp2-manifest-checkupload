# Loads libraries required for the app
import streamlit as st
import sys
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import tableone as tab1

sys.path.append('utils')
from writeread import read_filev2, read_file
from customcss import load_css
from qcutils import data_naproc


pd.set_option('display.max_rows', 1000)

def app():
    load_css("apps/css/css.css")
    #load_css("/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/apps/css/css.css")
    st.markdown('<p class="big-font">GP2 Data Visualization Tool</p>', unsafe_allow_html=True)
    st.sidebar.title("Options")

    # Load data and do na processing
    keep = ['sample_id', 'study', 'study_arm', 'diagnosis', 'sex',
            'race', 'age', 'age_of_onset', 'age_at_diagnosis', 'age_at_death', 'age_at_last_follow_up', 
            'family_history', 'visit_month', 'mds_updrs_part_iii_summary_score', 'moca_total_score', 
            'hoehn_and_yahr_stage', 'mmse_total_score']

    #dict_mapper = pd.read_excel('/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/apps/data/dict_mapper.xlsx')
    dict_mapper = pd.read_excel('apps/data/dict_mapper.xlsx')
    df_qc = None

    if not [x for x in (st.session_state['smqc'], st.session_state['clinqc']) if x is None]:
        df_merged = st.session_state['clinqc'].merge(st.session_state['smqc'], how = 'inner', on =  ['sample_id', 'study'])
        if not df_merged.shape[0] == 0:
            df_qc, cols_qc = data_naproc(df_merged[keep])
            mapper = {key:val for key,val in zip(dict_mapper['Item'], dict_mapper['ItemType']) if key in cols_qc}
            df_qc = df_qc.astype(mapper)
        else:
            st.error('We could not find matching sample ids between the clinical data and sample manifest')
            st.error('Please, revise your sample manifest. If there are matching sample ids, please contact GP2')
            st.stop()
    else:
        sm_file = st.sidebar.file_uploader("Upload Sample Manifest (CSV/XLSX)", type=['csv', 'xlsx'])
        clinical_file = st.sidebar.file_uploader("Upload Clinical data (CSV/XLSX)", type=['csv', 'xlsx'])
        if (sm_file is not None) and (clinical_file is not None):
            sm = read_file(sm_file)
            clin = read_file(clinical_file)
            
            # Check the sm and clin have the right formats
            if len(list(clin.columns)) != 7:
                st.error(' This does not seem like the QC clinical data')
                st.error('We have detected an unexpected number of columns')
                st.error(' Please QC the clinical data and come back')
                st.stop()            
            if len(list(sm.columns)) != 33:
                st.error(' This does not seem like the QC clinical data')
                st.error('We have detected an unexpected number of columns')
                st.error(' Please QC the clinical data and come back')
                st.stop()

            sm[['sample_id']] = sm[['sample_id']].astype(str)
            clin[['sample_id']] = clin[['sample_id']].astype(str)

            try:
                df_merged = sm.merge(clin , how = 'inner', on =  ['sample_id', 'study'])
            except:
                st.error('We were unable to match the clinical data and the sample manifest')
                st.error('Please make sure you upload the correct files')
                st.stop()

            if not df_merged.shape[0] == 0:
                try:
                    df_merged_filt = df_merged[keep]
                except:
                    diffcols = np.setdiff1d(keep, list(df_merged.columns))
                    st.error(' Please make sure you have qced both the sample manifest and clinical data before uploading the date')
                    st.error('Refer to the QC tabs and then come back to visualise your QC ed data')
                    st.error(f"Affected columns {diffcols}")
                    st.error('Contact the GP2 team if you need assistance')
                    st.error('CIAO')
                    st.stop()
            
                df_qc, cols_qc = data_naproc(df_merged_filt)
                mapper = {key:val for key,val in zip(dict_mapper['Item'], dict_mapper['ItemType']) if key in cols_qc}
                df_qc = df_qc.astype(mapper)
            else:
                st.error('We could not find matching sample ids between the clinical data and sample manifest')
                st.error('Please, revise your sample manifest. If there are matching sample ids, please contact GP2')
                st.stop()

    if df_qc is not None:
        if ('age_at_diagnosis' in df_qc.columns) and ('age' in df_qc.columns):
            df_qc["Dx_Diagnosis"] = df_qc["age"] - df_qc["age_at_diagnosis"]
            mapper["Dx_Diagnosis"] = 'int64'
        if ('age_of_onset' in df_qc.columns) and ('age' in df_qc.columns):
            df_qc["Dx_Onset"] = df_qc["age"] - df_qc["age_of_onset"]
            mapper["Dx_Onset"] = 'int64'

        # Group all variables present on categoric and numeric
        grouped_dict = {}
        #TODO Get the grouped dict to plot the histogram 
        for key, value in mapper.items():
            if value not in grouped_dict:
                grouped_dict[value] = [key]
            else:
                grouped_dict[value].append(key)
        nnml = grouped_dict.get('int64')
        cats = grouped_dict.get('str')

        unique_months = list(df_qc.visit_month.unique())
        if 0 not in unique_months:
            viz = st.sidebar.selectbox("Choose a Visualization", ["Tables", "Scatter Plot",
                                                                  "Bar Graph",
                                                                  "Line Plot"])
        else:
            viz = st.sidebar.selectbox("Choose a Visualization", ["Tables", "Scatter Plot",
                                                                  "Bar Graph","Baseline Histogram",
                                                                  "Line Plot"])

        df_plot = df_qc.copy()
        ###----------------------------------------------------------------------------------------------###
        ###The following code is responsible for producing the demographic summarization table
        ###----------------------------------------------------------------------------------------------'''
        if viz == "Tables":       
            foc = st.sidebar.selectbox("Select a Focus", ["Overall", "Demographic", "Clinical"])
            gby = st.sidebar.selectbox("Stratifying Variable", ["None", "study_arm", "study", 'diagnosis'])
            if foc == "Overall":
                columns = cats + nnml
                # columns containing categorical variables
                categorical = cats
                # non-normal variables
                nonnormal = nnml
                columns.remove('sample_id')
                categorical.remove('sample_id')
            if foc == "Demographic":
                # columns to summarize
                columns_demo = ['sex', 'diagnosis', 'study_arm', 'race', 
                                'age', 'age_of_onset', 'age_at_diagnosis', 'age_at_death', 'age_at_last_follow_up'
                                'family_history', 'visit_month', 'Dx_Diagnosis', 'Dx_Onset']
                            # columns = ['study', 'study_arm', 'diagnosis', 'sex',
                            # 'race', 'age', 'age_of_onset', 'age_at_diagnosis', 'age_at_death', 'age_at_last_follow_up', 
                            # 'family_history', 'visit_name', 'mds_updrs_part_iii_summary_score', 'moca_total_score', 
                            # 'hoehn_and_yahr_stage', 'mmse_total_score']
                columns_present = cats + nnml
                columns = [i for i in columns_demo if i in columns_present]
                categorical = [i for i in columns if i in cats]
                nonnormal = [i for i in nnml if i in nnml]

            if foc == "Clinical":
                # columns to summarize
                columns = ['mds_updrs_part_iii_summary_score', 
                            'moca_total_score','hoehn_and_yahr_stage', 'mmse_total_score']
                            # columns = ['study', 'study_arm', 'diagnosis', 'sex',
                            # 'race', 'age', 'age_of_onset', 'age_at_diagnosis', 'age_at_death', 'age_at_last_follow_up', 
                            # 'family_history', 'visit_name', 'mds_updrs_part_iii_summary_score', 'moca_total_score', 
                            # 'hoehn_and_yahr_stage', 'mmse_total_score']
                #columns_present = cats + nnml
                nonnormal = columns
                categorical = []

            # set the order of the categorical variables
            order = dict()
            for col in columns:
                if "Yes" in list(df_plot.loc[:, col].unique()):
                    order[col] = ["Yes", "No", "Unknown"]
            # if not columns:
            #     st.warning("No Variable Has Been Selected")
            
            df_plot = df_plot.drop_duplicates(subset="sample_id", keep="first")
            df_plot.replace('999', np.nan, inplace=True)
            df_plot.replace('999.0', np.nan, inplace=True)
            df_plot.replace(999, np.nan, inplace=True)
            #df_plot = df_plot.loc[~(df_plot[columns]== 999).any(axis=1)]
            #df_plot = df_plot.loc[~(df_plot[columns]== "999").any(axis=1)]
            #df_plot = df_plot.loc[~(df_plot[columns]== "999.0").any(axis=1)]
            if gby == "None":
                dt = tab1.TableOne(df_plot, 
                                columns=columns, categorical=categorical, nonnormal=nonnormal, order=order)
            else:
                dt = tab1.TableOne(df_plot, 
                                columns=columns, categorical=categorical, nonnormal=nonnormal, 
                                groupby=gby, order=order)
            st.write(dt)


        if viz == "Scatter Plot":
            xax = st.sidebar.selectbox("Select an x-axis variable", df_plot.columns[df_plot.columns.isin(nnml)])
            yax = st.sidebar.selectbox("Select a y-axis variable", df_plot.columns[df_plot.columns.isin(nnml)])
            
            if st.sidebar.checkbox("Include only Baseline?"):
                df_plot = df_plot[df_plot.visit_month == 0]
            #st.write(df_plot)
            df_plot = df_plot.loc[~(df_plot[[xax, yax]] == 999).any(axis=1)]
            tl = None
            #st.write(df_plot)
            if st.sidebar.checkbox("Add Trendline?"):
                tl = st.sidebar.selectbox("Select Trendline Type", ["ols", "lowess"])
            
            if st.sidebar.checkbox("Stratify Based on Third Variable?"):
                cs = st.sidebar.selectbox("Select a stratifying variable", df_plot.columns[df_plot.columns.isin(cats)])
                df_plot = df_plot.loc[~(df_plot[[cs]] == 999).any(axis=1)]
                fig = px.scatter(df_plot, x=xax, y=yax, color=cs, opacity=0.5, trendline=tl)
            else:
                fig = px.scatter(df_plot, x=xax, y=yax, opacity=0.5, trendline=tl)
            st.write(fig)


        ###----------------------------------------------------------------------------------------------###
        ###The following code is reponsible for producing histograms for baseline variables
        ###----------------------------------------------------------------------------------------------###
        if viz == "Baseline Histogram":
            var = st.sidebar.selectbox("Pick a variable to visualize", nnml)
            counts = st.sidebar.checkbox("Convert to Percent Histogram")
            df_plot = df_plot[df_plot.visit_month == 0]
            df_plot = df_plot.loc[~(df_plot[[var]] == 999).any(axis=1)]
            #df_plot = df_plot.loc[~(df_plot[[var]] == 999)]
            #if var not in df_plot.columns:
            #    st.write("This variable is not supported in the selected dataset")
            strat = st.sidebar.selectbox("Pick a Stratifier", ["None"] + list(nnml) ) #ist(d.columns[7:]))

            if var in nnml:
                nb = st.sidebar.slider("Number of Bins", 1, 25, 50, step=1)
            else:
                nb = len(df_plot.loc[:,var].unique())

            if strat == "None":
                fig = px.histogram(df_plot, x=var, nbins=nb)

                if counts == True:
                    fig = px.histogram(df_plot, x=var, barnorm="percent", nbins=nb)
            elif counts == True:
                #df_plot = df_plot.dropna(subset=[var, strat])
                df_plot = df_plot.loc[~(df_plot[[var,strat]] == 999).any(axis=1)]
                fig = px.histogram(df_plot, x=var, barnorm="percent", color=strat, nbins=nb)
            else:
                #df_plot = df_plot.dropna(subset=[strat])
                #df_plot = df_plot.loc[~(df_plot[[strat]] == 999).any(axis=1)]
                #df_plot = df_plot.loc[~(df_plot[[strat]] == 999)]
                df_plot = df_plot.loc[~(df_plot[[strat]] == 999).any(axis=1)]
                fig = px.histogram(df_plot, x=var, color=strat, nbins=nb)
            st.write(fig)


        ###----------------------------------------------------------------------------------------------###
        ###The following code is reponsible for producing the new stacked bar graphs
        ###----------------------------------------------------------------------------------------------###
        if viz == "Bar Graph":
            nnml_bar = [i for i in nnml if 'total' in i 
                            or 'summary' in i 
                            or 'hoehn' in i]
            var = st.sidebar.selectbox("Pick a y-axis", cats)
            bl = st.sidebar.selectbox("Pick an x-axis", nnml_bar)
            df_plot = df_plot.loc[~(df_plot[[bl,var]] == 999).any(axis=1)]
            strat_bar = ['None'] + [i for i in cats if 'sex' in i 
                                        or 'age' in i 
                                        or 'study_arm' in i
                                        or 'cohort' in i]
            strat = st.sidebar.selectbox("Pick a Stratifier", strat_bar)
            counts = st.sidebar.selectbox("Pick a Histogram Type", ["Count", "Percent"])
            nb = st.sidebar.slider("Number of Bins", 1, 25, 50, step=1)
            #df_plot = df_plot.dropna(subset=[var])
            #if bl in ["yearsDx", "yearsB"]:
            #    df_plot = df_plot.drop_duplicates(subset=["sample_id", var])
            # if var not in df_plot.columns:
            #     st.write("This variable is not supported in the selected dataset")
            if counts == "Percent":
                if strat == "None":
                    fig = px.histogram(df_plot, x=bl, color=var, barnorm="percent",
                                    nbins=nb)
                else:
                    df_plot = df_plot.loc[~(df_plot[[strat]] == 999).any(axis=1)]
                    fig = px.histogram(df_plot.dropna(subset=[strat]), 
                                    facet_col=strat, x=bl, color=var, barnorm="percent", nbins=nb)
            if counts == "Count":
                if strat == "None":
                    fig = px.histogram(df_plot, x=bl, color=var,
                                    nbins=nb)
                else:
                    df_plot = df_plot.loc[~(df_plot[[strat]] == 999).any(axis=1)]
                    fig = px.histogram(df_plot.dropna(subset=[strat]), 
                                    facet_col=strat, x=bl, color=var, nbins=nb)
            st.write(fig)


        ###----------------------------------------------------------------------------------------------###
        ###The following code is reponsible for producing the line plot
        ###----------------------------------------------------------------------------------------------###
        if viz == "Line Plot":
            alt.data_transformers.enable('default', max_rows=None)
            nnml_opts = [i for i in nnml if 'total' in i 
                            or 'summary' in i 
                            or 'hoehn' in i]
            var = st.sidebar.selectbox("Pick a Variable", nnml_opts)
            
            bl_opts = [i for i in nnml if i=='Dx_Diagnosis' or i=='Dx_Onset'] 
            #st.write(bl_opts)       
            bl = st.sidebar.selectbox("Select a Baseline", bl_opts)

            df_plot = df_plot.loc[~(df_plot[[var]] == 999).any(axis=1)]

            #bl_name = "study_arm" if bl == "Study Baseline" else "diagnosis"
            #bl_val = "yearsB" if bl == "Study Baseline" else "yearsDx"
            
            # if var == "HY":
            #     # Plot for HY

            # if var == "All UPDRS":
            #     alt.data_transformers.enable('default', max_rows=None)

            #     source = pd.DataFrame({
            #         'Years Since ' + bl_name: d[bl_val],
            #         'UPDRS1': d["UPDRS1"],
            #         'UPDRS2': d["UPDRS2"],
            #         'UPDRS3': d["UPDRS3"],
            #     })

            #     base = alt.Chart(source).mark_circle(opacity=0, color='white').transform_fold(
            #         fold=['UPDRS1', 'UPDRS2', 'UPDRS3'],
            #         as_=['category', 'UPDRS Score']
            #     ).encode(
            #         alt.X(('Years Since ' + bl_name + ':Q'),
            #             axis=alt.Axis(grid=False)),
            #         alt.Y('UPDRS Score:Q',
            #             axis=alt.Axis(grid=False)),
            #         alt.Color('category:N')
            #     ).properties(width=750, height=500)
            #     # Creating 95 CI
            #     band = alt.Chart(source).mark_errorband(extent='ci').transform_fold(
            #         fold=['UPDRS1', 'UPDRS2', 'UPDRS3'],
            #         as_=['category', 'UPDRS Score']
            #     ).encode(
            #         alt.X(('Years Since ' + bl_name + ':Q'),
            #             axis=alt.Axis(grid=False)),
            #         alt.Y('UPDRS Score:Q',
            #             axis=alt.Axis(grid=False)),
            #         alt.Color('category:N')
            #     )
            #     base = base + band + base.transform_loess(('Years Since ' + bl_name), 'UPDRS Score',
            #                                             groupby=['category']).mark_line(size=4)

            #     st.altair_chart(base)
            #else:
            alt.data_transformers.enable('default', max_rows=None)
            source = pd.DataFrame({
                #('Years Since ' + bl_name): dd_qc[bl_val],
                ('Years Since ' + bl): df_plot[bl],
                var: df_plot.loc[:, var]
            })
            #st.write(source)
            base = alt.Chart(source)\
                    .mark_circle(opacity=0, color='white')\
                    .encode(
                            alt.X(('Years Since ' + bl + ':Q'),axis=alt.Axis(grid=False)),
                            alt.Y((var + ':Q'), axis=alt.Axis(grid=False)))\
                    .properties(width = 750, height = 500)

            # Creating 95 CI
            band = alt.Chart(source)\
                    .mark_errorband(extent='ci', color ='green')\
                    .encode(
                            alt.X(('Years Since '+ bl +':Q'), axis=alt.Axis(grid=False)),
                            alt.Y((var+':Q'), axis=alt.Axis(grid=False)))
        
            base = base + band+ base.transform_loess(('Years Since'+ bl), var,
                                            groupby=['category']).mark_line(size=4, color="red")

            st.altair_chart(base)