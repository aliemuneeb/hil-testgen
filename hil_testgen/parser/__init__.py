# hil_testgen/parser/__init__.py
echo "from hil_testgen.parser.docx_parser import DocxParser
from hil_testgen.parser.excel_parser import ExcelParser
from hil_testgen.parser.pdf_parser import PdfParser

__all__ = ['DocxParser', 'ExcelParser', 'PdfParser']" > hil_testgen/parser/__init__.py

# hil_testgen/generator/__init__.py
echo "from hil_testgen.generator.ai_engine import AIEngine
from hil_testgen.generator.confidence_scorer import ConfidenceScorer
from hil_testgen.generator.test_case_builder import TestCaseBuilder

__all__ = ['AIEngine', 'ConfidenceScorer', 'TestCaseBuilder']" > hil_testgen/generator/__init__.py

# hil_testgen/exporters/__init__.py
echo "from hil_testgen.exporters.excel_exporter import ExcelExporter
from hil_testgen.exporters.csv_exporter import CsvExporter
from hil_testgen.exporters.html_exporter import HtmlExporter

__all__ = ['ExcelExporter', 'CsvExporter', 'HtmlExporter']" > hil_testgen/exporters/__init__.py
