import os
from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.WorkspaceClient import Workspace

def load_fastas(config, scratch, upa):
    '''

    '''
    dfu = DataFileUtil(config['callback_url'])
    au = AssemblyUtil(config['callback_url'])
    ws = Workspace(config['workspace-url'])

    obj_data = dfu.get_objects({"object_refs":[upa]})['data'][0]
    obj_type  = obj_data['info'][2]

    if 'KBaseSets.GenomeSet' in obj_type:
        upas = [gsi['ref'] for gsi in obj_data['data']['items']]
    elif 'KBaseSearch.GenomeSet' in obj_type:
        upas = [gse['ref'] for gse in obj_data['data']['elements'].values()]
    elif "KBaseGenomes.Genome" in obj_type:
        upas = [upa]
    elif "KBaseGenomes.ContigSet" in obj_type or "KBaseGenomeAnnotations.Assembly" in obj_type:
        # in this case we use the assembly file util to get the fasta file
        file_output = os.path.join(scratch, "input_fasta.fa")
        faf = au.get_assembly_as_fasta({"ref": upa})
        return [(faf['path'], upa)]

    fasta_paths = []
    for genome_upa in upas:
        if upa != genome_upa:
            genome_upa = upa + ';' + genome_upa
        genome_data = ws.get_objects2( {'objects':[{"ref":genome_upa}]})['data'][0]['data']
        target_upa = genome_data.get('contigset_ref') or genome_data.get('assembly_ref')
        assembly_upa = genome_upa + ';' + target_upa
        faf = au.get_assembly_as_fasta({"ref":assembly_upa})
        fasta_paths.append((faf['path'], assembly_upa))

    return fasta_paths
