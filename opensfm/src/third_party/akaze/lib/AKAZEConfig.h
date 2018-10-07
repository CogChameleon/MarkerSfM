/**
 * @file AKAZEConfig.h
 * @brief AKAZE configuration file
 * @date Oct 07, 2014
 * @author Pablo F. Alcantarilla, Jesus Nuevo
 */

#pragma once

/* ************************************************************************* */
// OpenCV
#include <opencv2/opencv.hpp>

// OpenMP
#ifdef _OPENMP
#include <omp.h>
#define OMP_MAX_THREADS 16
#endif

// System
#include <string>
#include <vector>
#include <cmath>
#include <bitset>
#include <iomanip>

/* ************************************************************************* */
/// Lookup table for 2d gaussian (sigma = 2.5) where (0,0) is top left and (6,6) is bottom right
const float gauss25[7][7] = {
  {0.02546481f,	0.02350698f,	0.01849125f,	0.01239505f,	0.00708017f,	0.00344629f,	0.00142946f},
  {0.02350698f,	0.02169968f,	0.01706957f,	0.01144208f,	0.00653582f,	0.00318132f,	0.00131956f},
  {0.01849125f,	0.01706957f,	0.01342740f,	0.00900066f,	0.00514126f,	0.00250252f,	0.00103800f},
  {0.01239505f,	0.01144208f,	0.00900066f,	0.00603332f,	0.00344629f,	0.00167749f,	0.00069579f},
  {0.00708017f,	0.00653582f,	0.00514126f,	0.00344629f,	0.00196855f,	0.00095820f,	0.00039744f},
  {0.00344629f,	0.00318132f,	0.00250252f,	0.00167749f,	0.00095820f,	0.00046640f,	0.00019346f},
  {0.00142946f,	0.00131956f,	0.00103800f,	0.00069579f,	0.00039744f,	0.00019346f,	0.00008024f}
};

/* ************************************************************************* */
/// AKAZE Descriptor Type
enum DESCRIPTOR_TYPE {
  SURF_UPRIGHT = 0, ///< Upright descriptors, not invariant to rotation
  SURF = 1,
  MSURF_UPRIGHT = 2, ///< Upright descriptors, not invariant to rotation
  MSURF = 3,
  MLDB_UPRIGHT = 4, ///< Upright descriptors, not invariant to rotation
  MLDB = 5
};

/* ************************************************************************* */
/// AKAZE Diffusivities
enum DIFFUSIVITY_TYPE {
  PM_G1 = 0,
  PM_G2 = 1,
  WEICKERT = 2,
  CHARBONNIER = 3
};

/* ************************************************************************* */
/// AKAZE Timing structure
struct AKAZETiming {

  AKAZETiming() {
    kcontrast = 0.0;
    scale = 0.0;
    derivatives = 0.0;
    detector = 0.0;
    extrema = 0.0;
    subpixel = 0.0;
    descriptor = 0.0;
  }

  double kcontrast;       ///< Contrast factor computation time in ms
  double scale;           ///< Nonlinear scale space computation time in ms
  double derivatives;     ///< Multiscale derivatives computation time in ms
  double detector;        ///< Feature detector computation time in ms
  double extrema;         ///< Scale space extrema computation time in ms
  double subpixel;        ///< Subpixel refinement computation time in ms
  double descriptor;      ///< Descriptors computation time in ms
};

/* ************************************************************************* */
/// AKAZE configuration options structure
struct AKAZEOptions {

  AKAZEOptions() {
    soffset = 1.6f;
    derivative_factor = 1.5f;
    omax = 4;
    nsublevels = 4;
    dthreshold = 0.001f;
    min_dthreshold = 0.00001f;
    target_num_features = 0;
    use_adaptive_suppression = false;

    diffusivity = PM_G2;
    descriptor = MLDB;
    descriptor_size = 0;
    descriptor_channels = 3;
    descriptor_pattern_size = 10;
    sderivatives = 1.0;

    kcontrast = 0.001f;
    kcontrast_percentile = 0.7f;
    kcontrast_nbins = 300;
    use_isotropic_diffusion = false;

    save_scale_space = false;
    save_keypoints = false;
    verbosity = false;
  }

  int omin;                       ///< Initial octave level (-1 means that the size of the input image is duplicated)
  int omax;                       ///< Maximum octave evolution of the image 2^sigma (coarsest scale sigma units)
  int nsublevels;                 ///< Default number of sublevels per scale level
  int img_width;                  ///< Width of the input image
  int img_height;                 ///< Height of the input image
  float soffset;                  ///< Base scale offset (sigma units)
  float derivative_factor;        ///< Factor for the multiscale derivatives
  float sderivatives;             ///< Smoothing factor for the derivatives
  DIFFUSIVITY_TYPE diffusivity;   ///< Diffusivity type

  float dthreshold;               ///< Detector response threshold to accept point
  float min_dthreshold;           ///< Minimum detector threshold to accept a point
  int target_num_features;        ///< Number of features to extract
  bool use_adaptive_suppression;  ///< Use adaptive suppression when selecting features

  DESCRIPTOR_TYPE descriptor;     ///< Type of descriptor
  int descriptor_size;            ///< Size of the descriptor in bits. 0->Full size
  int descriptor_channels;        ///< Number of channels in the descriptor (1, 2, 3)
  int descriptor_pattern_size;    ///< Actual patch size is 2*pattern_size*point.scale

  float kcontrast;                ///< The contrast factor parameter
  float kcontrast_percentile;     ///< Percentile level for the contrast factor
  size_t kcontrast_nbins;         ///< Number of bins for the contrast factor histogram
  bool use_isotropic_diffusion;   ///< Use isotropic diffusion instead of Perona-Malik

  bool save_scale_space;          ///< Set to true for saving the scale space images
  bool save_keypoints;            ///< Set to true for saving the detected keypoints and descriptors
  bool verbosity;                 ///< Set to true for displaying verbosity information

  friend std::ostream& operator<<(std::ostream& os,
                                  const AKAZEOptions& akaze_options) {

    os << std::left;
#define CHECK_AKAZE_OPTION(option) \
  os << std::setw(33) << #option << " =  " << option << std::endl

    // Scale-space parameters.
    CHECK_AKAZE_OPTION(akaze_options.omax);
    CHECK_AKAZE_OPTION(akaze_options.nsublevels);
    CHECK_AKAZE_OPTION(akaze_options.soffset);
    CHECK_AKAZE_OPTION(akaze_options.sderivatives);
    CHECK_AKAZE_OPTION(akaze_options.diffusivity);
    // Detection parameters.
    CHECK_AKAZE_OPTION(akaze_options.dthreshold);
    // Descriptor parameters.
    CHECK_AKAZE_OPTION(akaze_options.descriptor);
    CHECK_AKAZE_OPTION(akaze_options.descriptor_channels);
    CHECK_AKAZE_OPTION(akaze_options.descriptor_size);
    // Save scale-space
    CHECK_AKAZE_OPTION(akaze_options.save_scale_space);
    // Verbose option for debug.
    CHECK_AKAZE_OPTION(akaze_options.verbosity);
#undef CHECK_AKAZE_OPTIONS

    return os;
  }
};

/* ************************************************************************* */
/// AKAZE nonlinear diffusion filtering evolution
struct TEvolution {

  TEvolution() {
    etime = 0.0f;
    esigma = 0.0f;
    octave = 0;
    sublevel = 0;
    sigma_size = 0;
  }

  cv::Mat Lx, Ly;                   ///< First order spatial derivatives
  cv::Mat Lxx, Lxy, Lyy;            ///< Second order spatial derivatives
  cv::Mat Lflow;                    ///< Diffusivity image
  cv::Mat Lt;                       ///< Evolution image
  cv::Mat Lsmooth;                  ///< Smoothed image
  cv::Mat Lstep;                    ///< Evolution step update
  cv::Mat Ldet;                     ///< Detector response
  float etime;                      ///< Evolution time
  float esigma;                     ///< Evolution sigma. For linear diffusion t = sigma^2 / 2
  size_t octave;                    ///< Image octave
  size_t sublevel;                  ///< Image sublevel in each octave
  size_t sigma_size;                ///< Integer sigma. For computing the feature detector responses
};

