
# Lines above this one are auto-generated by the wrapper to provide as params:
# i
import time
import osmosis.model.sparse_deconvolution as sfm
import osmosis.model.dti as dti
import osmosis.predict_n as pn
from osmosis.utils import separate_bvals
import osmosis.utils as ozu
import nibabel as nib
import os
import numpy as np

if __name__=="__main__":
    t1 = time.time()
    data_path = "/biac4/wandell/data/klchan13/100307/Diffusion/data"
    
    data_file = nib.load(os.path.join(data_path, "data.nii.gz"))
    wm_data_file = nib.load(os.path.join(data_path,"wm_mask_registered.nii.gz"))
    
    data = data_file.get_data()
    wm_data = wm_data_file.get_data()
    wm_idx = np.where(wm_data==1)
    
    bvals = np.loadtxt(os.path.join(data_path, "bvals"))
    bvecs = np.loadtxt(os.path.join(data_path, "bvecs"))
    
    low = i*2000
    # Make sure not to go over the edge of the mask:
    high = np.min([(i+1) * 2000, int(np.sum(wm_data))])
    
    # Preserve memory by getting rid of this data:
    del wm_data

    # Now set the mask:
    mask = np.zeros(wm_data_file.shape)
    mask[wm_idx[0][low:high], wm_idx[1][low:high], wm_idx[2][low:high]] = 1

    # Predict 10% (n = 10)
    ad = {1000:1.6386920952169737, 2000:1.2919249903637751, 3000:0.99962593218241236}
    rd = {1000:0.33450124887561905, 2000:0.28377379537043729, 3000:0.24611723207420028}
    
    bval_list, b_inds, unique_b, rounded_bvals = ozu.separate_bvals(bvals)
    all_b_idx = np.where(rounded_bvals != 0)
    
    mod = sfm.SparseDeconvolutionModelMultiB(data, bvecs, bvals, mask = mask,
                                            params_file = "temp", solver = "nnls",
                                            mean = "mean_model", axial_diffusivity = ad,
                                            radial_diffusivity = rd)
    mp = mod.model_params[np.where(mask)]
    
    aff = np.eye(4)
    np.save("/hsgs/nobackup/klchan13/model_params_se_single%s.npy"%i, mp)
    
    t2 = time.time()
    print "This program took %4.2f minutes to run."%((t2 - t1)/60.)