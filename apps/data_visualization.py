# Loads libraries required for the app
import streamlit as st
import sys
sys.path.append('utils')
from writeread import read_file, read_filev2, output_create, read_filev2
from customcss import load_css
import pandas as pd
import numpy as np
import altair as alt
# import plotly.graph_objects as go
import plotly.express as px
# import re
# import glob
import tableone as tab1
# from lifelines import KaplanMeierFitter
# import matplotlib.pyplot as plt
pd.set_option('display.max_rows', 1000)

def data_naproc(df):
    navals = df.isna().sum().to_dict()
    cleancols = []
    for k, v in navals.items():
        if (v / df.shape[0] > 0.6):
            continue
        cleancols.append(k)
    df = df.fillna(999)
    return(df[cleancols], cleancols)

def app():
    load_css("/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/apps/css/css.css")
    st.markdown('<p class="big-font">GP2 Data Visualization Tool</p>', unsafe_allow_html=True)
    st.sidebar.title("Options")
    st.write(st.session_state['allqc'])

    # Load data and do na processing
    keep = ['sample_id', 'study', 'study_arm', 'diagnosis', 'sex',
            'race', 'age', 'age_of_onset', 'age_at_diagnosis', 'age_at_death', 'age_at_last_follow_up', 
            'family_history', 'visit_month', 'mds_updrs_part_iii_summary_score', 'moca_total_score', 
            'hoehn_and_yahr_stage', 'mmse_total_score']

    df_qc = None
    if st.session_state['allqc'] is None:
        data_file = st.sidebar.file_uploader("Upload Sample Manifest (CSV/XLSX)", type=['csv', 'xlsx'])
        if data_file is not None:
            #df_tmp = read_file(data_file)
            sm, clin, dct = read_filev2(data_file)
            df_merged = sm.merge(clin, how = 'inner', on =  ['sample_id', 'study'])
            df_qc, cols_qc = data_naproc(df_merged[keep])
    else:
        df_qc, cols_qc = data_naproc(st.session_state['allqc'][keep])

    if df_qc is not None:
        # Load data dictionary and map to data types
        data_dict = pd.read_table("/home/amcalejandro/Data/WorkingDirectory/Development_Stuff/GP2_SAMPLE_UPLOADER/sample_uploader/data/clincal_test/sm_dict.txt")
        mapper = {key:val for key,val in zip(data_dict['Item'], data_dict['ItemType']) if key in cols_qc}
        df_qc = df_qc.astype(mapper)
        #st.write(df_qc.info())
        #st.write(mapper)
        #data_dict_filt = {k:v for k,v in data_dict.items() if k in cols_qc}    
        # def my_filtering_function(pair, cols_qc=cols_qc):
        #     key, value = pair
        #     if key in cols_qc:
        #         return True  # filter pair out of the dictionary
        #     else:
        #         return False  # keep pair in the filtered dictionar
        # #data_dict_filt = dict(filter(my_filtering_function, data_dict.items()))
        # data_dict_filt = {k:v for k,v in data_dict.items() if k in cols_qc} 
        
        # Derive yearsB and yearsDx if possible.
        #bl_val = "yearsB" if bl == "Study Baseline" else "yearsDx"
        if ('age_at_diagnosis' in df_qc.columns) and ('age' in df_qc.columns):
            df_qc["Dx_Diagnosis"] = df_qc["age"] - df_qc["age_at_diagnosis"]
            mapper["Dx_Diagnosis"] = 'int64'
        # if ('age_at_diagnosis' in df.columns) and ('age_at_last_follow_up' in df.columns):
        #     df_qc["years_Last"] = df_qc["age"] - df_qc["age_at_last_follow_up"]
        #bl_val = "yearsB" if bl == "Study Baseline" else "yearsDx"
        if ('age_of_onset' in df_qc.columns) and ('age' in df_qc.columns):
            df_qc["Dx_Onset"] = df_qc["age"] - df_qc["age_of_onset"]
            mapper["Dx_Onset"] = 'int64'
        # if ('age_at_diagnosis' in df.columns) and ('age_at_last_follow_up' in df.columns):
        #     df_qc["yearsDxL"] = df_qc["age"] - df_qc["age_at_last_follow_up"]
        #st.write(df_qc.head())

        # Group all variables present on categoric and numeric
        grouped_dict = {}
        for key, value in mapper.items():
            if value not in grouped_dict:
                grouped_dict[value] = [key]
            else:
                grouped_dict[value].append(key)
        nnml = grouped_dict.get('int64')
        cats = grouped_dict.get('str')
        #st.write(mapper)
        #st.write(nnml)
        #st.write(cats)

        # Display plot options depending on the QCed data
        #long = True if len(df_qc.visit_name.unique()) > 1 else False
        # if long:
        #     viz = st.sidebar.selectbox("Choose a Visualization", ["Tables", "Scatter Plot","Bar Graph","Baseline Histogram"])
        if ('Dx_Diagnosis' in df_qc.columns) or ('Dx_Onset' in df_qc.columns):
            viz = st.sidebar.selectbox("Choose a Visualization", ["Tables", "Scatter Plot",
                                                                "Bar Graph","Baseline Histogram",
                                                                "Line Plot"])
        else:
            viz = st.sidebar.selectbox("Choose a Visualization", ["Tables", "Scatter Plot",
                                                                "Bar Graph","Baseline Histogram",])
        
        
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