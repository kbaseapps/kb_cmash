import os
from installed_clients.AssemblyUtilClient import AssemblyUtil

def load_fasta(callback_url, scratch, ref):
    au = AssemblyUtil(callback_url)
    file_output = os.path.join(scratch, "input_fasta.fa")
    faf = au.get_assembly_as_fasta({"ref": ref})
    fasta_path = faf['path']
    return fasta_path
