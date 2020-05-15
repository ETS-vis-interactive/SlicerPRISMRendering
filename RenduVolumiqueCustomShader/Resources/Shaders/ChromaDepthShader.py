from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Chroma depth shader
#------------------------------------------------------------------------------------
class ChromaDepthShader(CustomShader):
  shaderfParams = { 'depthMinRange' : { 'displayName' : 'Depth Min Range', 'min' : -100, 'max' : 10, 'defaultValue' : -80 }, \
                   'depthMaxRange' : { 'displayName' : 'Depth Max Range', 'min' : -100, 'max' : 140, 'defaultValue' : 100 }, \
   }
                   

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Chroma Depth Perception'

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
    float depthRangeInTexCoordStart = (ip_inverseTextureDataAdjusted * vec4(0,0,depthMinRange,1.0) ).z;
    float depthRangeInTexCoordEnd = (ip_inverseTextureDataAdjusted * vec4(0,0,depthMaxRange,1.0) ).z;
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