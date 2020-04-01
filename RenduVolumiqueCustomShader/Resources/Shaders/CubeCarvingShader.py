from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Cube carving shader
#------------------------------------------------------------------------------------
class CubeCarvingShader(CustomShader):

  shaderfParams = { 'boxLength' : { 'displayName' : 'Box Length',  'min' : 10.0, 'max' : 100.0, 'defaultValue' : 50. }}

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)
    self.entry = [1.0,1.0,1.0]
    self.target = [0.0,0.0,0.0]

  @classmethod
  def GetDisplayName(cls):
    return 'Cube Carving'

  def setupShader(self):
    super(CubeCarvingShader,self).setupShader()
    self.shaderUniforms.SetUniform3f("entry", self.entry)
    self.shaderUniforms.SetUniform3f("target", self.target)
    replacement = """
        vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
        vec3 dirVect = normalize(entry - target);
        vec3 orthVect1 = vec3(0.0,0.0,0.0);
        if(abs(dirVect.x) >= abs(dirVect.z) && abs(dirVect.x) >= abs(dirVect.y))
        {
          orthVect1 = cross(dirVect, vec3(0.0, 1.0, 0.0));
        }
        if(abs(dirVect.y) >= abs(dirVect.x) && abs(dirVect.y) >= abs(dirVect.z))
        {
          orthVect1 = cross(dirVect, vec3(1.0, 0.0, 0.0));
        }
        if(abs(dirVect.z) >= abs(dirVect.x) && abs(dirVect.z) >= abs(dirVect.y))
        {
          orthVect1 = cross(dirVect, vec3(1.0, 0.0, 0.0));
        }
        vec3 orthVect2 = cross(dirVect, orthVect1);
        g_skip =  abs(dot(texCoordRAS.xyz - entry, dirVect)) <= boxLength/2.0 && abs(dot(texCoordRAS.xyz - entry, normalize(orthVect1))) <= boxLength/2.0 && abs(dot(texCoordRAS.xyz - entry, normalize(orthVect2))) <= boxLength/2.0;
    """
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Impl", True, replacement, False)

  def setPathEnds(self,entry,target):
    self.shaderUniforms.SetUniform3f("entry", entry)
    self.shaderUniforms.SetUniform3f("target", target)