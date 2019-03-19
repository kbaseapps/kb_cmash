import os
import subprocess
import json
import uuid
import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape

from installed_clients.KBaseReportClient import KBaseReport

env = Environment(
    loader=PackageLoader('kb_cmash','utils/templates'),
    autoescape=select_autoescape(['html'])
)

class CMashUtils():
    '''
    Utilities for CMash
    '''
    def __init__(self, config, callback_url, workspace_name):
        self.shared_folder = config['scratch']
        self.callback_url  = callback_url
        self.cmash_scripts = '/opt/CMash/scripts/'
        self.workspace_name = workspace_name

        pass

    def build_db(self, fasta_dir):
        '''
        '''
        fasta_txt_file = 'FastaFileNames.txt'
        subprocess.check_output('ls '+ fasta_dir + ' > ' + fasta_txt_file)
        h5_db = 'TrainingDatabase.h5'

        make_dna = os.path.join(self.cmash_scripts, 'MakeDNADatabase.py')
        build_db_args = ['python', make_dna,
                fasta_txt_file, h5_db]
        subprocess.check_output(build_db_args)

        return h5_db


    def query_db(self, db, input_fasta):
        '''
        '''
        output = os.path.join(self.shared_folder, 'output.csv')
        query_script = os.path.join(self.cmash_scripts, 'QueryDNADatabase.py')
        query_db_args = ['python', query_script, input_fasta, db, output]
        subprocess.check_output(query_db_args)

        return output

    def _process_output(self, output_df):
        '''
        '''
        return [output_df.to_dict()]

    def _output_to_html(self, output_csv, html_file):
        '''
        '''
        html_path = os.path.join(self.shared_folder, html_file)
        formatted_csv = self._process_output(pd.read_csv(output_csv))
        template = env.get_template(html_file)
        rendered_html = template.render(results=formatted_csv)
        with open(html_path, 'w') as f:
            f.write(rendered_html)
        return html_path

    def get_report(self, output_csv):
        '''
        '''
        report_client = KBaseReport(self.callback_url)
        report_name = 'kb_cmash_'+str(uuid.uuid4())

        html_file = self._output_to_html(output_csv, 'output_csv.html')
        html_link = {
            'path': html_file,
            'name': 'output_csv.html',
            'description':'CMash output similarity list'
        }

        report_info = report_client.create_extended_report({
            'direct_html_link_index':0,
            'html_links':[html_link],
            'workspace_name': self.workspace_name,
            'report_object_name': report_name,
        })

        return {
            'report_name': report_info['name'],
            'report_ref': report_info['ref']
        }
