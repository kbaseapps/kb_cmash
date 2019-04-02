# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from kb_cmash.kb_cmashImpl import kb_cmash
from kb_cmash.kb_cmashServer import MethodContext
from kb_cmash.authclient import KBaseAuth as _KBaseAuth

from kb_cmash.utils.CMashUtils import CMashUtils
from kb_cmash.utils.ui_utils import format_results

from installed_clients.WorkspaceClient import Workspace

class kb_cmashTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_cmash'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_cmash',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = kb_cmash(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        if hasattr(self.__class__, 'wsName'):
            return self.__class__.wsName
        suffix = int(time.time() * 1000)
        wsName = "test_kb_cmash_" + str(suffix)
        ret = self.getWsClient().create_workspace({'workspace': wsName})  # noqa
        self.__class__.wsName = wsName
        return wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    def test_genome_set_input(self):
        """
        test genome set as input
        """
        gs_ref = "23594/20/1"
        db = "100_metagenomes_testdb.h5"

        ret = self.getImpl().run_kb_cmash(self.getContext(), {
            'workspace_name': self.getWsName(),
            'ref': gs_ref,
            'n_max_results': 10,
            'db':db
        })

    def test_assembly_input(self):
        """
        """
        ref = "23594/10/1"
        db = "100_metagenomes_testdb.h5"

        ret = self.getImpl().run_kb_cmash(self.getContext(), {
            'workspace_name': self.getWsName(),
            'ref': ref,
            'n_max_results': 10,
            'db':db
        })

    def test_from_files(self):
        '''
        test on local file
        '''
        fasta_path = "data/MGYA00237725_ERZ505430_FASTA.fa"
        db = "data/100_metagenomes_testdb.h5"

        cmu = CMashUtils(self.__class__.cfg, self.wsURL, self.callback_url)
        results = cmu.query_db(db, [(fasta_path, '0/0/0')])
        stats, upa_names, tree, markers = format_results(self.wsURL, self.callback_url, results, is_test=True)

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_your_method(self):
        # Prepare test objects in workspace if needed using
        # self.getWsClient().save_objects({'workspace': self.getWsName(),
        #                                  'objects': []})
        #
        # Run your method by
        # ret = self.getImpl().your_method(self.getContext(), parameters...)
        #
        # Check returned data with
        # self.assertEqual(ret[...], ...) or other unittest methods
        ref = "22385/47/1"
        db = "100_metagenomes_testdb.h5"

        ret = self.getImpl().run_kb_cmash(self.getContext(), {
            'workspace_name': self.getWsName(),
            'ref': ref,
            'n_max_results': 10,
            'db':db
        })
