# General Informations

## Introduction and Acknowledgements
**Title**: SlicerPRISMRendering

**Author(s)/Contributor(s)**: 
* Tiphaine RICHARD, Student Intern at École de technologie supérieure (ÉTS)
* Simon Drouin, Professor at ÉTS
* Camille Hascoët, Student Intern at École de technologie supérieure (ÉTS)

**License**: BSD

**Contact**: Simon Drouin, simon.drouin@etsmtl.ca

## Module Description

The goal of the PRISM Rendering module is to provide a set of examples of advanced volume rendering techniques not implemented in the standard volume rendering module. It also facilitates the implementation of new volume rendering techniques by allowing users to build their own effects. 

The PRISM Rendering module uses the functionality of the existing VolumeRendering module. It enables the implementation of various volume rendering effects by replacing part of the standard VTK volume rendering OpenGL shader.

Slicer version > 4.11.0 is needed to use this module.

The whole documentation of the module can be found [here](https://githubcomets-vis-interactiveslicerprismrendering.readthedocs.io/en/latest/).

## History

The PRISM Rendering module is an implementation for 3D Slicer of the original PRISM module developped for the Ibis Neuronav platform and described in [this paper](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0193636). Some of the functionality described in the original PRISM paper are not implemented in the Slicer version. The original PRISM from Ibis Neuronav is no longer maintained. New rendering techniques will be made available in the Slicer implementation.

## Similar Modules

[VolumeRendering](https://www.slicer.org/wiki/Documentation/4.10/Modules/VolumeRendering)

## References

[PRISM: An open source framework for the interactive design of GPU volume rendering shaders](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0193636).
