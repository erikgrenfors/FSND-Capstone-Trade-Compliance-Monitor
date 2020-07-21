import os
import time
import unittest

from tcm_app import create_app
from tcm_app.models import db


class TradeComplianceMonitor(unittest.TestCase):
    """Trade Compliance Monitor test case"""

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('EMPLOYEE_ROLE_ACCESS_TOKEN', None)
        co_token = os.environ.get('CO_ROLE_ACCESS_TOKEN', None)
        if token is None:
            raise Exception(
                "EMPLOYEE_ROLE_ACCESS_TOKEN environment variable is missing. " +
                "It's value must be a JWT access token.")
        if co_token is None:
            raise Exception(
                "CO_ROLE_ACCESS_TOKEN environment variable is missing. " +
                "It's value must be a JWT access token.")
        cls.headers = {'Authorization': 'Bearer ' + token}
        cls.co_headers = {'Authorization': 'Bearer ' + co_token}
        cls.trade_json = {
            "isin": "US0378331005",
            "amount": 36500,
            "price": 365.00,
            "direction": 'Buy',
            "date": "2020-01-01",
            "name": "Apple Inc",
            "quantity": 100,
            "currency": "USD"
        }

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        time.sleep(5)  # To stay clear of 429 response when requesting userinfo

    def test_post_trades(self):
        body = self.trade_json.copy()
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        self.assertEqual(res.status_code, 200)

        body['direction'] = 'X'
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        self.assertEqual(res.status_code, 422)

        body['isin'] = 'US0378331004'
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        self.assertEqual(res.status_code, 422)

        body['amount'] = '36411'
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        self.assertEqual(res.status_code, 422)

        body['price'] = '364,11'
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        self.assertEqual(res.status_code, 422)

        body['date'] = '20200715'
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        self.assertEqual(res.status_code, 422)

        body['quantity'] = '100'
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        self.assertEqual(res.status_code, 422)

        body['currency'] = 'US'
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        self.assertEqual(res.status_code, 422)

    def test_get_trades(self):
        res = self.client.get('/api/trades', headers=self.headers)
        self.assertEqual(res.status_code, 204)
        # Use Employee reporting two trades
        body = self.trade_json.copy()
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        res = self.client.get('/api/trades', headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_get_trade(self):
        res = self.client.get('/api/trades/1', headers=self.co_headers)
        self.assertEqual(res.status_code, 404)

        # Use CO as Employee reporting a violating trade (buy and sell)
        body = self.trade_json.copy()
        res = self.client.post('/api/trades', headers=self.co_headers, json=body)
        res = self.client.get('/api/trades/1', headers=self.co_headers)
        self.assertEqual(res.status_code, 200)
        # ... which other Employees cant see.
        self.client.cookie_jar.clear()
        res = self.client.get('/api/trades/1', headers=self.headers)
        self.assertEqual(res.status_code, 404)

    def test_patch_trade(self):
        body = self.trade_json.copy()
        res = self.client.patch('/api/trades/1', headers=self.co_headers, json=body)
        self.assertEqual(res.status_code, 404)

        # Use CO as Employee reporting a trade to patch
        body = self.trade_json.copy()
        res = self.client.post('/api/trades', headers=self.co_headers, json=body)
        res = self.client.patch('/api/trades/1', headers=self.co_headers, json=body)
        self.assertEqual(res.status_code, 204)

        body['quantity'] = 50
        res = self.client.patch('/api/trades/1', headers=self.co_headers, json=body)
        self.assertEqual(res.status_code, 200)

        # ... which other Employees cant change.
        self.client.cookie_jar.clear()
        res = self.client.patch('/api/trades/1', headers=self.headers, json=body)
        self.assertEqual(res.status_code, 404)

    def test_delete_trade(self):
        res = self.client.delete('/api/trades/1', headers=self.co_headers)
        self.assertEqual(res.status_code, 404)

        # Use CO as Employee reporting two trades
        body = self.trade_json.copy()
        res = self.client.post('/api/trades', headers=self.co_headers, json=body)
        res = self.client.post('/api/trades', headers=self.co_headers, json=body)
        # ... which he/she can delete ...
        res = self.client.delete('/api/trades/1', headers=self.co_headers)
        self.assertEqual(res.status_code, 204)
        # ... but other Employees cant delete.
        self.client.cookie_jar.clear()
        res = self.client.delete('/api/trades/2', headers=self.headers)
        self.assertEqual(res.status_code, 404)

        # Use Employee reporting two trades
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        # ... which he/she can delete ...
        res = self.client.delete('/api/trades/3', headers=self.headers)
        self.assertEqual(res.status_code, 204)
        # ... but which not even a CO can delete.
        self.client.cookie_jar.clear()
        res = self.client.delete('/api/trades/4', headers=self.co_headers)
        self.assertEqual(res.status_code, 404)

    def test_get_violations(self):
        res = self.client.get('/api/violations', headers=self.headers)
        self.assertEqual(res.status_code, 204)

        # Use Employee reporting a violating trade (buy and sell)
        body = self.trade_json.copy()
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        body['date'] = '2020-01-15'
        body['price'] = 375
        body['direction'] = 'Sell'
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        # Now there are a violation ...
        res = self.client.get('/api/violations', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        # ... which other Employees cant see.

        self.client.cookie_jar.clear()
        res = self.client.get('/api/violations', headers=self.co_headers)
        self.assertEqual(res.status_code, 204)


    def test_get_all_violations(self):
        res = self.client.get('/api/all-violations', headers=self.co_headers)
        self.assertEqual(res.status_code, 204)

        # Use CO as Employee reporting a violating trade (buy and sell)
        body = self.trade_json.copy()
        res = self.client.post('/api/trades', headers=self.co_headers, json=body)
        body['date'] = '2020-01-15'
        body['price'] = 375
        body['direction'] = 'Sell'
        res = self.client.post('/api/trades', headers=self.co_headers, json=body)
        # Now there are a violation ...
        res = self.client.get('/api/all-violations', headers=self.co_headers)
        self.assertEqual(res.status_code, 200)
        # ... which other Employees cant see.
        self.client.cookie_jar.clear()
        res = self.client.get('/api/all-violations', headers=self.headers)
        self.assertEqual(res.status_code, 403)

        # Use Employee reporting a violating trade (buy and sell)
        body = self.trade_json.copy()
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        body['date'] = '2020-01-15'
        body['price'] = 375
        body['direction'] = 'Sell'
        res = self.client.post('/api/trades', headers=self.headers, json=body)
        # Now there are violations for which a CO can see
        # (delete his/her own first)
        self.client.cookie_jar.clear()
        res = self.client.delete('/api/trades/1', headers=self.co_headers)
        res = self.client.delete('/api/trades/2', headers=self.co_headers)
        res = self.client.get('/api/all-violations', headers=self.co_headers)
        self.assertEqual(res.status_code, 200)


if __name__ == '__main__':
    unittest.main()
