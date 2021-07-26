import glob
import numpy as np
import os
import matplotlib.pyplot as plt
import imageio
pattern = r'F:\AA\output\20210425_M3\**\plane?\ops.npy'

for f in glob.glob(pattern,recursive=True):
    ops = np.load(f,allow_pickle=True).item()
    meanImg = ops['meanImg']
    fn = f.replace('ops.npy','meanImage.png')
    plt.imsave(fn,meanImg,cmap='gray')
    fnt = fn.replace('.png','.tif')
    imageio.imwrite(fnt,np.uint16(meanImg))
 