from st_aggrid import AgGrid, GridOptionsBuilder

def aggridPlotter(df):
    df_builder = GridOptionsBuilder.from_dataframe(df)
    df_builder.configure_grid_options(alwaysShowHorizontalScroll = True,
                                        enableRangeSelection=True,
                                        pagination=True,
                                        paginationPageSize=10000,
                                        domLayout='normal')
    godf = df_builder.build()
    AgGrid(df,gridOptions=godf, theme='streamlit', height=300)