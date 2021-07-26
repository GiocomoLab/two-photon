import glob
import pandas as pd
import os
pattern = r'F:\AA\output\**\artefact.h5'

for f in glob.glob(pattern,recursive=True):
    
    new_name = f.replace('.h5','.csv')
    if os.path.isfile(new_name):
        print(new_name +' exists, skipping.')
    else:
        df = pd.read_hdf(f,key='data')

        df.to_csv(new_name)