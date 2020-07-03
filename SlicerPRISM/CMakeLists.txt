cmake_minimum_required(VERSION 3.5)

project(SlicerPRISM)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://ets-vis-interactive.github.io/SlicerPRISM/")
set(EXTENSION_CATEGORY "Rendering")
set(EXTENSION_CONTRIBUTORS "Tiphaine RICHARD (ETS)")
set(EXTENSION_DESCRIPTION "This module is an implementation of the PRISM customizable volume rendering framework in 3D Slicer.")
set(EXTENSION_ICONURL "https://github.com/ETS-vis-interactive/SlicerPRISM/blob/master/docs/images/logoSlicerPRISM.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/ETS-vis-interactive/SlicerPRISM/blob/master/docs/images/screenshotSlicerPRISM.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
