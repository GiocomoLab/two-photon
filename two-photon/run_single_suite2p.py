import numpy as np
import suite2p

ops = np.load(r'F:\AA\output\20210619_M217\vr_stim-003\output\suite2p\combined\ops.npy',allow_pickle = True).item()
suite2p.run_s2p(ops=ops)