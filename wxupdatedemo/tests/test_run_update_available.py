"""
Test ability to run PyUpdaterWxDemo and confirm that an update is available.

We don't want this test to be dependent on having a
client_config.py (created by pyupdater init), so
we set the WXUPDATEDEMO_TESTING environment variable
before loading the wxupdatedemo.config module or
the run module.
"""
# pylint: disable=bad-continuation
# pylint: disable=line-too-long
import unittest
import os
import sys
import gzip
import json
import shutil
import tempfile

import ed25519
import six
import wx

from wxupdatedemo import __version__

APP_NAME = 'PyUpdaterWxDemo'
CURRENT_VERSION = '0.0.1'
UPDATE_VERSION = '0.0.2'
# PyUpdater version format is:
# Major.Minor.Patch.[Alpha|Beta|Stable].ReleaseNumber
# where Alpha=0, Beta=1 and Stable=2
UPDATE_VERSION_PYU_FORMAT = '%s.2.0' % UPDATE_VERSION

VERSIONS = {
  "updates": {
    APP_NAME: {
      UPDATE_VERSION_PYU_FORMAT: {
        "mac": {
          "file_hash": "bd4bc8824dfd8240d5bdb9e46f21a86af4d6d1cc1486a2a99cc4b9724a79492b",
          "filename": "%s-mac-%s.tar.gz" % (APP_NAME, UPDATE_VERSION),
          "file_size": 30253628
        },
        "win": {
          "file_hash": "b1399df583bce4ca45665b3960fd918a316d86c997d6c33556eda1cc2b555e59",
          "filename": "%s-win-%s.zip" % (APP_NAME, UPDATE_VERSION),
          "file_size": 14132995
        }
      }
    }
  },
  "latest": {
    APP_NAME: {
      "stable": {
        "mac": UPDATE_VERSION_PYU_FORMAT,
        "win": UPDATE_VERSION_PYU_FORMAT
      }
    }
  }
}

# Generated by "pyupdater keys -c":
# These keys are only used for automated testing!
# DO NOT SHARE YOUR PRODUCTION PRIVATE_KEY !!!
PUBLIC_KEY = "12y2oHGB2oroRQJkR73CJNaFeQy776oXsUrqWaAEiZU"
PRIVATE_KEY = "nHgoNwSmXSDNSMqQTtdAEmi/6otajiNYJEXESvAO8dc"

KEYS = {
  "app_public": "MIBCEwFh7AcaxJrHKIgYqAmZ9YX16NXVHLi+EdDmtYc",
  "signature": "1YTDuJauq7qVFUrKPHGMMESllJ4umo6u5r9pEgVmvlxgXi3qGXnKWo2LG94+oosN3KiO8DlxOmyfuwaaQKtFCw"
}


class RunTester(unittest.TestCase):
    """
    Test ability to run PyUpdaterWxDemo and confirm that an update is available.
    """
    def __init__(self, *args, **kwargs):
        super(RunTester, self).__init__(*args, **kwargs)
        self.app = None
        self.fileServerDir = None

    def setUp(self):
        tempFile = tempfile.NamedTemporaryFile()
        self.fileServerDir = tempFile.name
        tempFile.close()
        os.mkdir(self.fileServerDir)
        os.environ['PYUPDATER_FILESERVER_DIR'] = self.fileServerDir
        privateKey = ed25519.SigningKey(PRIVATE_KEY.encode('utf-8'),
                                        encoding='base64')
        signature = privateKey.sign(six.b(json.dumps(VERSIONS, sort_keys=True)),
                                    encoding='base64').decode()
        VERSIONS['signature'] = signature
        keysFilePath = os.path.join(self.fileServerDir, 'keys.gz')
        with gzip.open(keysFilePath, 'wb') as keysFile:
            keysFile.write(json.dumps(KEYS, sort_keys=True))
        versionsFilePath = os.path.join(self.fileServerDir, 'versions.gz')
        with gzip.open(versionsFilePath, 'wb') as versionsFile:
            versionsFile.write(json.dumps(VERSIONS, sort_keys=True))
        os.environ['WXUPDATEDEMO_TESTING'] = 'True'
        from wxupdatedemo.config import CLIENT_CONFIG
        self.clientConfig = CLIENT_CONFIG
        self.clientConfig.PUBLIC_KEY = PUBLIC_KEY
        self.clientConfig.APP_NAME = APP_NAME

    def test_run_update_available(self):
        """
        Test ability to run PyUpdaterWxDemo and confirm that an update is available.
        """
        self.assertEqual(__version__, CURRENT_VERSION)
        from run import Run
        self.app = Run(argv=['RunTester', '--debug'],
                       clientConfig=self.clientConfig)
        self.assertEqual(self.app.statusBar.GetStatusText(),
                         "Update available but application is not frozen.")
        sys.stderr.write("We can only restart a frozen app!\n")

    def tearDown(self):
        """
        Destroy the app
        """
        if self.app:
            self.app.frame.Hide()
            self.app.OnCloseFrame(wx.PyEvent())
            self.app.frame.Destroy()
        del os.environ['PYUPDATER_FILESERVER_DIR']
        del os.environ['WXUPDATEDEMO_TESTING']
        shutil.rmtree(self.fileServerDir)