from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Plane intersecting shader
#------------------------------------------------------------------------------------
class PlaneIntersectingShader(CustomShader):

  shaderParams = { 'relativePosition' : { 'displayName' : 'Relative Position', 'min' : 0.0, 'max' : 1.0, 'defaultValue' : 0.5 }}
  
  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)
    self.entry = [0.0,0.0,0.0]
    self.target = [0.0,0.0,0.0]

  @classmethod
  def GetDisplayName(cls):
    return 'Plane intersecting'

  def setupShader(self):
    super(PlaneIntersectingShader,self).setupShader()
    self.shaderUniforms.SetUniform3f("entry", self.entry)
    self.shaderUniforms.SetUniform3f("target", self.target)
    replacement = """
      vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
      vec3 dirVect = normalize(entry - target);
      g_skip =  dot(texCoordRAS.xyz - entry, dirVect) + length(entry - target) * relativePosition > 0;
    """
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Impl", True, replacement, False)

  def setPathEnds(self,entry,target):
    self.shaderUniforms.SetUniform3f("entry", entry)
    self.shaderUniforms.SetUniform3f("target", target)