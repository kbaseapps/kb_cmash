# -*- coding: utf-8 -*-
import os
import time
import unittest
import shutil
from configparser import ConfigParser

from kb_cmash.kb_cmashImpl import kb_cmash
from kb_cmash.kb_cmashServer import MethodContext
from kb_cmash.authclient import KBaseAuth as _KBaseAuth

from kb_cmash.utils.CMashUtils import CMashUtils
from kb_cmash.utils.ui_utils import format_results

from installed_clients.WorkspaceClient import Workspace
from installed_clients.AssemblyUtilClient import AssemblyUtil

SMALL_DB = "/kb/module/lib/kb_cmash/utils/data/100_metagenomes_testdb.h5"
BIG_DB = "/data/CMash_db_size8945.h5"

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
        ret = self.getImpl().run_kb_cmash(self.getContext(), {
            'workspace_name': self.getWsName(),
            'ref': gs_ref,
            'n_max_results': 10,
            'db': SMALL_DB
        })

    def test_assembly_input(self):
        """
        """
        ref = "23594/10/1"
        ret = self.getImpl().run_kb_cmash(self.getContext(), {
            'workspace_name': self.getWsName(),
            'ref': ref,
            'n_max_results': 10,
            'db': SMALL_DB
        })

    def test_from_files(self):
        '''
        test on local file
        '''
        fasta_path = "data/MGYA00237725_ERZ505430_FASTA.fa"

        cmu = CMashUtils(self.__class__.cfg, self.wsURL, self.callback_url)
        results = cmu.query_db(SMALL_DB, [(fasta_path, '0/0/0')])
        stats, upa_names, tree, markers = format_results(self.wsURL, self.callback_url, results, is_test=True)

    def test_bigger_db_with_genome_set(self):
        """
        """
        gs_ref = "23594/20/1"
        ret = self.getImpl().run_kb_cmash(self.getContext(), {
            'workspace_name': self.getWsName(),
            'ref': gs_ref,
            'n_max_results': 10,
            'db': BIG_DB
        })

    def test_bigger_db(self):
        """
        test against bigger database
        """
        ref = "22385/47/1"
        ret = self.getImpl().run_kb_cmash(self.getContext(), {
            'workspace_name': self.getWsName(),
            'ref': ref,
            'n_max_results': 10,
            'db': BIG_DB
        })

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_small_db(self):
        ref = "22385/47/1"

        ret = self.getImpl().run_kb_cmash(self.getContext(), {
            'workspace_name': self.getWsName(),
            'ref': ref,
            'n_max_results': 10,
            'db': SMALL_DB
        })

    def test_au1(self):
        """"""
        f_name = "mid_fasta_spoof.fasta"
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = curr_dir + "/data/" + f_name
        new_file_path = self.scratch + "/" + f_name
        shutil.copyfile(file_path, new_file_path)

        if not os.path.isfile(new_file_path):
            print("CANNOT FIND INPUT FILE")
            self.assertEqual(True, False)
        else:
            au = AssemblyUtil(self.callback_url)
            # au = AssemblyUtil(self.callback_url, service_ver="dev")
            assembly_params = {
                'file':  {
                    'path': new_file_path,
                    'assembly_name': "MetagenomeTestSpoofAssembly"
                },
                'assembly_name': "MetagenomeTestSpoofAssembly",
                'workspace_name': self.getWsName()
            }
            au.save_assembly_from_fasta(assembly_params)

    # def test_au2(self):
    #     """"""
    #     f_name = "mid_fasta_spoof.fasta"
    #     curr_dir = os.path.dirname(os.path.realpath(__file__))
    #     file_path = curr_dir + "/data/" + f_name
    #     new_file_path = self.scratch + "/" + f_name
    #     shutil.copyfile(file_path, new_file_path)

    #     if not os.path.isfile(new_file_path):
    #         print("CANNOT FIND INPUT FILE")
    #         self.assertEqual(True, False)
    #     else:
    #         # au = AssemblyUtil(self.callback_url)
    #         au = AssemblyUtil(self.callback_url, service_ver="dev")
    #         assembly_params = {
    #             'file':  {
    #                 'path': new_file_path,
    #                 'assembly_name': "MetagenomeTestSpoofAssembly"
    #             },
    #             'assembly_name': "MetagenomeTestSpoofAssembly",
    #             'workspace_name': self.getWsName()
    #         }
    #         au.save_assembly_from_fasta(assembly_params)
