import unidecode
import Levenshtein as lv
import wosplus as wp
import numpy as np
import pandas as pd
import unidecode
import os
import re
import sys
from IPython.display import clear_output
def get_author_info(x):
    sep='; '
    authors=[{'WOS_author':x[0].split(sep)[0],'affiliation':[x[0].split(sep)[-1]],'i':0}]
    iau=1
    for y  in x:
        y2=y.replace('[','').replace('] ',sep).split(sep)
        for z in y2[:-1]:
            aulist=[ d.get('WOS_author') for d in authors]
            if z not in aulist:
                authors.append({'WOS_author':z,'affiliation':[y2[-1]],'i':iau})
                iau=iau+1
            else:
                if y2[-1] not in [ d.get('affiliation') for d in authors if d.get('WOS_author')==z][0]:
                    index_author=[ d.get('i') for d in authors if d.get('WOS_author')==z][0]
                    authors[index_author]['affiliation'].append(y2[-1])
    return authors

def dictionary_list_add_columns(df,df_dl,df_dl_key,df_dl_i,df_columns):
    '''
    For a
     df: Pandas DataFrame 
    with a:
     df_dl: column of list of dictionaries, with
     df_dl_key: dictionary key: e.g x=[{df_dl_key:1},{df_dl_key:2}]
    for the element df_dl_i of the list:
    Update the dictionary with:
        df_dl_key==x[df_dl_i][df_dl_key]
    with the dictionaries { df_columns[i]: df_columns[i].values }
    '''
    dff=df.copy()
    for key in df_columns:
        tmp=dff[df_dl].combine(dff[key],
                func=lambda x,y: y if pd.isna(y) 
                                   else 
                                     [z.update({key:y}) 
                                     if z.get(df_dl_key)==x[df_dl_i][df_dl_key] 
                                     else z 
                                 for z in x  ] )
    return dff

def split_full_names(y,full_name='full_name'):
    """
    From an input dictionary with {full_name:'APPELLIDO1 APPELLIDO2 NOMBRES'}
    Obtain a dictionary with the several name parts.
    """    
    yy=y.get(full_name).title()
    lfn=len(y[full_name].split())
    aps=0
    d={ 'PRIMER APELLIDO':yy.split()[aps] }
    aps=aps+1
    if lfn>=4:
        names=-2
        if lfn==5: # Extra name or last name
            yyy=yy.split()
            ll=pd.np.array( [len(n) for n in yyy ] )
            if ll[3:][ ll[3:]  <= 3 ].shape[0]:
                # last_names first_first_name de(l) second_first_name
                yy=' '.join( [ y for y in yyy if len(y)>=3] )
            else: 
                # first_last name de(l) second_last_name first_names
                tmpll=yyy.pop() # internal memory
                yy=' '.join( yyy )  
        if len( d['PRIMER APELLIDO'] )<=3:
            d['PRIMER APELLIDO']=d['PRIMER APELLIDO']+' '+yy.split()[aps]
            aps=aps+1
            d.update(  {'SEGUNDO APELLIDO':yy.split()[aps]} )
            names=names+1
            
        d.update({'SEGUNDO APELLIDO':yy.split()[aps]})
        aps=aps+1
        if len( d['SEGUNDO APELLIDO'] )<=3:
            d['SEGUNDO APELLIDO']=d['SEGUNDO APELLIDO']+' '+yy.split()[aps]
            if names==-2:
                names=names+1
    elif lfn>=3:        
        d.update({'SEGUNDO APELLIDO':yy.split()[aps]})
        names=-1
    else: #Colombian interpretation (TODO: Includes Brazilian interpretation)    
        names=-1
    d.update({'NOMBRES':' '.join( yy.split()[names:]),
              'INICIALES':' '.join( [z[0]+'.' for z in yy.split()[names:]] ),
              })
    if not d.get('SEGUNDO APELLIDO'):
        d['SEGUNDO APELLIDO']=''
    #if not d.get('NOMBRE COMPLETO'):
    #    d['NOMBRE COMPLETO']=''        
    return d

# Creates mask Search key in a list of dictionay
# First apply convert null values to string
# Second apply: implement a mask
def find_key_in_list_of_dictionaries(df,column,key,pattern):
    return df[column].apply(lambda x: 
                [ '' if pd.isnull( y.get(key)) else y for y in x ]  ).apply(
                            lambda x: 
                [ True if y.get(key).find(pattern)>-1 else False for y in x  ][0]  )

def key_contains_in_list_of_dictionaries(df,pattern,column='authors_WOS',key='WOS_author'):
    #TODO: loop in column len
    i=0
    r=df[ df[column].str[i].apply(lambda x: {} if pd.isnull(x) else x).apply(
                       lambda x: x.get(key) if x else '').str.contains(
        pattern) ][column].reset_index(drop=True)
    return r

def update_institutional_authors(kkn,AU,authors_column='UDEA_authors',authors_column_key='full_name',
                                        AU_first_last_name='PRIMER APELLIDO',
                                        AU_second_last_name='SEGUNDO APELLIDO',
                                        AU_first_names='NOMBRES'
                                ):
    '''
    For a Data base containing full names of the authors of the articles: SIU,
    include detailed information from other database                    : AU.
      authors_column    : kkn Column with dictionary to be updated
      authors_column_key: Key with full name as a value in  authors_column of kkn
      For Spaniard name, e.g "Juan Pedro Restrepo Correa"
      AU_first_last_name: AU column with "Restrepo"
      AU_second_last_name: AU column with "Correa"
      AU_first_names: AU column with "Juan Pedro"
      full_name: Colum in AU with full name
      
    '''
    full_name='name_tmp'
    AU_columns=list( AU.columns.values )

    AU[full_name]=(AU[AU_first_last_name]+' '+AU[AU_second_last_name]+' '+AU[AU_first_names]
                  ).str.lower().str.strip().apply( unidecode.unidecode )

    maxau=kkn[authors_column].apply(lambda l: [d.get(full_name) for d in l ] 
                                    if type(l)==list else []).apply(len).max()
    
    newcolumns=[full_name]+AU_columns
    for i in range(maxau):
        print(i)
        kkn[full_name]=kkn[authors_column].apply(lambda l: [d.get(authors_column_key) for d in l ]
                        if type(l)==list else ''
                            ).str[i].apply( lambda s: unidecode.unidecode( s.lower().strip()) 
                                                      if not pd.isna(s) else s)
        if not kkn[~kkn[full_name].isna()].empty:
            kkn=kkn.merge(AU[newcolumns],on=full_name,how='left').reset_index(drop=True)
            kkn=dictionary_list_add_columns(kkn,authors_column,authors_column_key,i,AU_columns)
            kkn=kkn.drop(newcolumns,axis='columns')
    return kkn

def SCI_C1_to_C1(UDEA,C1='C1',Tipo='Tipo',WOS='WOS',SCI='SCI',affil='Univ Antioquia',
            SCI_C1='SCI_C1',
            regex_normalize_affilliation_SCI=['Universidad de Antioquia','Univ. de Antioquia']):
    UDEA_SCI=UDEA[SCI_C1].combine(UDEA[Tipo],
                    func=lambda x,y: x if y.find(SCI)>-1 and y.find(WOS)==-1 else None)
    for bad_affil in regex_normalize_affilliation_SCI:
        UDEA_SCI=UDEA_SCI.apply(lambda x:x.replace(
            bad_affil,affil) if not pd.isnull(x) else x)
    #Update only if not filled already
    return UDEA_SCI.combine(UDEA[C1],lambda x,y:x if pd.isnull(y) else y)

def SCP_Authors_with_affiliations_to_C1(UDEA,C1='C1',Tipo='Tipo',SCP='SCP',
            affil='Univ Antioquia',SCP_C1='SCP_Authors with affiliations',
            lastname='[\w\-\.\s]+',firstname='[\w\-\.]+',
            regex_normalize_affilliation_SCP=['Universi[dadty]{2,3}\s+[deofDEOF]{2}\s+Antioqu[ií]a',
                                              'U[\.niv]{1,4}\s+[deofDEOF]{0,2}\s*Antioqu[ií]a',
                                              'Antioqu[ií]a\s+[deofDEOF]{0,2}\s*Universi[dadty]{2,3}']):    
    #Remove authors without affiliations
    SCP2WOS=UDEA[SCP_C1].str.replace('(^|;\s+)(({},\s+{};\s+)+)'.format( 
                                        lastname,firstname,lastname,firstname),r'\1',re.UNICODE
                                                     )
    SCP2WOS=SCP2WOS.str.replace('; ','\n').str.replace(
                                '^({},{}),'.format( lastname,lastname),r'[\1]',re.UNICODE).str.replace(
                                '\n({},{}),'.format(lastname,lastname),r'\n[\1]',re.UNICODE).str.replace(
                                '(,\s+\w\.)(\w\.\])'.format(lastname,lastname),r'\1 \2',re.UNICODE)
    # Normalize to WOS
    for bad_affil in regex_normalize_affilliation_SCP:
            SCP2WOS=SCP2WOS.str.replace(bad_affil,affil)
    UDEA_SCP=SCP2WOS.combine(UDEA[Tipo],func=lambda x,y: x if y==SCP else None)
    #Update only if not filled already
    return UDEA_SCP.combine(UDEA[C1],lambda x,y:x if pd.isnull(y) else y)

def wos_names_append(wos_names,last_name,first_names,initials):
    wos_names=wos_names+[           last_name+', '+first_names]
    if len( first_names.split())>1:
        wos_names=wos_names+[ last_name+', '+first_names.split()[0] ]
    if len( first_names.split())==2 and  len(first_names.split()[-1]):
        wos_names=wos_names+[ last_name+', '+first_names.split()[-1] ]
    wos_names=wos_names+[ last_name+', '+initials]
    if len( initials.split())>1:
        wos_names=wos_names+[ last_name+', '+initials.split()[0]]
    if len(initials.split())==2:
        wos_names=wos_names+[
              last_name+', '+first_names.split()[0]+' '+initials.split()[-1] ]
        wos_names=wos_names+[last_name+', '+initials.split()[-1] ]
    return wos_names
    
def wos_names_list(dy ,y_keys=['PRIMER APELLIDO','NOMBRES','INICIALES','SEGUNDO APELLIDO','full_name']   ):
    """
    Generate a list of WOS names possibilitites from full name parts.
    The full name parts are obtained from dictionary: dy
    with keys in the strict order:
       y_keys=[first_last_name,names,initials,second_first_name,[full_name]]
               otptional full_name is used in general function
    Output Example:
      ['Pabon, Adriana Lucia',
       'Pabon, Adriana',
       'Pabon, Lucia',
       'Pabon, A. L.',
       'Pabon, A.',
       'Pabon, Adriana L.',
       'Pabon, L.',
       'Pabon-Vidal, Adriana Lucia',
       'Pabon-Vidal, Adriana',
       'Pabon-Vidal, Lucia',
       'Pabon-Vidal, A. L.',
       'Pabon-Vidal, A.',
       'Pabon-Vidal, Adriana L.',
       'Pabon-Vidal, L.']
    TODO: Initial can be internally generated
    """
    last_name= unidecode.unidecode( dy[y_keys[0]]   )
    first_names=unidecode.unidecode( dy[y_keys[1]]  )
    initials=unidecode.unidecode( dy[y_keys[2]]  )

    wos_names=[]
    wos_names=wos_names_append(wos_names,last_name,first_names,initials)
    
    if dy.get( y_keys[3] ):
        last_names= unidecode.unidecode( dy[y_keys[0]]+'-'+dy[y_keys[3]]   )
        wos_names=wos_names_append(wos_names,last_names,first_names,initials)
    return wos_names
    
def combinewos(x,y,x_keys=['WOS_author','affiliation'],
                   y_keys=['PRIMER APELLIDO','NOMBRES','INICIALES','SEGUNDO APELLIDO','full_name'],
                   xy_keys=['WOS_author','WOS_affiliation']):
    if type(x)==list and type(y)==list:
        for dx in x:
            wos_name=unidecode.unidecode( dx[ x_keys[0] ] )
            WOS_affiliation= dx[x_keys[1]]
            # Try by buildinng spanish-like names list                                
            for i in range( len(y) ):
                if wos_name.title() in wos_names_list(y[i] ,y_keys):
                    y[i][  xy_keys[0] ]=[ wos_name ]
                    y[i][  xy_keys[1] ]=WOS_affiliation
                    break
            #Try again but comparing full lists
            wos_name_to_list=wos_name.replace(',','').replace('-',' ').title().split()
            for i in range( len(y) ):
                yi_to_list=unidecode.unidecode( y[i][y_keys[4]].title() )
                if yi_to_list:
                    yi_to_list=yi_to_list.split()
                else:
                    yi_to_list=[]
                if not pd.np.setdiff1d(wos_name_to_list,yi_to_list).shape[0]:
                    y[i][  xy_keys[0] ]=[ wos_name ]
                    y[i][  xy_keys[1] ]=WOS_affiliation
                    break
            #Try again but comparing full lists with initials
            wos_name_to_list=wos_name.replace(',','').replace('-',' ').title().split()
            for i in range( len(y) ):
                yi_to_list=[y[i][y_keys[0]],y[i][y_keys[3]] ]+y[i][y_keys[2]].split()
                if not pd.np.setdiff1d(wos_name_to_list,yi_to_list).shape[0]:
                    y[i][  xy_keys[0] ]=[ wos_name ]
                    y[i][  xy_keys[1] ]=WOS_affiliation
                    break
            #Try again but comparing full lists with first first name and initial
            for i in range( len(y) ):
                yi_to_list=[y[i][y_keys[0]],y[i][y_keys[3]],y[i][y_keys[1]].split()[0],
                              y[i][y_keys[2]].split()[-1]]
                if not pd.np.setdiff1d(wos_name_to_list,yi_to_list).shape[0]:
                    y[i][  xy_keys[0] ]=[ wos_name ]
                    y[i][  xy_keys[1] ]=WOS_affiliation
                    break                    
            #Try again but comparing full lists with second first name and initial
            for i in range( len(y) ):
                yi_to_list=[y[i][y_keys[0]],y[i][y_keys[3]],y[i][y_keys[1]].split()[-1],
                              y[i][y_keys[2]].split()[0]]
                if not pd.np.setdiff1d(wos_name_to_list,yi_to_list).shape[0]:
                    y[i][  xy_keys[0] ]=[ wos_name ]
                    y[i][  xy_keys[1] ]=WOS_affiliation
                    break                    
                    
                    
    return y

def extract_internal_value_of_a_dictionary_key_in_a_list_of_dictionaries(df,
    list_of_dictionaries='UDEA_authors',
    dictionary_key='WOS_author'):
    #Extract internal value of a dictionary key in a list of dictionaries and empty list otherwise
    
    return df[list_of_dictionaries].apply(lambda x: [y.get(dictionary_key) 
                                                        if y.get(dictionary_key) else []   
                                                        for y in x  ]
                           if type(x)==list else [])

def extract_internal_list_as_value_of_a_dictionary_key_in_a_list_of_dictionaries(df,
    list_of_dictionaries='UDEA_authors',
    dictionary_key='WOS_author'):
    #Extract internal list as value of a dictionary key in a list of dictionaries and empty list otherwise
    
    return extract_internal_value_of_a_dictionary_key_in_a_list_of_dictionaries(df,
                    list_of_dictionaries,dictionary_key).apply(lambda x: 
                           [item for sublist  in x for item in sublist] 
                            if type(x)==list else x)

def mask_on_internal_value_of_a_dictionary_key_in_a_list_of_dictionaries(df,
    pattern='RESTREPO QUINTERO DIEGO ALEJANDRO',
    list_of_dictionaries='UDEA_authors',dictionary_key='full_name'):
    """
    Build a mask for a Pandas Series of list of dictionaries of label:
      list_of_dictionaries. 
    The:
      dictionary_key must be a single value like string or float
    """
    return extract_internal_value_of_a_dictionary_key_in_a_list_of_dictionaries(df,
            list_of_dictionaries,dictionary_key).apply( 
            lambda x: pattern in x)

def fill_trained_data(UDEA,SIU,UDEA_authors='UDEA_authors',semicolon_authors='UDEA_autores',Tipo='Tipo',
                      Tipo_prefix='UDEA',full_name='full_name',DI='DI',TI='TI',
                      REMOVE_UDEA_columns=True,
                     udea_columns=[       'UDEA_autores',
           'UDEA_año realiz', 'UDEA_doi', 'UDEA_fecha aplicación',
           'UDEA_idioma', 'UDEA_item adic', 'UDEA_material', 'UDEA_nombre',
           'UDEA_nombre revista o premio', 'UDEA_nro autores', 'UDEA_país',
           'UDEA_procodigo', 'UDEA_ptos', 'UDEA_simple_doi', 'UDEA_título',
           'UDEA_valor item']):
    SIU=SIU[SIU[Tipo].str.contains('\+{}'.format(Tipo_prefix))].reset_index(drop=True)

    SIU[semicolon_authors]=SIU[semicolon_authors].str.replace('\s+',' ')

    #SIU[UDEA_authors]=SIU[semicolon_authors].str.split(';').apply(lambda x: [{full_name:y} for y in x ])
    
    #Be sure that always be True. The columns will be obtaied from SIU
    REMOVE_UDEA_columns=True
    if REMOVE_UDEA_columns:
        UDEA_columns=[c for c in UDEA.columns if c.find('{}_'.format(Tipo_prefix))>-1]
        UDEA=UDEA.drop(UDEA_columns,axis='columns')    

    SIUDI=SIU[~SIU[DI].isna()].drop_duplicates(DI).reset_index(drop=True)
    SIUTI=SIU[ SIU[DI].isna()].drop_duplicates(TI).reset_index(drop=True)
    SIUTI=SIUTI[SIUTI!=''].reset_index(drop=True)
    SIUTI=SIUTI[~SIUTI[TI].isnull()].reset_index(drop=True)
    SIUTI=SIUTI[ SIUTI[TI].apply(len)>20 ].reset_index(drop=True)

    UDEADI=UDEA[UDEA[DI]!=''].drop_duplicates(DI).reset_index(drop=True)
    UDEATI=UDEA[UDEA[DI]==''].drop_duplicates(TI).reset_index(drop=True)

    UDEA_mergeDI=UDEADI.merge( SIUDI[ [DI]+udea_columns ],on=DI,how='left' )

    UDEA_PTJ=pd.DataFrame()
    UDEA_PTJ_NOT=pd.DataFrame()
    UDEA_PTJ=UDEA_mergeDI[~UDEA_mergeDI[semicolon_authors].isna()].reset_index(drop=True)
    UDEA_PTJ_NOT=UDEA_mergeDI[UDEA_mergeDI[semicolon_authors].isna()].reset_index(drop=True)

    UDEATI['tmptitle']=UDEATI[TI].str.strip()
    SIUTI['tmptitle']=SIUTI[TI].str.strip()

    kk=UDEATI.merge( SIUTI[ ['tmptitle']+udea_columns ],on='tmptitle',how='left' ).drop('tmptitle',axis='columns')

    UDEA_PTJ=UDEA_PTJ.append( kk[ ~kk[semicolon_authors].isna() ] ).reset_index(drop=True)
    UDEA_PTJ_NOT=UDEA_PTJ_NOT.append( kk[ kk[semicolon_authors].isna() ] ).reset_index(drop=True)

    print(UDEA_PTJ.shape[0]+UDEA_PTJ_NOT.shape[0],UDEA.shape)

    print(UDEA_PTJ.shape,UDEA_PTJ_NOT.shape)

    UDEA=UDEA_PTJ.append(
        UDEA_PTJ_NOT).reset_index(
        drop=True)    
    return UDEA,SIU

def build_udea_authors(UDEA,UDEA_authors='UDEA_authors',authors_WOS='authors_WOS'):
    aumax=UDEA[UDEA_authors].dropna().apply(len).max() 
    ua=pd.DataFrame()
    if type(aumax)!=int:
        aumax=1
    for i in range(aumax):
        kkk=pd.DataFrame()
        kkk[UDEA_authors]= UDEA[UDEA_authors].str[i].dropna()
        kkk[authors_WOS]= UDEA[authors_WOS]
        #kkk['SCP_Authors']=UDEA['SCP_Authors']
        kkk['tmp_str']=kkk['UDEA_authors'].astype(str)
        kkk=kkk.drop_duplicates('tmp_str')
        ua=ua.append(kkk).reset_index(drop=True)

    ua['tmp_author']=ua[UDEA_authors].apply( 
            lambda d: d.get('full_name') if type(d)==dict else d)
        
    ua[authors_WOS]=ua[authors_WOS].apply(lambda l: l if l else pd.np.nan)
    ua=ua[~ua[authors_WOS].isna()].reset_index(drop=True)        
    return ua

def DataFrame_authors(UDEA,UDEA_authors='UDEA_authors',
                      WOS_affiliation='WOS_affiliation',
                     WOS_author='WOS_author'):
    ua=build_udea_authors(UDEA)
    full_names=ua['tmp_author'].unique()
    aunly=pd.DataFrame()
    for f in full_names:
        clear_output(wait=True)
        print(f)    
        kk=pd.DataFrame( { 'tmp_author':[f]  } ).merge(
              ua[['tmp_author','UDEA_authors']],on='tmp_author',how='left')

        kk['tmp_str']=kk[UDEA_authors].astype(str)

        kk=kk.drop_duplicates('tmp_str').dropna()#[['tmp_author','UDEA_authors']]

        try:
            laff=list( kk[UDEA_authors].apply(lambda d: d.get( WOS_affiliation )
                                         ).dropna().apply(pd.Series).stack().unique() )
            lau=list( kk[UDEA_authors].apply(lambda d: d.get( WOS_author )
                                         ).dropna().apply(pd.Series).stack().unique() )
        except AttributeError:
            laff=[];lau=[]

        if len(laff)>0 and len(lau)>0:
            tmpupdate=kk['UDEA_authors'].apply(lambda d: d.update({WOS_author:lau,WOS_affiliation:laff}) )

            kk['tmp_str']=kk[UDEA_authors].astype(str)

            kk=kk.drop_duplicates('tmp_str')

            kk['tmp_len']=kk['tmp_str'].apply(len)#.astype(str)

            aunly=aunly.append( kk.sort_values('tmp_len',ascending=False).drop(index=kk.index[1:]).drop(
                   ['tmp_str','tmp_len'],axis='columns') ).reset_index(drop=True)
    
    return aunly

def fill_full_wos_author_info(l,WOS_df,full_name='full_name',full_name_column='tmp_author',
                               WOS_column='UDEA_authors',WOS_author='WOS_author',
                               WOS_affiliation='WOS_affiliation'):
    '''
    WOS_df=aunly
    '''
    newl=[]
    if type(l)==list:
        for d in l:
            if d.get('WOS_author'):
                #find in aunly
                mtch=WOS_df[WOS_df[full_name_column]==d.get(full_name)].reset_index(drop=True)
                if mtch.shape[0]==1:
                    #update d
                    if mtch[WOS_column].loc[0].get(WOS_author):
                        d[WOS_author]=mtch[WOS_column].loc[0].get(WOS_author)
                        d[WOS_affiliation]=mtch[WOS_column].loc[0].get(WOS_affiliation)
            newl.append(d)
    else:
        newl=l
    return newl


def find_author_affiliation(author,affiliation,author_df,column='UDEA_authors',
                            author_key='WOS_author',affiliation_key='WOS_affiliation',ratio=0.9):
    '''
    author_df=aunly
    find the WOS+"UDEA puntaje" dictionary for WOS author:   `author`
    and WOS affiliation:                                    `affiliation`
    The information is  searched in 
    WOS+"UDEA puntaje" DataFrame:                            `author_df`, 
    which has the column:                                    `column` 
    which contains a dictionary with list value for the key: `author_key`
    and list value for the key:                              `affiliation_key`.
    Affiliation must be similar until a Levenshtein ratio:   `ratio`
    '''
    if not author_df.empty:
        au=author_df[ author_df[column].apply(
                    lambda d: d.get(author_key) if type(d)==dict else '').apply(
                      lambda l: author in l)]#.reset_index(drop=True).loc[0,column]
    else:
        au=pd.DataFrame()
        
    if au.shape[0]>0:
        #Fast
        auf=au[au[column].apply(
                 lambda d: d.get(affiliation_key) if type(d)==dict else '').apply(
                 lambda l: affiliation in l)]
        

        if auf.shape[0]>0:
              return auf.reset_index(drop=True).loc[0,column]          
        #Slow
        else:
            aus=au[au[column].apply(
                 lambda d: d.get(affiliation_key) if type(d)==dict else '').apply(
                 lambda l: len( [af for af in l if lv.ratio(af,affiliation) > ratio ] )>0 )]

            if aus.shape[0]==1: #fix 1 to avoid homonymous
                dold=aus.reset_index(drop=True).loc[0,column]
                # Dictionary is automatically updated in author_df!
                dold[affiliation_key]=dold[affiliation_key]+[affiliation]
                return dold
    else:
        return None

def get_UDEA_authors(x,y,author_df,x_author_key='WOS_author',x_affiliation_key='affiliation',
                        column='UDEA_authors',
                        author_key='WOS_author',affiliation_key='WOS_affiliation',
                        ratio=0.9):
    '''
    author_df=aunly
    get the WOS+"UDEA puntaje" list of dictionaries for WOS author list 
    and affiliation list in the  list of dictionaries:      `x`, 
    where each dictionary have the string value for the key: `x_author_key`, 
    and the list value for the key:                          `x_affiliation_key`.
    The information is obtained directly from the 
    WOS+"UDEA puntaje" list:                                 `y` 
    if already there, or searched in 
    WOS+"UDEA puntaje" DataFrame:                            `author_df`, 
    which has the column:                                    `column` 
    which contains a dictionary with list value for the key: `author_key`
    and list value for the key:                              `affiliation_key`.
    If not foun None is returned.
    WOS info can be changed for other standarized dababase info
    and "UDEA puntaje" can be changed from any other full name author
    and affiliation info.
    
    IMPORTANT:
    The list of values in:                                   `affiliation_key` 
    is automatically updated with the similar first 
    affiliation value of the list in:                        `x_affiliation_key`
    according with the Levenshtein similarity ratio:         `ratio`
    '''
    if type(y)==list:
        #already filled:
        return y

    au=[]
    if ( type(x)==list and x):
        for j in range(len(x)):
            xx=find_author_affiliation(x[j].get(x_author_key),x[j].get(x_affiliation_key)[0],
                                        author_df=author_df,
                                        author_key=author_key,
                                        affiliation_key=affiliation_key,
                                        ratio=ratio )
            if xx:
                au.append(xx)
    if au:
        return au
    else:
        return None


def merge_puntaje(drive_files,on_left='WOS',on_right='UDEA',
                  UDEA_title='UDEA_título',UDEA_title_list='UDEA_título_list',
                  left_DOI="DI",left_TI="TI",
                  right_TI="UDEA_TI",
                  left_author="AU", left_year="PY",
                  right_author="UDEA_nombre",right_year="UDEA_año realiz",
                  left_extra_journal="SO",
                  right_extra_journal="UDEA_nombre revista o premio",
                  UDEA_doi='UDEA_doi',
                  UDEA_authors='UDEA_authors',
                  titlec='UDEA_TI',
                  authorc='UDEA_nombre',
                  authorsc='UDEA_autores',
                  UDEA_normalization={'UDEA_pais prod':'UDEA_país','UDEA_puntos':'UDEA_ptos'}):
    on_right_prexif=on_right+'_'
    on_left_on_right=on_left+'_'+on_right
    
    #*** on_right *****
    septrans=r'(.+)\((.{10,})\)$'

    #Title normalization
    drive_files.biblio[on_right][UDEA_title_list]=drive_files.biblio[on_right][UDEA_title].str.replace(
        septrans,r'\1;;\2',re.UNICODE).str.split(';;').apply(
       lambda l: [ re.sub( r'^"','',
                          re.sub( r'"$','', s.strip() )
                         ) for s in l] )#.loc[i]

    #TODO: check
    if UDEA_doi not in drive_files.biblio[on_right].columns:
        drive_files.biblio[on_right][UDEA_doi]=''

    drive_files.biblio[on_right]=drive_files.biblio[on_right].reset_index(drop=True)
    i=0 #1

    drive_files.biblio[on_right][titlec]=drive_files.biblio[on_right][UDEA_title_list].str[i]

    #Generate semicolon separated values for authors
    multi_au=drive_files.biblio[on_right][
         drive_files.biblio[on_right].duplicated(subset=[titlec],keep=False)].reset_index(drop=True)

    single_au=drive_files.biblio[on_right][
        ~drive_files.biblio[on_right].duplicated(subset=[titlec],keep=False)].reset_index(drop=True)

    single_au[authorsc]=single_au[authorc]

    multi_au=multi_au.sort_values(titlec).reset_index(drop=True)    


    t_old=''
    au_old=pd.np.nan
    for i in multi_au.index:
        t=multi_au.loc[i,titlec]
        if t==t_old:
            au_old=au_old+';'+multi_au.loc[i,authorc]
            multi_au.loc[i-1,authorsc]=pd.np.nan
        else:
            t_old=t
            multi_au.loc[i-1,authorsc]=au_old
            au_old=multi_au.loc[i,authorc]

    drive_files.biblio[on_right]=(multi_au.dropna(subset=[authorsc]).append(single_au,sort=False)
                           ).reset_index(drop=True)
    print( drive_files.biblio[on_right].shape )
    #*** END on_right***

    #*** on_left ***
    if authorsc in drive_files.biblio[on_left].columns:
        drive_files.biblio[on_left][authorc]=drive_files.biblio[on_left][authorc].apply(
                                              lambda s: re.sub('\s+',' ',s) if type(s)==str else s).apply(
                                              lambda s: s if s else None)
        #ALREADY in PTJ
        UDEA_PTJ=drive_files.biblio[on_left][ ~drive_files.biblio[on_left][authorsc].isna()].reset_index(drop=True)
        # Missing PTJ. To be proccesses below
        UDEA_PTJ_NOT    =drive_files.biblio[on_left][ drive_files.biblio[on_left][authorsc].isna()].reset_index(drop=True)
    else:
        UDEA_PTJ_NOT    =drive_files.biblio[on_left]
        UDEA_PTJ=pd.DataFrame()
   
    drive_files.biblio[on_left]=UDEA_PTJ_NOT

    udea_columns=[c for c in drive_files.biblio[on_left].columns if c.find(on_right_prexif)>-1]

    drive_files.biblio[on_left]=drive_files.biblio[on_left].drop( udea_columns, axis='columns' )
    
    #*** END on_left ***

    kk=drive_files.merge(left=on_left, right=on_right,
                         left_DOI=left_DOI, left_TI=left_TI,
                         right_DOI=UDEA_doi, right_TI=right_TI,
                         left_author=left_author, left_year=left_year,
                         right_author=right_author,right_year=right_year,
                         left_extra_journal=left_extra_journal,
                         right_extra_journal=right_extra_journal
                         )
    
    newwos=drive_files.biblio[on_left_on_right][drive_files.biblio[on_left_on_right].Tipo!=on_right]
    
    app_to_UDEA_PTJ=newwos[newwos.Tipo.str.contains(on_right)].reset_index(drop=True)

    new_UDEA_not_PTJ=newwos[~newwos.Tipo.str.contains(on_right)].reset_index(drop=True)
    print(7258,':',new_UDEA_not_PTJ.shape[0],'+',app_to_UDEA_PTJ.shape[0],'=',
          new_UDEA_not_PTJ.shape[0]+app_to_UDEA_PTJ.shape[0])

    drive_files.biblio[on_left]=new_UDEA_not_PTJ

    drive_files.biblio[on_left]=drive_files.biblio[on_left].drop( 
         [ c for c in drive_files.biblio[on_left].columns if c.find(on_right_prexif)>-1  ],
           axis='columns')
    
    i=1
    drive_files.biblio[on_right][right_TI]=drive_files.biblio[on_right][UDEA_title_list].str[i]

    drive_files.biblio[on_right]=wp.fill_NaN(drive_files.biblio[on_right])
    drive_files.biblio[on_left] =wp.fill_NaN(drive_files.biblio[on_left])    
    drive_files.UDEA=drive_files.biblio[on_right]
    drive_files.WOS =drive_files.biblio[on_left]    

    kk=drive_files.merge(left=on_left, right=on_right,
                         left_DOI=left_DOI, left_TI=left_TI,
                         right_DOI=UDEA_doi, right_TI=right_TI,
                         left_author=left_author, left_year=left_year,
                         right_author=right_author,right_year=right_year,
                         left_extra_journal=left_extra_journal,
                         right_extra_journal=right_extra_journal
                         )

    newwos=drive_files.biblio[on_left_on_right][drive_files.biblio[on_left_on_right].Tipo!=on_right]

    app_to_UDEA_PTJ_2=newwos[newwos.Tipo.str.contains(on_right)].reset_index(drop=True)
    app_to_UDEA_PTJ_2.shape

    new_UDEA_not_PTJ=newwos[~newwos.Tipo.str.contains(on_right)].reset_index(drop=True)
    new_UDEA_not_PTJ.shape[0]+app_to_UDEA_PTJ.shape[0]

    print(7258,':',new_UDEA_not_PTJ.shape[0],'+',app_to_UDEA_PTJ_2.shape[0],'=',
          new_UDEA_not_PTJ.shape[0]+app_to_UDEA_PTJ_2.shape[0])

    drive_files.biblio[on_left]=new_UDEA_not_PTJ

    drive_files.biblio[on_left]=drive_files.biblio[on_left].drop( 
         [ c for c in drive_files.biblio[on_left].columns if c.find(on_right_prexif)>-1  ],
           axis='columns')
    drive_files.biblio[on_left].shape

    drive_files.biblio[on_right]=wp.fill_NaN(drive_files.biblio[on_right])
    drive_files.biblio[on_left] =wp.fill_NaN(drive_files.biblio[on_left])    

    kk=drive_files.merge(left=on_left, right=on_right,
                         left_DOI=left_DOI, left_TI=left_TI,
                         right_DOI=UDEA_doi, right_TI=UDEA_title,
                         left_author=left_author, left_year=left_year,
                         right_author=right_author,right_year=right_year,
                         left_extra_journal=left_extra_journal,
                         right_extra_journal=right_extra_journal
                         )

    newwos=drive_files.WOS_UDEA[drive_files.WOS_UDEA.Tipo!=on_right]

    app_to_UDEA_PTJ_tot=newwos[newwos.Tipo.str.contains(on_right)].reset_index(drop=True)

    new_UDEA_not_PTJ=newwos[~newwos.Tipo.str.contains(on_right)].reset_index(drop=True)
    new_UDEA_not_PTJ.shape[0]+app_to_UDEA_PTJ_tot.shape[0]
    new_UDEA_not_PTJ=new_UDEA_not_PTJ.drop(
        [ c for c in new_UDEA_not_PTJ.columns if c.find(on_right_prexif)>-1  ],axis='columns')

    print(7258,':',new_UDEA_not_PTJ.shape[0],'+',app_to_UDEA_PTJ_tot.shape[0],'=',
          new_UDEA_not_PTJ.shape[0]+app_to_UDEA_PTJ_tot.shape[0])

    new_UDEA_PTJ=app_to_UDEA_PTJ.append(app_to_UDEA_PTJ_2).append(app_to_UDEA_PTJ_tot).reset_index(drop=True)
    new_UDEA_PTJ=new_UDEA_PTJ.drop_duplicates(left_TI).reset_index(drop=True)

    new_UDEA_PTJ=new_UDEA_PTJ.drop(right_TI,axis='columns')
    new_UDEA_PTJ=new_UDEA_PTJ.rename(UDEA_normalization,axis='columns')
    


    print(new_UDEA_PTJ.shape,'+',new_UDEA_not_PTJ.shape,'=',
     new_UDEA_PTJ.shape[0]+new_UDEA_not_PTJ.shape[0])


    UDEA=UDEA_PTJ.append( new_UDEA_PTJ.append( new_UDEA_not_PTJ,sort=False ),
                         sort=False ).reset_index(drop=True)
    return UDEA    