from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Opacity peeling shader
#------------------------------------------------------------------------------------
class OpacityPeelingShader(CustomShader):

  shaderfParams = {'T_low' : { 'displayName' : 'Low Threshold', 'min' : 0.0, 'max' : 1.0, 'defaultValue' : 0.3 }, \
                   'T_high' : { 'displayName' : 'High Threshold', 'min' : 0.01, 'max' : 1.0, 'defaultValue' : 0.8 }, \
                   'radius' : { 'displayName' : 'Sphere Radius', 'min' : 0.0, 'max' : 150.0, 'defaultValue' : 75.0 }}
                   
  shaderiParams = {'wantedLayer' : { 'displayName' : 'Wanted Layer', 'min' : 1.0, 'max' : 20.0, 'defaultValue' : 1.0 }}

  shaderbParams = { 'sphere' : { 'displayName' : 'Sphere Carving', 'defaultValue' : 0}}
  
  shader4fParams = {'centerPoint': {'displayName': 'Center', 'defaultValue': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0}}}

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Opacity Peeling'

  def setupShader(self):
    super(OpacityPeelingShader,self).setupShader()
    self.setAllUniforms()
    self.shaderProperty.ClearAllFragmentShaderReplacements()


    croppingDecCode = """
    int currentLayer = 0;
    float layerAlpha = 0.0;"""

    shadingImplCode = """
    if (!g_skip)
    {
      vec3 center = centerPoint.xyz;
      // Get alpha for current pos according to transfer function
      vec4 scalar = texture3D(in_volume[0], g_dataPos);
      scalar.r = scalar.r * in_volume_scale[0].r + in_volume_bias[0].r;
      scalar = vec4(scalar.r);
      g_srcColor = vec4(0.0);
      g_srcColor.a = computeOpacity(scalar);
      
      // Determine if the current position is within the spherical ROI
      vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
      bool isInROI = length(texCoordRAS.xyz - center) < radius;
      
      if((sphere == 1 && isInROI || sphere == 0) && currentLayer < wantedLayer)
      {
        layerAlpha = layerAlpha + ( 1.0 - layerAlpha ) * g_srcColor.a;
        if( layerAlpha > T_high && g_srcColor.a < T_low )
        {
          currentLayer = currentLayer + 1;
          layerAlpha = 0.0;
        }
      }

      else if (g_srcColor.a > 0.0)
      {
        g_srcColor = computeColor(scalar, g_srcColor.a);
        g_srcColor.rgb *= g_srcColor.a;
        g_fragColor = (1.0f - g_fragColor.a) * g_srcColor + g_fragColor;
      }
    }"""

    self.shaderProperty.ClearAllFragmentShaderReplacements()
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Dec", True, croppingDecCode, False)
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Shading::Impl", True, shadingImplCode, False)
