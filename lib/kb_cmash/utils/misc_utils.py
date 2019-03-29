import os
from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.GenomeFileUtilClient import GenomeFileUtil

def load_fastas(callback_url, scratch, upa):
    '''

    '''
    dfu = DataFileUtil(callback_url)

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
        au = AssemblyUtil(callback_url)
        file_output = os.path.join(scratch, "input_fasta.fa")
        faf = au.get_assembly_as_fasta({"ref": upa})
        fasta_path = faf['path']
        return [(fasta_path, upa)]

    gfu = GenomeFileUtil(callback_url)
    fasta_paths = []
    for upa in upas:
        faf = gfu.genome_features_to_fasta({"genome_ref": upa})
        fasta_paths.append((faf['file_path'], upa))
    return fasta_paths
