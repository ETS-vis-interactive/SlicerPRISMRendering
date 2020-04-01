from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Double Plane shader
#------------------------------------------------------------------------------------
class DoublePlaneShader(CustomShader):

  shaderfParams = { 'relativePosition' : { 'displayName' : 'Relative Position', 'min' : 0.0, 'max' : 1.0, 'defaultValue' : 0.5 }}

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Double Plane'

  def setupShader(self):
    super(DoublePlaneShader,self).setupShader()
    self.shaderUniforms.SetUniform3f("entry", [0.0,0.0,1.0])
    self.shaderUniforms.SetUniform3f("target", [0.0,0.0,0.0])
    replacement = """
      vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
      vec3 dirVect = normalize(entry - target);

      bool skipAlongAxis = dot(texCoordRAS.xyz - entry, dirVect) + length(entry - target) * relativePosition > 0;

      vec3 vPlaneN = cross( vec3(0.0,0.0,1.0), dirVect );
      float dirCoord = dot(texCoordRAS.xyz - entry, vPlaneN);
      float dirCam = dot(in_cameraPos - entry, vPlaneN);
      bool skipVertical = dirCoord * dirCam > 0.0;

      g_skip = skipAlongAxis && skipVertical;
    """
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Impl", True, replacement, False)

  def setPathEnds(self,entry,target):
    self.shaderUniforms.SetUniform3f("entry", entry)
    self.shaderUniforms.SetUniform3f("target", target)