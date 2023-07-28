from PRISMRenderingShaders.CustomShader import CustomShader
from PRISMRenderingParams import *
import vtk, qt, ctk, slicer
import logging

class EchoVolumeShader(CustomShader):

  threshold = FloatParam('threshold', 'Threshold', 20.0, 0.0, 100.0)
  edgeSmoothing = FloatParam('edgeSmoothing', 'Edge Smoothing', 5.0, 0.0, 20.0)
  depthRange = RangeParam('depthRange', 'Depth Range', [-150.0, 150.0], [-120.0, 10.0])
  depthDarkening = IntParam('depthDarkening', 'Depth Darkening', 30, 0, 100)
  depthColoringRange = RangeParam('depthColoringRange', 'Depth Coloring Range', [-50, 50], [-24, 23])
  brightnessScale = FloatParam('brightnessScale', 'Brightness Scale', 120.0, 0.0, 200.0)
  saturationScale = FloatParam('saturationScale', 'Saturation Scale', 120.0, 0.0, 200.0)

  param_list = [threshold, edgeSmoothing, depthRange, depthDarkening, depthColoringRange, brightnessScale, saturationScale]

  def __init__(self, shaderPropertyNode, volumeNode = None, logic = None, paramlist = param_list):
    CustomShader.__init__(self, shaderPropertyNode, volumeNode)
    self.param_list = paramlist

    self.update_param_list = [self.threshold, self.edgeSmoothing]

    for p in self.param_list:
      if p in self.update_param_list:
        p.addCustomShaderUpdater(self)
    
    self.createMarkupsNodeIfNecessary(logic)

    self.volumeRenderingDisplayNode = self._setupVolumeRenderingDisplayNode(self.volumeNode)

    self.getBaseVolumeProperty()

  @classmethod
  def GetDisplayName(cls):
    return 'Echo Volume Renderer'
  
  @classmethod
  def GetBasicDescription(cls):
    """Function to get a basic description of the current shader.
    
    :return: Description of the current shader.
    :rtype: str
    """
    return 'Use custom shaders for depth-dependent coloring for volume rendering of 3D/4D ultrasound images.'

  def setupShader(self):

    super(EchoVolumeShader, self).setupShader()

    ComputeColorReplacementCommon = """

vec3 rgb2hsv(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

uniform sampler2D in_colorTransferFunc_0[1];

vec4 computeColor(vec4 scalar, float opacity)
{
    // Get base color from color transfer function (defines darkening of transparent voxels and neutral color)

    vec3 baseColorRgb = texture2D(in_colorTransferFunc_0[0], vec2(scalar.w, 0.0)).xyz;
    vec3 baseColorHsv = rgb2hsv(baseColorRgb);

    // Modulate hue and brightness depending on distance

    float hueFar = clamp(baseColorHsv.x-depthColoringRangeMin*0.01, 0.0, 1.0);
    float hueNear = clamp(baseColorHsv.x-depthColoringRangeMax*0.01, 0.0, 1.0);
    float sat = clamp(saturationScale*0.01*baseColorHsv.y,0.0,1.0);
    float brightnessNear = brightnessScale*0.01*baseColorHsv.z;
    float brightnessFar = clamp(brightnessScale*0.01*(baseColorHsv.z-depthDarkening*0.01), 0.0, 1.0);

    // Determine the ratio (dist) that serves to interpolate between the near
    // color and the far color. depthRange specifies the depth range, in voxel
    // coordinates, between the front color and back color.
    vec3 camInTexCoord = (ip_inverseTextureDataAdjusted * vec4(g_eyePosObj.xyz,1.0) ).xyz;
    float depthRangeInTexCoordStart = (ip_inverseTextureDataAdjusted * vec4(0,0,depthRangeMin,1.0) ).z;
    float depthRangeInTexCoordEnd = (ip_inverseTextureDataAdjusted * vec4(0,0,depthRangeMax,1.0) ).z;
    vec3 dp = g_dataPos - camInTexCoord;
    vec3 dv = vec3(0.5,0.5,0.5) - camInTexCoord;
    float lv = length(dv);
    float lp = dot(dp, dv) / lv;
    float dist = (lp - lv - depthRangeInTexCoordStart) / ( depthRangeInTexCoordEnd - depthRangeInTexCoordStart);
    dist = clamp( dist, 0.0, 1.0 );

    vec3 rgbNear = hsv2rgb(vec3( hueNear, sat, brightnessNear));
    vec3 rgbFar = hsv2rgb(vec3( hueFar, sat, brightnessFar));
    vec3 rgbDepthModulated = mix( rgbNear, rgbFar, dist );

    vec4 color = vec4(rgbDepthModulated, opacity);
"""

    ComputeColorReplacementVTK8 = ComputeColorReplacementCommon + """
    return computeLighting(color, 0);
}
"""

    ComputeColorReplacementVTK9 = ComputeColorReplacementCommon + """
    return computeLighting(color, 0, 0.0);
}
"""
    sp = self.shaderPropertyNode.GetShaderProperty()
    sp.ClearAllShaderReplacements()
    computeColorReplacement = ComputeColorReplacementVTK9 if vtk.vtkVersion().GetVTKMajorVersion() >= 9 else ComputeColorReplacementVTK8
    sp.AddShaderReplacement(vtk.vtkShader.Fragment, "//VTK::ComputeColor::Dec", True, computeColorReplacement, True)
    #shaderreplacement
    self.updateVolumeProperty()
    
  def updateVolumeProperty(self):

    if not self.volumeRenderingDisplayNode:
      return

    # retrieve scalar opacity transfer function
    volPropNode = self.volumeRenderingDisplayNode.GetVolumePropertyNode()
    if not volPropNode:
      volPropNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLVolumePropertyNode")
      self.volumeRenderingDisplayNode.SetAndObserveVolumePropertyNodeID(volPropNode.GetID())
    disableModify = volPropNode.StartModify()

    # Set up lighting/material
    volPropNode.GetVolumeProperty().ShadeOn()
    #volPropNode.GetVolumeProperty().SetAmbient(0.5)
    #volPropNode.GetVolumeProperty().SetDiffuse(0.5)
    #volPropNode.GetVolumeProperty().SetSpecular(0.5)
    volPropNode.GetVolumeProperty().SetAmbient(0.1)
    volPropNode.GetVolumeProperty().SetDiffuse(0.9)
    volPropNode.GetVolumeProperty().SetSpecular(0.2)
    volPropNode.GetVolumeProperty().SetSpecularPower(10)

    slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLViewNode").SetVolumeRenderingSurfaceSmoothing(True)

    # compute parameters of the piecewise opacity function
    #volRange = self.getCurrentVolumeNode().GetImageData().GetScalarRange()
    volRange = [0,255] # set fixed range so that absolute threshold value does not change as we switch volumes

    eps = 1e-3  # to make sure rampeStart<rampEnd
    volRangeWidth = ( volRange[1] - volRange[0] )
    edgeSmoothing = max(eps, self.edgeSmoothing.value)

    rampCenter = volRange[0] + self.threshold.value * 0.01 * volRangeWidth
    rampStart = rampCenter - edgeSmoothing * 0.01 * volRangeWidth
    rampEnd = rampCenter + edgeSmoothing * 0.01 * volRangeWidth

    # build opacity function
    scalarOpacity = vtk.vtkPiecewiseFunction()
    scalarOpacity.AddPoint(min(volRange[0],rampStart),0.0)
    scalarOpacity.AddPoint(rampStart,0.0)
    scalarOpacity.AddPoint(rampCenter,0.2)
    scalarOpacity.AddPoint(rampCenter+eps,0.8)
    scalarOpacity.AddPoint(rampEnd,0.95)
    scalarOpacity.AddPoint(max(volRange[1],rampEnd),0.95)

    # build color transfer function
    darkBrown = [84.0/255.0, 51.0/255.0, 42.0/255.0]
    green = [0.5, 1.0, 0.5]
    colorTransferFunction = vtk.vtkColorTransferFunction()
    colorTransferFunction.AddRGBPoint(min(volRange[0],rampStart), 0.0, 0.0, 0.0)
    colorTransferFunction.AddRGBPoint((rampStart+rampCenter)/2.0, *darkBrown)
    colorTransferFunction.AddRGBPoint(rampCenter, *green)
    colorTransferFunction.AddRGBPoint(rampEnd, *green)
    colorTransferFunction.AddRGBPoint(max(volRange[1],rampEnd), *green)
    
    volPropNode.GetVolumeProperty().SetScalarOpacity(scalarOpacity)
    volPropNode.GetVolumeProperty().SetColor(colorTransferFunction) 

    volPropNode.EndModify(disableModify)
    volPropNode.Modified()
  
  def getBaseVolumeProperty(self):

    volPropNode = self.volumeRenderingDisplayNode.GetVolumePropertyNode()

    self.ambient = volPropNode.GetVolumeProperty().GetAmbient()
    self.diffuse = volPropNode.GetVolumeProperty().GetDiffuse()
    self.specular = volPropNode.GetVolumeProperty().GetSpecular()
    self.specularPower = volPropNode.GetVolumeProperty().GetSpecularPower()

  def resetVolumeProperty(self):

    volPropNode = self.volumeRenderingDisplayNode.GetVolumePropertyNode()

    disableModify = volPropNode.StartModify()

    volPropNode.GetVolumeProperty().ShadeOff()

    slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLViewNode").SetVolumeRenderingSurfaceSmoothing(False)

    volPropNode.GetVolumeProperty().SetAmbient(self.ambient)
    volPropNode.GetVolumeProperty().SetDiffuse(self.diffuse)
    volPropNode.GetVolumeProperty().SetSpecular(self.specular)
    volPropNode.GetVolumeProperty().SetSpecularPower(self.specularPower)
    # volPropNode.GetVolumeProperty().GetScalarOpacity().DeepCopy(vtk.vtkPiecewiseFunction())
    # volPropNode.GetVolumeProperty().GetRGBTransferFunction().DeepCopy(vtk.vtkColorTransferFunction()) 

    volPropNode.EndModify(disableModify)
    volPropNode.Modified()
    
  def inputVolumeNode(self):
    return self._setupVolumeRenderingDisplayNode(self.volumeNode)
  
  def hasImageData(self, volumeNode):
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def _setupVolumeRenderingDisplayNode(self, volumeNode):
    """Sets up volume rendering display node and associated property and ROI nodes.
    If the nodes already exist and valid then nothing is changed.
    :param volumeNode: input volume node
    :return: volume rendering display node
    """
    
    # Make sure the volume node has image data
    if self.hasImageData(volumeNode) == False:
      return None

    # Make sure the volume node has a volume rendering display node
    volRenLogic = slicer.modules.volumerendering.logic()
    volumeRenderingDisplayNode = volRenLogic.GetFirstVolumeRenderingDisplayNode(volumeNode)
    if not volumeRenderingDisplayNode:
      volumeRenderingDisplayNode = volRenLogic.CreateDefaultVolumeRenderingNodes(volumeNode)

    # Make sure GPU volume rendering is used
    if not volumeRenderingDisplayNode.IsA("vtkMRMLGPURayCastVolumeRenderingDisplayNode"):
      gpuVolumeRenderingDisplayNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLGPURayCastVolumeRenderingDisplayNode")
      roiNode = volumeRenderingDisplayNode.GetROINodeID()
      gpuVolumeRenderingDisplayNode.SetAndObserveROINodeID(roiNode)
      gpuVolumeRenderingDisplayNode.SetAndObserveVolumePropertyNodeID(volumeRenderingDisplayNode.GetVolumePropertyNodeID())
      gpuVolumeRenderingDisplayNode.SetAndObserveShaderPropertyNodeID(volumeRenderingDisplayNode.GetShaderPropertyNodeID())
      gpuVolumeRenderingDisplayNode.SetCroppingEnabled(volumeRenderingDisplayNode.GetCroppingEnabled())
      gpuVolumeRenderingDisplayNode.SetThreshold(volumeRenderingDisplayNode.GetThreshold())
      gpuVolumeRenderingDisplayNode.SetWindowLevel(volumeRenderingDisplayNode.GetWindowLevel())
      gpuVolumeRenderingDisplayNode.SetFollowVolumeDisplayNode(volumeRenderingDisplayNode.GetFollowVolumeDisplayNode())
      gpuVolumeRenderingDisplayNode.SetIgnoreVolumeDisplayNodeThreshold(volumeRenderingDisplayNode.GetIgnoreVolumeDisplayNodeThreshold())
      gpuVolumeRenderingDisplayNode.SetUseSingleVolumeProperty(volumeRenderingDisplayNode.GetUseSingleVolumeProperty())
      slicer.modules.volumerendering.logic().UpdateDisplayNodeFromVolumeNode(gpuVolumeRenderingDisplayNode, volumeNode)
      slicer.mrmlScene.RemoveNode(volumeRenderingDisplayNode)
      volumeRenderingDisplayNode = gpuVolumeRenderingDisplayNode

    # Keep only first volume rendering display node, delete all the others
    displayNodes = []
    for displayNodeIndex in range(volumeNode.GetNumberOfDisplayNodes()):
      displayNodes.append(volumeNode.GetNthDisplayNode(displayNodeIndex))
    alreadyAdded = False
    for displayNode in displayNodes:
      if not displayNode.IsA("vtkMRMLVolumeRenderingDisplayNode"):
        continue
      if displayNode == volumeRenderingDisplayNode:
        alreadyAdded = True
        continue
      slicer.mrmlScene.RemoveNode(displayNode)

    # Make sure markups ROI node is used (if Slicer is recent enough)
    if vtk.vtkVersion().GetVTKMajorVersion() >= 9:
      if not volumeRenderingDisplayNode.GetMarkupsROINode():
        markupsRoiNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsROINode', volumeNode.GetName()+' ROI')
        markupsRoiNode.CreateDefaultDisplayNodes()
        markupsRoiNode.GetDisplayNode().SetVisibility(False)
        markupsRoiNode.GetDisplayNode().SetPropertiesLabelVisibility(False)
        markupsRoiNode.GetDisplayNode().SetRotationHandleVisibility(True)
        markupsRoiNode.GetDisplayNode().SetTranslationHandleVisibility(True)
        annotationRoiNode = volumeRenderingDisplayNode.GetROINode()
        volumeRenderingDisplayNode.SetAndObserveROINodeID(markupsRoiNode.GetID())
        if annotationRoiNode:
          roiCenter = [0.0, 0.0, 0.0]
          roiRadius = [1.0, 1.0, 1.0]
          annotationRoiNode.GetXYZ(roiCenter)
          annotationRoiNode.GetRadiusXYZ(roiRadius)
          markupsRoiNode.SetXYZ(roiCenter)
          markupsRoiNode.SetRadiusXYZ(roiRadius)
          slicer.mrmlScene.RemoveNode(annotationRoiNode)
        else:
          slicer.modules.volumerendering.logic().FitROIToVolume(volumeRenderingDisplayNode)

    shaderPropertyNode = volumeRenderingDisplayNode.GetOrCreateShaderPropertyNode(slicer.mrmlScene)
    sp = shaderPropertyNode.GetShaderProperty()
    sp.ClearAllShaderReplacements()

    return volumeRenderingDisplayNode

  def onParamUpdater(self):
    self.updateVolumeProperty()