# -*- coding: utf-8 -*-
#BEGIN_HEADER
import os
import subprocess
from installed_clients.KBaseReportClient import KBaseReport
from .utils.CMashUtils import CMashUtils

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
        ref = params['ref']
        db  = os.path.join("utils/data",params['db'])
        # get fasta file from input reference
        fasta_path = load_fasta(ref)
        # form reference database
        fasta_dir = []

        cmu = CMashUtils(self.cfg, params['workspace_name'])
        # db = cmu.build_db(fasta_dir)
        # db = "utils/data/soil_test_4_samples.h5"
        output_csv = cmu.query_db(db, fasta_path)
        output = cmu.get_report(output_csv)

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
