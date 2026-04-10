# Configuration file for the Sphinx documentation builder.
# Bullseye Fintech — NSE EOD Dashboard
# =========================================================================

import os
import sys

# -- Path setup --------------------------------------------------------------
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'Bullseye Fintech'
copyright = '2024–2026, Bullseye Fintech'
author = 'Bullseye Fintech'
release = '2.0.6'
version = '2.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinx.ext.intersphinx',
    'sphinx_copybutton',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'

html_theme_options = {
    'logo_only': False,
    'navigation_depth': 4,
    'titles_only': False,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'prev_next_buttons_location': 'both',
    'style_external_links': True,
    'style_nav_header_background': '#0f1629',
}

html_static_path = ['_static']

html_css_files = [
    'css/custom.css',
]

html_title = 'Bullseye Fintech Docs'
html_short_title = 'Bullseye'

# Sidebar extras
html_context = {
    'display_github': True,
    'github_user': 'pranava-ba',
    'github_repo': 'bullseye-nse-eod',
    'github_version': 'main',
    'conf_py_path': '/docs/',
}

# -- MathJax -----------------------------------------------------------------
mathjax3_config = {
    'tex': {
        'inlineMath': [['$', '$'], ['\\(', '\\)']],
        'displayMath': [['$$', '$$'], ['\\[', '\\]']],
    }
}

# -- intersphinx mapping -----------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- copybutton --------------------------------------------------------------
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# -- Suppress warnings -------------------------------------------------------
suppress_warnings = ['toc.secnum']
