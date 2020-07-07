from Resources.CustomShader import CustomShader

"""!@class ChromaDepthShader
@brief Class containing the code for the Chroma Depth shader.
@param CustomShader class : Parent class containing the function to access the parameters of the shader.
""" 
class Decluttering(CustomShader):

  shaderfParams = {}
  shaderiParams = {}
  shader4fParams = {}
  shaderbParams = {}
  shaderrParams = {}
  shadertfParams = {}
  shadervParams = { 'distancetoAVM' : { 'displayName' : 'Distance to AVM', 'defaultVolume' : 1, 'transferFunctions' : \
  { 'scalarColorMapping2' : { 'displayName' : 'Scalar Color Mapping second', 'defaultColors' : [[0, 0, 1, 0, 0, 0.5], [300, 1, 0, 0, 0, 0.5]], 'type' : 'color'},\
   'scalarOpacityMapping2' : { 'displayName' : 'Scalar Opacity Mapping second', 'defaultColors' : [], 'type' : 'scalarOpacity'}}}}
  
  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Decluttering'

  def setupShader(self):
    super(Decluttering,self).setupShader()
    shadingImplCode = """
    if (!g_skip)      
    {      
      vec4 scalar = texture3D(in_volume[0], g_dataPos);        
      scalar.r = scalar.r * in_volume_scale[0].r + in_volume_bias[0].r;        
      scalar = vec4(scalar.r);             
      g_srcColor = vec4(0.0);             
      g_srcColor.a = computeOpacity(scalar);             
      if (g_srcColor.a > 0.0)             
        {             
          g_srcColor = computeColor(scalar, g_srcColor.a);           
          g_srcColor.rgb *= g_srcColor.a;           
          g_fragColor = (1.0f - g_fragColor.a) * g_srcColor + g_fragColor;             
        }      
      }
    g_srcColor = vec4(1.0);
    if (in_noOfComponents > 0)
    {
      g_srcColor = vec4(0.0);
      vec4 sample = texture3D(in_volume[2], g_dataPos);        
    }

  """

    self.shaderProperty.ClearAllFragmentShaderReplacements()
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Shading::Impl", True, shadingImplCode, False)
    #shaderreplacement
