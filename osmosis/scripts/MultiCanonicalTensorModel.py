import os
import nibabel as ni
import numpy as np
import matplotlib

import osmosis as oz
import osmosis.model as ozm
import osmosis.viz as viz
import osmosis.volume as ozv
import osmosis.utils as ozu
import osmosis.tensor as ozt 
reload(ozt)
reload(ozm)
reload(ozu)

data_path = os.path.split(oz.__file__)[0] + '/data/'

dwi_1k_1 = '0009_01_DWI_2mm150dir_2x_b1000_aligned_trilin.nii.gz'
dwi_1k_2 = '0011_01_DWI_2mm150dir_2x_b1000_aligned_trilin.nii.gz'

bvecs_1k_1 = '0009_01_DWI_2mm150dir_2x_b1000_aligned_trilin.bvecs'
bvecs_1k_2 = '0011_01_DWI_2mm150dir_2x_b1000_aligned_trilin.bvecs'

bvals_1k_1 = '0009_01_DWI_2mm150dir_2x_b1000_aligned_trilin.bvals'
bvals_1k_2 = '0011_01_DWI_2mm150dir_2x_b1000_aligned_trilin.bvals'

dwi_2k_1 = '0005_01_DTI_2mm_150dir_2x_b2000_aligned_trilin.nii.gz'
dwi_2k_2 = '0007_01_DTI_2mm_150dir_2x_b2000_aligned_trilin.nii.gz'

bvecs_2k_1 = '0005_01_DTI_2mm_150dir_2x_b2000_aligned_trilin.bvecs'
bvecs_2k_2 = '0007_01_DTI_2mm_150dir_2x_b2000_aligned_trilin.bvecs'

bvals_2k_1 = '0005_01_DTI_2mm_150dir_2x_b2000_aligned_trilin.bvals'
bvals_2k_2 = '0007_01_DTI_2mm_150dir_2x_b2000_aligned_trilin.bvals'


dwi_4k_1 = '0005_01_DWI_2mm150dir_2x_b4000_aligned_trilin.nii.gz'
dwi_4k_2 = '0007_01_DWI_2mm150dir_2x_b4000_aligned_trilin.nii.gz'

bvecs_4k_1 = '0005_01_DWI_2mm150dir_2x_b4000_aligned_trilin.bvecs'
bvecs_4k_2 = '0007_01_DWI_2mm150dir_2x_b4000_aligned_trilin.bvecs'

bvals_4k_1 = '0005_01_DWI_2mm150dir_2x_b4000_aligned_trilin.bvals'
bvals_4k_2 = '0007_01_DWI_2mm150dir_2x_b4000_aligned_trilin.bvals'

# These are based on the calculations in GetADandRD_multi_bval: 
AD = [1.7139, 1.4291, 0.8403]
RD = [0.3887, 0.3507, 0.2369]

for dwi1, bvecs1, bvals1, dwi2, bvecs2, bvals2, b, AD, RD, in zip(
        [dwi_1k_1, dwi_2k_1, dwi_4k_1],
        [bvecs_1k_1, bvecs_2k_1, bvecs_4k_1],
        [bvals_1k_1, bvals_2k_1, bvals_4k_1],
        [dwi_1k_2, dwi_2k_2, dwi_4k_2],
        [bvecs_1k_2, bvecs_2k_2, bvecs_4k_2],
        [bvals_1k_2, bvals_2k_2, bvals_4k_2],
        [1000, 2000, 4000],
        AD,
        RD):

    
    Model1 = ozm.MultiCanonicalTensorModel(data_path + dwi1,
                                     data_path + bvecs1,
                                     data_path + bvals1,
                                     mask=data_path + 'brainMask.nii.gz',
                                     radial_diffusivity=RD,
                                     axial_diffusivity=AD,
            params_file=data_path + 'MultiCanonicalTensorCombinedb%s.nii.gz'%b
                                     )
    
    Model2 = ozm.CanonicalTensorModel(data_path + dwi2,
                                     data_path + bvecs2,
                                     data_path + bvals2,
                                     mask=data_path + 'brainMask.nii.gz',
                                     radial_diffusivity=RD,
                                     axial_diffusivity=AD,
                                     )

    TM1 = ozm.TensorModel(data_path + dwi1,
                          data_path + bvecs1,
                          data_path + bvals1,
                          mask=data_path + 'brainMask.nii.gz')
    
    # Plot the parameter values:
    ax = viz.quick_ax()
    to_hist1 = Model1.model_params[Model1.mask,1]
    ax.hist(to_hist1[~np.isnan(to_hist1)], histtype='step',bins=1000,
            label='Canonical tensor #1')
    to_hist2 = Model1.model_params[Model1.mask,2]
    ax.hist(to_hist2[~np.isnan(to_hist2)], histtype='step', bins=1000,
            label='Canonical tensor #2')
    to_hist3 = Model1.model_params[Model1.mask,3]
    ax.hist(to_hist3[~np.isnan(to_hist3)], histtype='step', bins=1000,
            label='Sphere parameter')
    fig = ax.get_figure()
    fig.set_size_inches([10,5])
    ax.set_xlim([0,1])
    ax.set_xlabel('Parameter value')
    ax.set_ylabel('# voxels')
    ax.legend()
    fig.savefig('/Users/arokem/Dropbox/DWI_figures/MultiCanonicalTensor_params_%s.png'%b)

    idx = np.logical_and(to_hist1<1, to_hist2<1)

    T1 = ni.load(data_path + 'FP_t1_resampled_to_dwi.nii.gz').get_data()

    fig = viz.mosaic(T1.T, cmap=matplotlib.cm.bone, cbar=False)
    fig = viz.mosaic(Model1.model_params[:,:,:,1].T,
                     fig=fig, cmap=matplotlib.cm.hot, vmax=1)
    fig.set_size_inches([12,8])
    fig.savefig('/Users/arokem/Dropbox/DWI_figures/MultiCanonicalTensor_tensor_param%s.png'%b)
    
    fig = viz.mosaic(T1.T, cmap=matplotlib.cm.bone, cbar=False)
    fig = viz.mosaic(Model1.model_params[:,:,:,2].T,
                     fig=fig,
                     cmap=matplotlib.cm.hot,
                     vmax=1)
    fig.set_size_inches([12,8])
    fig.savefig('/Users/arokem/Dropbox/DWI_figures/MultiCanonicalTensor_sphere_param%s.png'%b)


    fractional_anisotropy = (
        (Model1.model_params[:,:,:,1]-Model1.model_params[:,:,:,2])/
        (Model1.model_params[:,:,:,1] + Model1.model_params[:,:,:,2]))

    fig = viz.mosaic(T1.T, cmap=matplotlib.cm.bone, cbar=False)
    fig = viz.mosaic(fractional_anisotropy.T,fig=fig,
                     cmap=matplotlib.cm.RdBu_r, vmax=1, vmin=-1)
    fig.set_size_inches([12,8])
    fig.savefig('/Users/arokem/Dropbox/DWI_figures/MultiCanonicalTensor_FA%s.png'%b)
    
    signal_rmse = np.nan * np.ones(Model1.shape[:3])
    signal_rmse[Model1.mask] = ozu.rmse(Model1._flat_signal,
                                        Model2._flat_signal)
    model_rmse = np.nan * np.ones(Model1.shape[:3])
    model_rmse[Model1.mask] = ozu.rmse(Model1.fit[Model1.mask],
                                       Model2._flat_signal)
    relative_rmse = np.nan * np.ones(Model1.shape[:3])
    relative_rmse = model_rmse/signal_rmse
    relative_rmse[np.isinf(relative_rmse)] = np.nan
    ax = viz.quick_ax()
    ax.hist(relative_rmse[~np.isnan(relative_rmse)],
            histtype='step',
            bins=100,
            color='g')
    fig = ax.get_figure()
    fig.set_size_inches([10,5])
    ax.set_xlim([0,2])
    ax.set_ylabel('# voxels')
    ax.set_xlabel('$RMSE_{relative}$')
    ax.set_title('Canonical Tensor model')
    fig.savefig('/Users/arokem/Dropbox/DWI_figures/MultiCanonicalTensor_RMSE_hist%s.png'%b)

    fig = viz.mosaic(T1.T, cbar=False, cmap=matplotlib.cm.bone)
    to_show = relative_rmse.copy()
    lb = 0.9
    ub = 1.5
    to_show[np.logical_or(to_show<lb, to_show>ub)] = np.nan

    fig = viz.mosaic(to_show.T,
                     fig=fig,
                     cmap=matplotlib.cm.YlOrRd,
                     vmin=0, vmax=1.5)
    fig.set_size_inches([15,10])

    fig.savefig('/Users/arokem/Dropbox/DWI_figures/MultiCanonicalTensor_RMSE_map_th%s.png'%b)

    fig2 = viz.mosaic(T1.T, cbar=False, cmap=matplotlib.cm.bone)
    fig2 = viz.mosaic(relative_rmse.T,
                      fig=fig2,
                      cmap=matplotlib.cm.YlOrRd,
                      vmin=0, vmax=1.5)
    fig2.set_size_inches([15,10])
    fig2.savefig('/Users/arokem/Dropbox/DWI_figures/MultiCanonicalTensor_RMSE_map%s.png'%b)
