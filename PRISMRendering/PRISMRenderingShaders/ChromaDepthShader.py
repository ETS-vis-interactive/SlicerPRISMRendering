from PRISMRenderingShaders.CustomShader import CustomShader
import math  
import vtk, qt, ctk, slicer

"""!@class ChromaDepthShader
@brief Class containing the code for the Chroma Depth shader.
@param CustomShader class : Parent class containing the function to access the parameters of the shader.
""" 
class ChromaDepthShader(CustomShader):
  shaderrParams = { 'depthRange' : { 'displayName' : 'Depth Range', 'defaultValue' : [0.0, 1.0]}}
  shadertfParams = { 'scalarColorMapping' : { 'displayName' : 'Scalar Color Mapping', 'defaultColors' : [[0, 1, 0, 0, 0, 0.5], [300, 0, 0, 1, 0, 0.5]], 'type' : 'color'}}
  
  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self, shaderPropertyNode)
    volumeRange = self.getVolumeRange()
    if volumeRange :
      self.shaderrParams['depthRange']['defaultValue'][0] = -1* volumeRange
      self.shaderrParams['depthRange']['defaultValue'][1] = volumeRange

  @classmethod
  def GetDisplayName(cls):
    return 'Chroma Depth Perception'

  def getVolumeRange(self):
    """Function to get the range of the current volume.

    @return Range float : Range of the current volume.
    """
    imageSelectorNode = slicer.modules.PRISMRenderingWidget.ui.imageSelector.currentNode()
    if imageSelectorNode != None :
      volumeNode = imageSelectorNode.GetVolumeDisplayNode().GetVolumeNode()
      dim = [0, 0, 0]
      volumeNode.GetImageData().GetDimensions(dim)
      return math.sqrt(dim[0]**2 + dim[1]**2 + dim[2]**2)/2

  def setupShader(self):
    super(ChromaDepthShader,self).setupShader()
    self.shaderProperty.ClearAllFragmentShaderReplacements()

    ComputeColorReplacement = """
  uniform sampler2D in_colorTransferFunc_0[1];
  vec4 computeColor(vec4 scalar, float opacity)
  {
      // Determine the ratio (dist) that serves to interpolate between the near
      // color and the far color. depthRange specifies the depth range, in voxel
      // coordinates, between the front color and back color.
      vec3 camInTexCoord = (ip_inverseTextureDataAdjusted * vec4(g_eyePosObj.xyz,1.0) ).xyz;
      // ramnère les distance de slicer au système de coordonnée de la texture 3D
      float depthRangeInTexCoordStart = (ip_inverseTextureDataAdjusted * vec4(0, 0, depthRangeMin, 1.0) ).z;
      float depthRangeInTexCoordEnd = (ip_inverseTextureDataAdjusted * vec4(0, 0, depthRangeMax, 1.0) ).z;
      vec3 dp = g_dataPos - camInTexCoord;
      vec3 dv = vec3(0.5,0.5,0.5) - camInTexCoord;
      float lv = length(dv);
      float lp = dot(dp, dv) / lv;
      float range = depthRangeInTexCoordEnd - depthRangeInTexCoordStart;
      float dist = (lp - lv - depthRangeInTexCoordStart) / range;
      dist = clamp( dist, 0.0, 1.0 );
      vec4 c = texture2D(in_colorTransferFunc_0[0], vec2(dist));
      return computeLighting(c, 0);
  }
  """
    self.shaderProperty.ClearAllFragmentShaderReplacements()
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::ComputeColor::Dec", True, ComputeColorReplacement,True)
