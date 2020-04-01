from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Drill-core shader
#------------------------------------------------------------------------------------
class DrillCoreShader(CustomShader):

  shaderfParams = { 'radius' : { 'displayName' : 'Radius', 'min' : 0.0, 'max' : 100.0, 'defaultValue' : 20. }}

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)
    self.entry = [0.0,0.0,0.0]
    self.target = [0.0,0.0,0.0]

  @classmethod
  def GetDisplayName(cls):
    return 'Drill-core'

  def setupShader(self):
    super(DrillCoreShader,self).setupShader()
    self.shaderUniforms.SetUniform3f("entry", self.entry)
    self.shaderUniforms.SetUniform3f("target", self.target)
    replacement = """
      vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
      vec3 dirVect = entry - target;
      float constVal = radius * length(dirVect);
      g_skip =  dot(texCoordRAS.xyz - target, dirVect) > 0. && dot(texCoordRAS.xyz - entry, dirVect) < 0. && length(cross(texCoordRAS.xyz - target, dirVect)) < constVal;
    """
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Impl", True, replacement, False)

  def setPathEnds(self,entry,target):
    self.shaderUniforms.SetUniform3f("entry", entry)
    self.shaderUniforms.SetUniform3f("target", target)