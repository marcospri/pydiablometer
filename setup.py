import py2exe

from distutils.core import setup
import os


def all_dir(path, dest):
    dataFiles = []
    for root, dirs, files in os.walk(path):
        sampleList = []
        if files:
            for filename in files:
                sampleList.append(root + "/" + filename)

            if sampleList:
                dataFiles.append((root.replace(path, dest), sampleList))
    return dataFiles

data_files = []

data_files.extend(all_dir("./widgets", "./widgets"))

options = {
    'py2exe': {
        'compressed': True,
        'optimize': 2,
        'bundle_files': 1,
        'dll_excludes': [
            'MSVCP90.dll', "mswsock.dll", "powrprof.dll",
         ],
        'includes': ['PySide.QtXml', 'pyHook']
     }
}

setup(
    data_files=data_files,
    windows=[{'script': 'pydiablometer.py'}],
    options=options
)
