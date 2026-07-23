if col_blok != "Tiada" and col_tingkat != "Tiada":
                # Create the crosstab table
                cross_tab = pd.crosstab(df[col_tingkat], df[col_blok], margins=True, margins_name='JUMLAH')
                
                subset_rows = cross_tab.index[:-1]
                subset_cols = cross_tab.columns[:-1]
                
                # Force global min and max calculations for the color scale
                # This stops Streamlit from guessing and forces uniform colors across all blocks
                data_subset = cross_tab.loc[subset_rows, subset_cols]
                global_min = data_subset.values.min()
                global_max = data_subset.values.max()
                
                # Apply styling: background gradient and center text alignment
                styled_table = (
                    cross_tab.style
                    .background_gradient(
                        cmap='Reds', 
                        axis=None,  
                        subset=pd.IndexSlice[subset_rows, subset_cols],
                        vmin=global_min,
                        vmax=global_max
                    )
                    .set_properties(**{'text-align': 'center'}) # Centers the figures
                )
                
                st.dataframe(styled_table, use_container_width=True)
            else:
                st.info("Pilih lajur Blok dan Tingkat dari data Excel anda untuk melihat jadual ini.")

        except Exception as e:
            st.error(f"Terdapat ralat semasa membaca fail: {e}")
