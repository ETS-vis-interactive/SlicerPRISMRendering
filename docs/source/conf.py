import os
import sys

# Ajoutez le chemin relatif au répertoire PRISMRendering
sys.path.insert(0, os.path.abspath('../../PRISMRendering'))

# Test d'importation pour s'assurer que le module est trouvé
try:
    import PRISMRendering
    print("Module imported successfully")
except ImportError as e:
    print("Error importing module:", e)

# -- Project information -----------------------------------------------------
master_doc = 'index'

project = 'SlicerPRISMRendering'
copyright = '2020, Tiphaine RICHARD'
author = 'Tiphaine Richard (ETS), Simon Drouin (ETS)'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'recommonmark',
    'sphinx.ext.graphviz',
    'sphinx.ext.inheritance_diagram'
]

templates_path = []
exclude_patterns = []
add_module_names = False

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_favicon = 'images/logoPRISMRenderingHTMLfavicon.png'
html_logo = 'images/logoPRISMRenderingHTML.png'
html_static_path = []

autodoc_mock_imports = ["PythonQt", "vtk", "qt", "ctk", "slicer", "numpy"]

# -- Options for graphs -------------------------------------------------------
graphviz_output_format = 'svg'
inheritance_graph_attrs = dict(rankdir="TB", size='""')

# Source suffix
source_suffix = ['.rst', '.md']

def setup(app):
    from recommonmark.transform import AutoStructify
    app.add_config_value('recommonmark_config', {
            'url_resolver': lambda url: github_doc_root + url,
            'auto_toc_tree_section': 'Contents',
            }, True)
    app.add_transform(AutoStructify)
