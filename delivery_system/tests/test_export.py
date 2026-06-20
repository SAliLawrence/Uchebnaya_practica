import pytest
import tempfile
import os
from data_export import DataExporter


def test_json_export_import():
    exporter = DataExporter()
    test_data = [{'id': 1, 'customer_id': 1, 'order_date': '2025-01-01', 'status': 'новый', 'total': 100, 'items': []}]

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        exporter.export_to_json(test_data, f.name)
        imported = exporter.import_from_json(f.name)
        os.unlink(f.name)

    assert len(imported) == 1


def test_validate_order_data():
    exporter = DataExporter()
    valid_order = {'customer_id': 1, 'order_date': '2025-01-01', 'status': 'новый', 'total': 100, 'items': []}
    assert exporter.validate_order_data(valid_order) == True
