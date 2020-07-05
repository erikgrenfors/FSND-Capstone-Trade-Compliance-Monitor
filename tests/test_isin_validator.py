import unittest

from marshmallow import ValidationError

from tcm_app.models import validate_isin


class TradeComplianceMonitor(unittest.TestCase):
    """Trade Compliance Monitor test case"""

    def test_validate_isin(self):
        self.assertRaises(
            ValidationError, validate_isin, 'ab0123456789')
        self.assertIsNone(validate_isin('US0378331005'))
