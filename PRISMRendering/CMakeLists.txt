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
  PRISMRenderingShaders/DeclutteringShader.py
  PRISMRenderingShaders/OpacityPeelingShader.py
  PRISMRenderingShaders/OutlineShader.py
  PRISMRenderingShaders/PlaneIntersectingShader.py
  PRISMRenderingShaders/SphereCarvingShader.py
  # PRISMRenderingShaders/Template  TODO: template must be moved to MODULE_PYTHON_RESOURCES
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/UI/PRISMRendering.ui
  Resources/shaderTags.json
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
