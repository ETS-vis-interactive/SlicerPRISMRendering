# SlicerPRISM
1. [ Introduction and Acknowledgements. ](#intro)
2. [ Module Description. ](#desc)
3. [ Use Cases. ](#usec)
4. [ Tutorials. ](#tutos)
5. [ Panels and their use. ](#panels)
6. [ Similar Modules. ](#similar)
7. [ References. ](#ref)
8. [ Information for Developers. ](#info)

	* [ Limitations. ](#lim)
	* [ Key nodes and classes. ](#key)
	* [ How Tos. ](#howto)

<a name="intro"></a>
## Introduction and Acknowledgements
**Title**: SlicerPRISM

**Author(s)/Contributor(s)**: Simon Drouin, Professor at École de technologie supérieure (ÉTS), Montréal, Tiphaine RICHARD, Student Intern at ÉTS.

**License**: slicer4

**Acknowledgements**: 

**Contact**: Tiphaine RICHARD, tiphainejh@gmail.com

<a name="desc"></a>
## Module Description
This module is an implementation of the PRISM customizable volume rendering framework in 3D Slicer.

<a name="usec"></a>
## Use Cases

<a name="tutos"></a>
## Tutorials

<a name="panels"></a>
## Panels and their use

<table>
    <tr style="white-space:nowrap;">
        <td style="white-space:nowrap;">
            <ul> 
                <li><b>Data</b> : Contains the volume required for SlicerPRISM. </li>
                <ul>
                    <li><b>Image Volume</b> : Select the current volume to render. </li>
                </ul>
            </ul>
        </td>
        <td>
            <img src="/SlicerPRISM/Resources/Documentation/Data.png" alt="Data" width ="50%" title="Data"/>
        </td>
    </tr>
    <tr style="white-space:nowrap;">
        <td style="white-space:nowrap;">
            <ul> 
                <li> <b>View Setup</b> : Contains the controls for rendering the volume as well as controls for the cropping box (ROI) of the volume. </li>
                <ul>
                    <li><b>Volume Rendering</b> : Enable/Disable rendering the volume.</li>
                    <li><b>Enable Cropping</b> : Enable/Disable cropping the volume.</li>
                    <li><b>Display ROI</b> : Enable/Disable displaying the ROI of the volume.</li>
                    <li><b>Enable Scaling</b> : Enable/Disable scaling the ROI of the volume.</li>
                    <li><b>Enable Rotation</b> : Enable/Disable rotating the ROI of the volume.</li>
                </ul>
            </ul>
        </td>
        <td style="white-space:nowrap;">
            <img src="/SlicerPRISM/Resources/Documentation/ViewSetup.png" alt="ViewSetup" width ="50%" title="ViewSetup"/>
        </td>
    </tr>
    <tr style="white-space:nowrap;">
        <td style="white-space:nowrap;">
            <ul> 
                <li><b>Custom Shader</b> : Controls of the shader.</li>
                <ul>
                    <li><b>Custom Shader</b> : Name of the shader to be applied during the rendering.</li>
                    <li><b>Reload</b> : Reload the current shader.</li>
                    <li><b>Open</b> : Open the current shader source code.</li>
                    <li><b>Duplicate</b> : Duplicate the current shader source code.</li>
                </ul>
            </ul>
        </td>
        <td style="white-space:nowrap;">
            <img src="/SlicerPRISM/Resources/Documentation/CustomShader.png" alt="CustomShader" width ="50%" title="CustomShader"/>
        </td>
    </tr>
    <tr style="white-space:nowrap;">
        <td rowspan=3 style="white-space:nowrap;">
            <ul> 
                <li><b>Modify or Create Custom Shader</b> : Create or Modify a custom shader and add parameters.</li>
                <ul>
                    <li><b>Shader</b> : Name of the shader to modify or <i>Create new Custom Shader</i> to create a new one.</li>
                    <li><b>Class Name</b> : Name of the class that will be created.</li>
                    <li><b>Display Name</b> : Name of the shader that will be displayed in the UI.</li>
                    <li><b>Create</b> : Create the class.</li>
                    <li><b>Add Code</b> : Add a code that will replace a specific shader tag in the shader.</li>
                    <ul>
                        <li><b>Tag Type</b> : Type of the tag to be remplaced in the shader.</li>
                        <li><b>Shader Tag</b>: Tag to be remplaced in the shader.</li>
                        <li><b>Shader Code</b> : Code to replace the specified tag in the shader. Can be added directly in the </li>file by clicking <i>Open File</i>.
                        <li><b>Open File</b> : Open the class containing the shader.</li>
                        <li><b>Modify</b> : Apply the modifications the the class.</li>
                    </ul>
                    <li><b>Add Param</b> : Add specified parameters to the class that will be used in the shader.</li>
                    <ul>
                        <li><b>Type</b> : Type of the parameter.</li>
                        <li><b>Name</b> : Name of the parameter that will be used in the shader.</li>
                        <li><b>Display Name</b> : Name of the parameter that will be displayed in the UI.</li>
                        <li><b>Add Parameter</b> : Add the parameter in the class.</li>
                    </ul>
                </ul>
            </ul>
        </td>
        <td style="white-space:nowrap;">
            <img src="/SlicerPRISM/Resources/Documentation/MCCustomShader.png" alt="MCCustomShader" width ="50%" title="MCCustomShader"/>
        </td>
    </tr>
    <tr style="white-space:nowrap;">
        <td style="white-space:nowrap;">
            <img src="/SlicerPRISM/Resources/Documentation/MCCustomShaderCode.png" alt="MCCustomShaderCode" width ="50%" title="MCCustomShaderCode"/>
        </td>
    </tr>
    <tr style="white-space:nowrap;">
        <td style="white-space:nowrap;">
            <img src="/SlicerPRISM/Resources/Documentation/MCCustomShaderParam.png" alt="MCCustomShaderParam" width ="50%" title="MCCustomShaderParam"/>
        </td>
    </tr>
</table>

<p align="center"><img src="/SlicerPRISM/Resources/Documentation/UnderConstruction.gif" alt="UnderConstruction" width ="30%" title="MCCustomShaderParam"/></p>

<a name="similar"></a>
## Similar Modules

[VolumeRendering](https://www.slicer.org/wiki/Documentation/4.10/Modules/VolumeRendering)
<a name="ref"></a>
## References

[PRISM: An open source framework for the interactive design of GPU volume rendering shaders](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0193636)  
<a name="info"></a>
## Information for Developers

<a name="lim"></a>
### Limitations

<a name="key"></a>
### Key nodes and classes

<a name="howto"></a>
### How Tos
