cmake_minimum_required(VERSION 3.5)

project(RenduVolumiqueCustomShader)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/RenduVolumiqueCustomShader")
set(EXTENSION_CATEGORY "Projet")
set(EXTENSION_CONTRIBUTORS "Tiphaine RICHARD (ETS)")
set(EXTENSION_DESCRIPTION "This is a scripted module to edit custom volume rendering shaders")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/RenduVolumiqueCustomShader.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/RenduVolumiqueCustomShader/Screenshots/1.png")
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
