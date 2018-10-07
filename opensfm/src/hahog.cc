#include "types.h"
#include "hahog.h"

#include <vector>
#include <iostream>

extern "C" {
  #include "vl/covdet.h"
  #include "vl/sift.h"
  #include <time.h>
}


namespace csfm {

bp::object hahog(PyObject *image,
                 float peak_threshold,
                 float edge_threshold,
                 int target_num_features,
                 bool use_adaptive_suppression) {
  PyArrayContiguousView<float> im((PyArrayObject *)image);

  if (im.valid()) {
    //clock_t t_start = clock();
    // create a detector object
    VlCovDet * covdet = vl_covdet_new(VL_COVDET_METHOD_HESSIAN);
    // set various parameters (optional)
    vl_covdet_set_first_octave(covdet, 0);
    //vl_covdet_set_octave_resolution(covdet, octaveResolution);
    vl_covdet_set_peak_threshold(covdet, peak_threshold);
    vl_covdet_set_edge_threshold(covdet, edge_threshold);
    vl_covdet_set_target_num_features(covdet, target_num_features);
    vl_covdet_set_use_adaptive_suppression(covdet, use_adaptive_suppression);

    // process the image and run the detector
    vl_covdet_put_image(covdet, im.data(), im.shape(1), im.shape(0));

    //clock_t t_scalespace = clock();

    vl_covdet_detect(covdet);

    //clock_t t_detect = clock();

    // compute the affine shape of the features (optional)
    //vl_covdet_extract_affine_shape(covdet);

    //clock_t t_affine = clock();

    // compute the orientation of the features (optional)
    vl_covdet_extract_orientations(covdet);

    //clock_t t_orient = clock();

    // get feature descriptors
    vl_size numFeatures = vl_covdet_get_num_features(covdet);
    VlCovDetFeature const *feature = (VlCovDetFeature const *)vl_covdet_get_features(covdet);
    VlSiftFilt *sift = vl_sift_new(16, 16, 1, 3, 0);
    vl_index i;
    vl_size dimension = 128;
    vl_index patchResolution = 15;
    double patchRelativeExtent = 7.5;
    double patchRelativeSmoothing = 1;
    vl_size patchSide = 2 * patchResolution + 1;
    double patchStep = (double)patchRelativeExtent / patchResolution;
    std::vector<float> points(6 * numFeatures);
    std::vector<float> desc(dimension * numFeatures);
    std::vector<float> patch(patchSide * patchSide);
    std::vector<float> patchXY(2 * patchSide * patchSide);

    vl_sift_set_magnif(sift, 3.0);
    for (i = 0; i < (signed)numFeatures; ++i) {
      points[6 * i + 0] = feature[i].frame.x;
      points[6 * i + 1] = feature[i].frame.y;
      points[6 * i + 2] = feature[i].frame.a11;
      points[6 * i + 3] = feature[i].frame.a12;
      points[6 * i + 4] = feature[i].frame.a21;
      points[6 * i + 5] = feature[i].frame.a22;

      vl_covdet_extract_patch_for_frame(covdet,
                                        &patch[0],
                                        patchResolution,
                                        patchRelativeExtent,
                                        patchRelativeSmoothing,
                                        feature[i].frame);

      vl_imgradient_polar_f(&patchXY[0], &patchXY[1],
                            2, 2 * patchSide,
                            &patch[0], patchSide, patchSide, patchSide);

      vl_sift_calc_raw_descriptor(sift,
                                  &patchXY[0],
                                  &desc[dimension * i],
                                  (int)patchSide, (int)patchSide,
                                  (double)(patchSide - 1) / 2, (double)(patchSide - 1) / 2,
                                  (double)patchRelativeExtent / (3.0 * (4 + 1) / 2) / patchStep,
                                  VL_PI / 2);

    }
    vl_sift_delete(sift);
    vl_covdet_delete(covdet);

    // clock_t t_description = clock();
    // std::cout << "t_scalespace " << float(t_scalespace - t_start)/CLOCKS_PER_SEC << "\n";
    // std::cout << "t_detect " << float(t_detect - t_scalespace)/CLOCKS_PER_SEC << "\n";
    // std::cout << "t_affine " << float(t_affine - t_detect)/CLOCKS_PER_SEC << "\n";
    // std::cout << "t_orient " << float(t_orient - t_affine)/CLOCKS_PER_SEC << "\n";
    // std::cout << "description " << float(t_description - t_orient)/CLOCKS_PER_SEC << "\n";

    bp::list retn;
    npy_intp points_shape[2] = {npy_intp(numFeatures), 6};
    retn.append(bpn_array_from_data(2, points_shape, &points[0]));
    npy_intp desc_shape[2] = {npy_intp(numFeatures), npy_intp(dimension)};
    retn.append(bpn_array_from_data(2, desc_shape, &desc[0]));
    return retn;
  }
  return bp::object();
}

}
