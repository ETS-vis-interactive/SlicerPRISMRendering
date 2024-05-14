#-----------------------------------------------------------------------------
set(MODULE_NAME PRISMRendering)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  PRISMRenderingLogic/__init__.py
  PRISMRenderingLogic/PRISMRenderingLogic.py
  PRISMRenderingShaders/__init__.py
  PRISMRenderingShaders/ChromaDepthShader.py
  PRISMRenderingShaders/CustomShader.py
  PRISMRenderingShaders/OpacityPeelingShader.py
  PRISMRenderingShaders/OutlineShader.py
  PRISMRenderingShaders/PlaneIntersectingShader.py
  PRISMRenderingShaders/SphereCarvingShader.py
  PRISMRenderingParams/__init__.py
  PRISMRenderingParams/FloatParam.py
  PRISMRenderingParams/IntParam.py
  PRISMRenderingParams/Param.py
  PRISMRenderingParams/BoolParam.py
  PRISMRenderingParams/TransferFunctionParam.py
  PRISMRenderingParams/RangeParam.py
  PRISMRenderingParams/FourFParam.py
  PRISMRenderingPoints/__init__.py
  PRISMRenderingPoints/CustomShaderPoints.py
  PRISMRenderingVolumes/__init__.py
  PRISMRenderingVolumes/PRISMRenderingVolume.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/UI/${MODULE_NAME}.ui
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
