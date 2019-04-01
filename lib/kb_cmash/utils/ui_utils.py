import os
import json
import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, leaves_list

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.WorkspaceClient import Workspace

def get_statistics(df_metadata, result, dist_col="containment_index",upa_name=None):
    '''
    Inputs:
        - df_metadata:
        - result:
        - upa_name (optional):
    Returns:

    '''

    df_id_col  = "assembly_id" #
    row_id_col = "assembly_id" #
    columns = df_metadata.columns
    stats = []
    dist_dict = {}
    for row in result:
        curr = {}

        df_row = df_metadata[df_metadata[df_id_col] == row[row_id_col]]
        df_row = df_row.reset_index()
        if len(df_row) > 1:
            raise ValueError("should only have 1 assembly id row in the dataframe.")
        for key, value in row.items():
            curr[key.strip().lower().replace(' ','_').replace('-', '_')] = value
        for col in columns:
            curr[col.strip().lower().replace(' ','_').replace('-', '_')] = df_row.loc[0, col]

        dist_dict[df_row.loc[0,'assembly_id']] = row[dist_col]

        stats.append(curr)

    return stats, dist_dict

def create_tree(df, tree_cols, dist_dict, source_order=None):
    '''
    Inputs:
        - df:
        - tree_cols:
        - dist_dict:
        - source_order:
    Returns:

    '''
    tree = []
    if len(tree_cols) == 0:
        return tree
    col = tree_cols[0]
    type_count = df[col].value_counts().to_dict()

    for t in type_count:
        count = "({})".format(type_count[t])
        leaf = create_tree(df[df[col]==t], tree_cols[1:], dist_dict, source_order=source_order)
        if leaf == []:
            if len(tree_cols) == 1:
                dist = dist_dict[t]
            else:
                dist = ""
            truncated_name = df[df[col]==t].iloc[0]['assembly_id']

            tree.append({
                'truncated_name': str(truncated_name),
                'name': t,
                'count': "({})".format(1),
            })
            tree[-1]['dist'] = dist

        else:
            tree.append({
                'truncated_name': t,
                'count': count,
                'children': leaf
            })
        if source_order!=None:
            sources = []
            # if leaf == []:
            #     d = df[df[col]==t][['upa','']]
            #     upas = d['upa'].tolist()
            #     for upa in upas:
            #         d[d['upa']==upa][''].tolist()
            # else:
            source_count = d[d[col]==t]['upa'].value_counts().to_dict()
            for i, s in enumerate(source_order):
                if s in source_count:
                    sources.append(source_count[s])
                else:
                    sources.append(0)
            tree[-1]['sources'] = sources
            tree[-1]['count'] = "({})".format(sum(sources))
    return tree

def get_locations(stats, markers, upa_name):
    '''
    Inputs:
        - stats:
        - markers:
    Returns:

    '''
    for s in stats:
        id_ = s["assembly_id"]
        if id_ in markers:
            markers[id_]['inputs'].append(upa_name)
        else:
            markers[id_] = {
                'name': s['sample_name'],
                'lat': s['latitude'],
                'lng': s['longitude'],
                'details': "Collection date: %s <br>Analysis completed: %s <br>Geo-location: %s"%(
                        s["collection_date"], s["analysis_completed"], s["geo_loc_name"]
                ),
                'inputs': [upa_name]
            }
    return markers

def get_upa_name(ws_url, cb_url, upa, is_test):
    '''
    '''
    if is_test:
        return "test_object"

    ws = Workspace(ws_url)
    objs = ws.get_object_info3({
        'objects': [{'ref':upa}]
    })
    upa_names = [info[1] for info in objs['infos']]
    if len(upa_names) > 0:
        return upa_names[0]

    dfu = DataFileUtil(cb_url)
    objs = dfu.get_objects({'object_refs':[upa]})['data']
    upa_names = [obj['info'][1] for obj in objs]
    if len(upa_names) > 0:
        return upa_names[0]
    else:
        raise ValueError("Could not find name of workspace object with id %s"%upa)

def remap_sources(sources, upa_order):
    '''
    '''
    new_sources = {}
    for j, i in enumerate(upa_order):
        val = sources[i]
        if val !=0 and val != []:
            new_sources[j] = val


def rewind_tree(tree, upa_order):
    '''
    '''
    for t_ix, t in enumerate(tree['children']):
        t['sources'] = remap_sources(t['sources'], upa_order)
        if t.get('children'):
            t = rewind_tree(t, upa_order)
        tree['children'][t_ix] = t
    return tree


def unwind_tree(X, tree):
    '''
    '''
    if tree.get('children'):
        for t in tree['children']:
            if 'compl' in t:
                X.append(np.array([len(mag_ids) for mag_ids in t['sources']]))
            else:
                X.append(np.array(t['sources']))
            X = unwind_tree(X, t)
    return X


def get_source_order(tree, upa_names):
    '''
    '''
    X = unwind_tree([tree['sources']], tree)
    X = np.transpose(np.array(X))
    z = linkage(X, 'ward')
    return leaves_list(z)


def format_results(ws_url, cb_url, results, is_test=False):
    '''
    Inputs:
        - results:
    Returns:
        -
    '''
    curr_dir =  os.path.dirname(os.path.realpath(__file__))
    metadata_path = os.path.join(curr_dir, 'data', 'ebi_samples_metadata_with_studies_final_with_cols.csv')
    df_metadata = pd.read_csv(metadata_path)
    tree_cols = ["category_"+str(i) for i in range(1,6)] + ["assembly_id"]

    df_metadata = df_metadata.fillna({col:"Unknown" for col in tree_cols})

    upas, upa_names, stats, markers = [], [], [], {}
    all_df = []
    # biosample,sample-alias,sample-desc,biome_id,sample_id,assembly_id,study-name

    dist_dict = {}

    id_col = "assembly_id" # put in the ID column
    df_id_col = "assembly_id" #Id columns for dataframe

    for upa, result in results.items():
        upa_name = get_upa_name(ws_url, cb_url, upa, is_test)
        upa_names.append(upa_name)
        upas.append(upa)
        curr_stats, curr_dist_dict = get_statistics(df_metadata, result, upa_name=upa_name)
        markers = get_locations(curr_stats, markers, upa_name)
        stats+=curr_stats
        for key, val in curr_dist_dict.items():
            dist_dict[key]=val

        curr_df = df_metadata[df_metadata[df_id_col].isin([s[id_col] for s in curr_stats])]
        curr_df.loc[:,'upa'] = upa
        all_df.append(curr_df)

    markers = [value for key, value in markers.items()]

    df = pd.concat(all_df)

    if len(upas) == 1:
        tree = create_tree(df, tree_cols, dist_dict)
        total_num = sum([int(t['count'][1:-1]) for t in tree])
        tree = {"truncated_name":"", "count":"({})".format(str(total_num)), 'count_num':total_num, "children":tree}
    else:
        tree = create_tree(df, tree_cols, dist_dict, source_order=upas)
        sources = [0 for _ in range(len(upas))]
        for i in range(len(upas)):
            for t in tree:
                sources[i]+=t['sources'][i]
        total_num = sum(sources)
        tree = {"truncated_name":"", "count":"({})".format(str(total_num)), 'count_num':total_num, 'sources':sources, "children":tree}

        upa_order = get_source_order(tree, upa_names)
        tree['sources'] = remap_sources(tree['sources'], upa_order)
        tree = rewind_tree(tree, upa_order)
        upa_names = [upa_names[idx] for idx in upa_order]

    return stats, upa_names, tree, markers
