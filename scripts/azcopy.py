"""AzCopy"""

import os
from os import makedirs, path, sys
from glob import glob
from logging import getLogger
from tarfile import TarFile
from urllib.request import urlopen
from zipfile import ZipFile

from performance.common import (RunCommand, get_artifacts_directory,
                                get_tools_directory)


class AzCopy:
    """wrapper for calling AzCopy"""
    def __init__(self, sas: str, container_path: str, verbose: bool):
        self.container_url = 'https://pvscmdupload.blob.core.windows.net/results/'
        self.container_path = container_path
        self.sas = sas
        self.verbose = verbose

        if sys.platform == 'win32':
            self.archivename = 'azcopy.zip'
            self.exename = 'azcopy.exe'
            self.download_url = 'https://aka.ms/downloadazcopy-v10-windows'
        else:
            self.archivename = 'azcopy.tar.gz'
            self.exename = 'azcopy'
            self.download_url = 'https://aka.ms/downloadazcopy-v10-linux'

    def get_azcopy_directory(self) -> str:
        return path.join(get_tools_directory(), 'azcopy')

    def archive_path(self) -> str:
        return path.join(self.get_azcopy_directory(), self.archivename)

    def exe_path(self) -> str:
        return path.join(self.get_azcopy_directory(), self.exename)

    def get_upload_url(self) -> str:
        return "{0}{1}{2}".format(self.container_url, self.container_path, self.sas)

    def download_azcopy(self) -> None:
        if path.exists(self.exe_path()):
            return

        getLogger().info('downloading azcopy')
        if not path.isdir(self.get_azcopy_directory()):
            makedirs(self.get_azcopy_directory())

        with urlopen(self.download_url) as response, open(self.archive_path(), 'wb') as zipfile:
            zipfile.write(response.read())

        if sys.platform == 'win32':
            with ZipFile(self.archive_path()) as zipfile:
                item, = (zipfile for zipfile in zipfile.infolist() if zipfile.filename.endswith('.exe'))
                item.filename = path.basename(item.filename)
                zipfile.extract(item, self.get_azcopy_directory())
        else:
            tar = TarFile.open(self.archive_path())
            item, = (tar for tar in tar.getmembers() if tar.name.endswith('azcopy'))
            item.name = path.basename(item.name)
            tar.extract(item, self.get_azcopy_directory())
            tar.close()

    def upload_files(self, search_path: str):
        self.download_azcopy()
        cmdline = [
            self.exe_path(), 'copy', search_path, self.get_upload_url(), '--recursive=true'
        ]
        RunCommand(cmdline, verbose=self.verbose).run()

    @staticmethod
    def upload_results(container_path: str, verbose: bool) -> None:
        if os.getenv('PERFLAB_UPLOAD_TOKEN') and os.getenv("HELIX_CORRELATION_ID"):

            # first find if we have any files at all
            files = glob(path.join(
                get_artifacts_directory(),
                '**',
                '*perf-lab-report.json'), recursive=True)

            if files:
                # since we do, we will rename them to include the correlation ID
                for file in files:
                    directory_name = path.dirname(file)
                    filename = path.basename(file)
                    newname = "{0}-{1}".format(path.join(
                                                directory_name,
                                                os.getenv('HELIX_CORRELATION_ID')),
                                               filename)
                    os.rename(file, newname)

                renamed_files = glob(path.join(
                                        get_artifacts_directory(),
                                        '**',
                                        '*perf-lab-report.json'), recursive=True)


                dirname = path.dirname(renamed_files[0])
                if len(renamed_files) == 1:
                    # need to work around a bug in azcopy which loses file name if
                    # there is only one file.
                    # https://github.com/Azure/azure-storage-azcopy/issues/410
                    container_path = path.join(container_path, path.basename(renamed_files[0]))
                AzCopy(os.environ['PERFLAB_UPLOAD_TOKEN'],
                       container_path,
                       verbose).upload_files(path.join(dirname, '*perf-lab-report.json'))
