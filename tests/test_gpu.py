import unittest
from executors import permitted, command
from gpu import approved, docker_args

IMAGE='sha256' + ':' + 'a'*64
BASE={'allow_container':True,'allowed_images':[IMAGE], 'container_runtime':'docker'}
D={'execution':'container','image':IMAGE,'gpu':'cuda','command':['/bin/true'],'capabilities':['gpu.cuda']}
class GPU(unittest.TestCase):
    def test_cuda_requires_explicit_capability_and_consent(self):
        p={**BASE,'gpu':{'enabled':True,'backend':'cuda','device_ids':['0']}}
        self.assertTrue(permitted(D,p))
        argv=command(D,p,'/source','/inputs','/out','attempt')
        self.assertEqual(argv[argv.index('--gpus')+1],'device=0')
        self.assertIn('--network=none',argv)
        self.assertIn('--read-only',argv)
        self.assertFalse(permitted(D,BASE))
        self.assertFalse(permitted({**D,'capabilities':[]},p))
        self.assertFalse(permitted({**D,'gpu':'rocm'},p))
        self.assertFalse(permitted({**D,'execution':'scripted'},p))
        self.assertFalse(permitted({**D,'image':'ubuntu:latest'},p))
        self.assertFalse(permitted({**D,'gpu':None},p))
    def test_rocm_mappings_are_tight(self):
        p={**BASE,'gpu':{'enabled':True,'backend':'rocm',
            'render_devices':['/dev/dri/renderD128'],'group_ids':[110],
            'hsa_override_gfx_version':'10.3.0'}}
        d={**D,'gpu':'rocm','capabilities':['compute.cpu','gpu.rocm']}
        self.assertTrue(permitted(d,p))
        argv=command(d,p,'/source','/inputs','/out','attempt')
        self.assertEqual(argv.count('--device'),2)
        self.assertIn('/dev/kfd',argv)
        self.assertIn('/dev/dri/renderD128',argv)
        self.assertIn('110',argv)
        self.assertIn('HSA_OVERRIDE_GFX_VERSION=10.3.0',argv)
        for path in ('/dev/dri/../nvidia0','/dev/dri/card0','/dev/kfd','/tmp/fake'):
            cfg={**p,'gpu':{**p['gpu'],'render_devices':[path]}}
            self.assertFalse(permitted(d,cfg),path)
        self.assertFalse(permitted(d,{**p,'gpu':{**p['gpu'],'group_ids':['110']}}))
        self.assertFalse(permitted(d,{**p,'gpu':{**p['gpu'],'hsa_override_gfx_version':'1;rm -rf /'}}))
    def test_no_implicit_gpu_devices(self):
        d={**D,'gpu':None,'capabilities':['compute.cpu']}
        p={**BASE}
        self.assertTrue(permitted(d,p))
        self.assertNotIn('--gpus',command(d,p,'s','i','o','n'))
        self.assertFalse(approved({**d,'capabilities':['gpu.cuda']},p))
        self.assertFalse(approved({**d,'gpu':'cuda'},p))
