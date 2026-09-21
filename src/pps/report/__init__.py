"""
Report generation modules.
"""

from pps.report.core.html_pdf_generator import HTMLPDFGenerator

PDFGenerator = HTMLPDFGenerator

__all__ = ['PDFGenerator', 'HTMLPDFGenerator']