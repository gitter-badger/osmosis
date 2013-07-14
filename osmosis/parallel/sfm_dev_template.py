
# Lines above this one are auto-generated by the wrapper to provide as params:
# this_dir
import osmosis.model.sparse_deconvolution as sfm
import nibabel as nib
import scipy.io as sio
import os
import numpy as np

if __name__=="__main__":
    dt6 = sio.loadmat(os.path.join(this_dir, "dt6.mat"),
                      squeeze_me=True)
    data = [str(x) for x in [dt6["files"]["alignedDwRaw"],
                             dt6["files"]["alignedDwBvecs"],
                             dt6["files"]["alignedDwBvals"]]]

    M = sfm.SparseDeconvolutionModel(*data,
                                     axial_diffusivity=1.5,
                                     radial_diffusivity=0.5,
                                     force_recompute=True)

    nib.Nifti1Header(M.dispersion_index(), M.affine).to_filename(
                          M.params_file.split(".")[0] + "_DI.nii.gz")
