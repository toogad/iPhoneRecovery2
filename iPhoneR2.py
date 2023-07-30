#! /usr/bin/python3

import pandas as pd
import sqlite3
import subprocess
from os.path import exists


def filepath_check(file_path, folder_type='work'):
    res = file_path
    i = 0
    while not exists(res):
        if i == 0:
            prompt = 'Enter the full path to the ' + folder_type + ' directory:'
        else:
            prompt = 'Path does NOT exist. Please re-enter with a valid existing directory: '
        res = input(prompt)
        i += 1
    if res[-1] != '/':
        res += '/'
    return res


def folder_search(base, sub, start):
    search = subprocess.run(["find", base, "-type", "d", "-name", sub], stdout=subprocess.PIPE)
    return [s.split('/')[-1] for s in search.stdout.decode('utf-8').split('\n')][start:-1]


work_dir = filepath_check('', 'full work')

backup_dir_by_Apple = filepath_check('', "Apple's /MobileSync/backup/")
backup_subfolders = folder_search(backup_dir_by_Apple, "*", 1)
print("List of found subfolders within Apple's backup collection: ", backup_subfolders)

target_subfolder = ''
while target_subfolder == '':
    target_subfolder_init = input('Enter the first few characters that distinguish the target folder: ')
    id = [k for k in range(len(backup_subfolders)) if target_subfolder_init in backup_subfolders[k]]
    if len(id) == 1:
        target_subfolder = backup_subfolders[0]
    else:
        print('Wrong subfolder name initials... Please retry.')
        target_subfolder = ''
print("Selected TARGET subfolder: ", target_subfolder)


conn = sqlite3.connect(backup_dir_by_Apple + target_subfolder + '/Manifest.db')
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

backupPath = []
recoveredName = []
for id in df_filtered.index:
    backup_file_id = str(df_filtered['fileID'][id])
    backup_mainfolder = backup_dir_by_Apple + str(target_subfolder) + '/' + str(df_filtered['fileID'][id])[:2]
    backup_path_search = subprocess.run(["find", backup_mainfolder, "-name", backup_file_id], stdout=subprocess.PIPE)
    backup_path = backup_path_search.stdout.decode('utf-8')[:-1]
    recovered_filename = df_filtered['relativePath'][id].replace('/', '_')
    backupPath.append(backup_path)
    recoveredName.append(recovered_filename)
df_filtered['backupPath'] = backupPath
df_filtered['recoveredName'] = recoveredName
df_filtered.to_csv(work_dir + 'extraction_map.csv')

recover_subfolder = filepath_check('', 'recovered file subfolder')

recover_dir = recover_subfolder
mk_dir = subprocess.run(["mkdir", recover_dir])
print(mk_dir.stdout)
for id in df_filtered.index:
    subprocess.run(["cp", df_filtered['backupPath'][id], recover_dir + '/' + df_filtered['recoveredName'][id]])
