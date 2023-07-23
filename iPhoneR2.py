#! /usr/bin/python3

import pandas as pd
import sqlite3
import subprocess
from os.path import exists


def filepath_check(file_path):
    res = file_path
    while not exists(res):
        res = input("Path does NOT exist. Please re-enter with a valid existing directory: ")
    if res[-1] != '/':
        res += '/'
    return res


work_dir = input("Enter the full work directory:")
work_dir = filepath_check(work_dir)

backup_dir_by_Apple = input('Enter the full backup directory where the Manifest.db is stored:')
backup_dir_by_Apple = filepath_check(backup_dir_by_Apple)

conn = sqlite3.connect(backup_dir_by_Apple + 'Manifest.db')
query = "SELECT * FROM Files"
df = pd.read_sql_query(query, conn)
print(df.columns)

df = df[ ['fileID','relativePath'] ]
df.to_csv(work_dir + 'full_list.csv')

ext_filter = ['.jpg', '.jpeg', '.png', '.heic', '.tiff', '.pic',
              '.pdf', '.docx', '.xlsx',
              '.mov', '.mp4', '.mp3','.flac']

to_keep = [ (rel_path[-4:].lower() in ext_filter or rel_path[-5:].lower() in ext_filter)
            and 'dcim' in rel_path.lower()
            and 'thumbnail' not in rel_path.lower()
            and 'metadata' not in rel_path.lower()
            for rel_path in df['relativePath'] ]
df['keep'] = to_keep
df_filtered = df[ df['keep'] == True ].sort_values(by='fileID').reset_index(drop=True)
df_filtered.to_csv(work_dir + 'filtered.csv')

#TODO: allow user input for the subfolder_init
subfolder_init = "00008*"
backup_subfolder_search = subprocess.run(["find", backup_dir_by_Apple, "-type", "d", "-name", subfolder_init],
                                         stdout=subprocess.PIPE)
subfolder = backup_subfolder_search.stdout.decode('utf-8')[:-1].split('/')[-1]
print(subfolder)

backupPath = []
recoveredName = []
for id in df_filtered.index:
    backup_file_id = str(df_filtered['fileID'][id])
    backup_mainfolder = backup_dir_by_Apple + str(subfolder) + '/' + str(df_filtered['fileID'][id])[:2]
    backup_path_search = subprocess.run(["find", backup_mainfolder, "-name", backup_file_id], stdout=subprocess.PIPE)
    backup_path = backup_path_search.stdout.decode('utf-8')[:-1]
    recovered_filename = df_filtered['relativePath'][id].replace('/', '_')
    backupPath.append(backup_path)
    recoveredName.append(recovered_filename)
df_filtered['backupPath'] = backupPath
df_filtered['recoveredName'] = recoveredName
df_filtered.to_csv(work_dir + 'extraction_map.csv')

#TODO: check and repeat if needed
recover_subfolder = input("Enter the subfolder in the work directory to store the files to be recovered:")

recover_dir = work_dir + recover_subfolder
mk_dir = subprocess.run(["mkdir", recover_dir])
print(mk_dir.stdout)
for id in df_filtered.index:
    subprocess.run(["cp", df_filtered['backupPath'][id], recover_dir + '/' + df_filtered['recoveredName'][id]])
