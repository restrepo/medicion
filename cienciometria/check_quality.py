def check_quality(df,
     authors_WOS='authors_WOS',
     Tipo='Tipo',
     UDEA_authors='UDEA_authors'
    ):
    import pandas as pd
    if authors_WOS in df.columns:
        print(authors_WOS)
        x=df[authors_WOS].apply(lambda l:
                 l if type(l)==list
                 and len(l)>0 else None
                    ).dropna().shape[0]
        print(x)
        kk=df[df['TI']=='Leptonic charged Higgs decays in the Zee model'].reset_index(drop=True)
        print(kk.loc[0,'TI'],'; authors_WOS:',kk.loc[0,authors_WOS],'; AU:',kk.loc[0,'AU'])
    if Tipo in df.columns:        
        print('Tipo contains UDEA')
        x=df[df[Tipo].str.contains(
             'UDEA')].shape[0]
        print(x)
    if UDEA_authors in df.columns:
        print(UDEA_authors)
        kk=df[UDEA_authors].apply(lambda l:
             l if type(l)==list
             and len(l)>0 else None
                ).dropna().reset_index(drop=True)
        print(kk.shape[0])

        print('UDEA_authors → full_names (Extrapolado puntaje)')
        x=kk[kk.apply(lambda l: len([1 for d in l if 
                   d.get('full_name')])>0
               )].shape[0]
        print(x)
    
        print('UDEA_authors → "NOMBRE COMPLETO" (Extrapolado CENTRO)')
        x=kk[kk.apply(lambda l: len([1 for d in l if 
                   d.get('NOMBRE COMPLETO')])>0
               )].shape[0]
        print(x)
        


        
    print('TI: "The inert doublet model" check WOS_author vs UDEA_authors')
    print('...')
