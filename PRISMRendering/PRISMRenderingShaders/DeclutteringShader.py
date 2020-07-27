from PRISMRenderingShaders.CustomShader import CustomShader

"""ChromaDepthShader Class containing the code for the Chroma Depth shader.

:param CustomShader:  Parent class containing the function to access the parameters of the shader. 
:type CustomShader: class.
""" 
class DeclutteringShader(CustomShader):

  shaderfParams = {}
  shaderiParams = {}
  shader4fParams = {}
  shaderbParams = {}
  shaderrParams = {}
  shadertfParams = {}
  shadervParams = { 'distancetoAVM' : { 'displayName' : 'Distance to AVM', 'defaultVolume' : 1, 'transferFunctions' : \
  { 'scalarColorMapping' : { 'displayName' : 'Scalar Color Mapping', 'defaultColors' : [], 'type' : 'color'},\
   'scalarOpacityMapping' : { 'displayName' : 'Scalar Opacity Mapping', 'defaultColors' : [], 'type' : 'scalarOpacity'}}}}
  
  def __init__(self, shaderPropertyNode, volumeNode = None):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Decluttering'

  def setupShader(self):
    super(DeclutteringShader,self).setupShader()
    shadingImplCode = """
    if (!g_skip)      
    {      
      vec4 scalar = texture3D(in_volume[0], g_dataPos);        
      scalar.r = scalar.r * in_volume_scale[0].r + in_volume_bias[0].r;        
      scalar = vec4(scalar.r);             
      if (in_noOfComponents > 1)
      {
        vec4 sample = texture3D(in_volume[1], g_dataPos);        
        scalar *= sample;
        g_srcColor = vec4(0.0);             
        g_srcColor.a = computeOpacity(scalar);             
        if (g_srcColor.a > 0.0)             
          {             
            g_srcColor = computeColor(scalar, g_srcColor.a);           
            g_srcColor.rgb *= g_srcColor.a;           
            g_fragColor = (1.0f - g_fragColor.a) * g_srcColor + g_fragColor;             
          }  
      }    
    }

  """

    self.shaderProperty.ClearAllFragmentShaderReplacements()
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Shading::Impl", True, shadingImplCode, False)
    #shaderreplacement
