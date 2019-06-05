# -*- coding: utf-8 -*-
#BEGIN_HEADER
import os
import subprocess
import collections
from installed_clients.KBaseReportClient import KBaseReport
from .utils.CMashUtils import CMashUtils
from .utils.misc_utils import load_fastas
#END_HEADER

cmash_scripts = '/opt/CMash/CMash/scripts/'

class kb_cmash:
    '''
    Module Name:
    kb_cmash

    Module Description:
    A KBase module: kb_cmash
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.workspace_url = config['workspace-url']
        self.shared_folder = config['scratch']
        self.cfg = config
        #END_CONSTRUCTOR
        pass


    def run_kb_cmash(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_kb_cmash
        if params.get('ref'):
            ref = params.get('ref')
        else:
            raise ValueError("must provide ws reference")
        if params.get('db'):
            db = params.get('db')
            # verify db is file
            if not os.path.isfile(db):
                raise ValueError(f"db path {db} not valid.")
        else:
            raise ValueError("must provide reference database")
        if params.get("n_max_results"):
            n_max_results = params.get('n_max_results')
        else:
            raise ValueError("Must provide n_max_results")

        # get fasta file from input reference
        fasta_paths = load_fastas(self.callback_url, self.shared_folder, ref)
        # load utils
        cmu = CMashUtils(self.cfg, self.callback_url, params['workspace_name'])
        results = cmu.query_db(db, fasta_paths)
        filtered_results = {}
        for upa in results:
            if len(results[upa]) > 0:
                filtered_results[upa] = results[upa]
        if len(filtered_results) < 1:
            html_path = os.path.join(self.shared_folder, "index.html")
            with open(html_path, 'w') as f:
                # f.write("<script>window.parent.document.getElementById().height = \"\";</script>")
                f.write("<body style=\"height:40px\"><h3 style=\"height: 40px\">No inputs have matched with any metagenomes in database %s</h3></body>"%params.get('db'))
        else:
            if sum([len(res) for upa, res in filtered_results.items()]) > n_max_results:
                # we want to keep the top 'n_max_results' hits.
                # in this case we want their 'dist' field to be higher.
                flatten = []
                for upa, res in filtered_results.items():
                    for hit in res:
                        flatten.append((upa, hit))
                flatten.sort(reverse=True, key=lambda x: x[1]['dist'])
                flatten = flatten[:n_max_results]
                filtered_results = collections.defaultdict(lambda: [])
                for item in flatten:
                    filtered_results[item[0]].append(item[1])

            html_path = cmu.output_to_html(filtered_results, 'index.html')

        output = cmu.get_report(html_path)
        #END run_kb_cmash

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_kb_cmash return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
