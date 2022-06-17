cmake_minimum_required(VERSION 3.13.4)

project(SlicerPRISMRendering)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://githubcomets-vis-interactiveslicerprismrendering.readthedocs.io/")
set(EXTENSION_CATEGORY "Rendering")
set(EXTENSION_CONTRIBUTORS "Tiphaine Richard (ETS), Simon Drouin (ETS)")
set(EXTENSION_DESCRIPTION "This module is an implementation of the PRISM customizable volume rendering framework in 3D Slicer.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/PRISMRendering/Resources/Icons/PRISMRendering.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/screenshotSlicerPRISMRendering.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(PRISMRendering)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
