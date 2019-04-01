import os
import subprocess
import json
import math
import uuid
import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape
import pprint

from installed_clients.KBaseReportClient import KBaseReport
from .ui_utils import format_results

env = Environment(
    loader=PackageLoader('kb_cmash','utils/templates'),
    autoescape=select_autoescape(['html'])
)

pp = pprint.PrettyPrinter(indent=4)

class CMashUtils():
    '''
    Utilities for CMash
    '''
    def __init__(self, config, callback_url, workspace_name):
        self.shared_folder = config['scratch']
        self.callback_url  = callback_url
        self.workspace_url = config['workspace-url']
        self.cmash_scripts = '/opt/CMash/scripts/'
        self.workspace_name = workspace_name

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


    def query_db(self, db, fasta_paths):
        '''
        '''
        if not os.path.isdir(os.path.join(self.shared_folder, 'output')):
            os.mkdir(os.path.join(self.shared_folder, 'output'))
        query_script = os.path.join(self.cmash_scripts, 'QueryDNADatabase.py')
        outputs = {}

        for fasta_path, upa in fasta_paths:
            fasta_name = fasta_path.split('/')[-1].split('.')[0]
            output = os.path.join(self.shared_folder, 'output', fasta_name+'.csv')
            query_db_args = ['python', query_script, fasta_path, db, output]
            try:
                status_code = subprocess.check_output(query_db_args)
            except subprocess.CalledProcessError as grepexc:
                raise ValueError("error code:", grepexc.returncode, grepexc.output)

            outputs[upa] = self._process_output(output)

        return outputs


    def _process_output(self, output_csv):
        '''
        process output csv file from CMash database query
        '''
        if os.path.isfile(output_csv):
            output_df = pd.read_csv(output_csv)
            columns = list(output_df.columns)
            columns[0] = "file_path"
            columns = {output_df.columns[i]:columns[i].lower().strip().replace(" ", "_") for i in range(len(columns))}
            output_df.rename(columns=columns, inplace=True)
            output_df['assembly_id'] = None
            output_df['mgy_id'] = None
            for idx, row in output_df.iterrows():
                fp = row['file_path']
                sample_id = fp.split('/')[-1].split('_')[1]
                mgy_id = fp.split('/')[-1].split('_')[0]
                output_df.loc[idx,'assembly_id'] =  sample_id
                output_df.loc[idx,'mgy_id'] = mgy_id

            output_df.loc[:,'dist'] = output_df['containment_index']

            records = output_df.to_dict('records')
            return records
        else:
            raise RuntimeError("output csv file does not exist.")


    def _get_remaining_args(self, stats, tree, upa_names):
        '''
        Get the remaining output arguments from the provided inputs
        '''
        minimum_step = 0.001
        num_steps = 100
        min_dist   = math.floor(100*min([s['dist'] for s in stats]))/100.0
        max_dist   = math.ceil(100*max([s['dist'] for s in stats]))/100.0
        step_dist  = max( round((max_dist-min_dist)/num_steps, 3), minimum_step)

        ranges = [min_dist, max_dist, step_dist]

        shortened_upa_names = []
        shortened_len = 18
        for s in upa_names:
            s = str(s)
            if len(s) <= shortened_len:
                shortened_upa_names.append(s)
            else:
                shortened_upa_names.append(s[:shortened_len-3] + "...")

        if len(upa_names) > 1:
            number_of_points = max(list(tree['sources'].values()))
        else:
            number_of_points = tree['count_num']
        return ranges, shortened_upa_names, number_of_points


    def output_to_html(self, results, html_file):
        '''
        '''
        html_path = os.path.join(self.shared_folder, html_file)
        stats, upa_names, tree, markers = format_results(self.workspace_url, self.callback_url, results)

        # print("="*80)
        # print("STATS",stats)
        # print("TREE")
        # pp.pprint(tree)
        # print("UPA NAMES", upa_names)
        # print("MARKERS", markers)



        ranges, shortened_upa_names, number_of_points = self._get_remaining_args(stats, tree, upa_names)

        # print("RANGES", ranges)
        # print("SHORT UPA NAMES", shortened_upa_names)
        # print("NUMBER OF POINTS", number_of_points)
        # print("="*80)
        template = env.get_template(html_file)

        #[ranges, markers, sources, tree,  short_sources, number_of_points]
        # if len(upa_names) > 1:
        rendered_html = template.render(
            ranges=ranges,
            markers=markers,
            tree=tree,
            sources=upa_names,
            short_sources=shortened_upa_names,
            number_of_points=number_of_points
        )
        # else:
            # rendered_html = template.render(
            #     ranges=ranges,
            #     markers=markers,
            #     tree=tree,
            #     sources=upa_names,
            #     short_sources=shortened_upa_names,
            #     number_of_points=number_of_points
            # )
        with open(html_path, 'w') as f:
            f.write(rendered_html)
        return html_path

    def get_report(self, html_path):
        '''
        '''
        report_client = KBaseReport(self.callback_url)
        report_name = 'kb_cmash_'+str(uuid.uuid4())

        html_link = {
            'path': html_path,
            'name': 'index.html',
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
