import sys
from datetime import datetime

import simplejson
from flask import abort
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, ValidationError, fields, validate

db = SQLAlchemy()


# ---
# CUSTOM MARSHMALLOW VALIDATORS
# ---
def validate_isin(a):
    """Raises an error when ISIN is invalid.
    Code adapted from: https://rosettacode.org/wiki/Validate_International_Securities_Identification_Number#Python
    """
    if len(a) != 12 or not all(c.isalpha() for c in a[:2]) or not all(
            c.isalnum() for c in a[2:]):
        raise ValidationError("Not a valid ISIN.")
    s = "".join(str(int(c, 36)) for c in a)
    if 0 != (sum(sum(divmod(2 * (ord(c) - 48), 10)) for c in s[-2::-2]) +
             sum(ord(c) - 48 for c in s[::-2])) % 10:
        raise ValidationError("Invalid ISIN.")


def validate_not_future_date(date):
    """Raises an error when date is in the future"""
    if date > datetime.now().date():
        raise ValidationError("Future dates not allowed!")


# ---
# MODELS
# ---
class Trade(db.Model):
    __tablename__ = 'Trade'
    id = db.Column(db.Integer, primary_key=True)
    isin = db.Column(db.String(12), nullable=False)
    name = db.Column(db.String, nullable=False)
    direction = db.Column(db.String(4), nullable=False)
    quantity = db.Column(db.Numeric, nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    amount = db.Column(db.Numeric, nullable=False)
    date = db.Column(db.Date, nullable=False)
    reporter = db.Column(db.String(), nullable=False)
    reported_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        items = self.__dict__.items()
        return '<Trade {}>'.format(', '.join(
            [f'{key}={str(value)}' for (key, value) in items if key[0] != '_']
        ))

    def create(self):
        """Creates model in db and sends it back serialised.
        """
        error = False
        try:
            db.session.add(self)
            db.session.commit()
        except BaseException:
            print(sys.exc_info())
            db.session.rollback()
            error = True
        finally:
            serialised = trade_schema.dump(self)
            db.session.close()
            return serialised

        if error:
            abort(422)

    def update(self):
        """Updates model in db and sends it back serialised.
        """
        error = False
        try:
            db.session.commit()
        except BaseException:
            print(sys.exc_info())
            db.session.rollback()
            error = True
        finally:
            serialised = trade_schema.dump(self)
            db.session.close()
            return serialised

        if error:
            abort(422)

    def delete(self):
        """Deletes model from db.
        """
        error = False
        try:
            db.session.delete(self)
            db.session.commit()
        except BaseException:
            print(sys.exc_info())
            db.session.rollback()
            error = True
        finally:
            db.session.close()

        if error:
            abort(422)


class TradeSchema(Schema):
    id = fields.Integer(dump_only=True, example=1)
    isin = fields.Str(
        required=True, validate=validate_isin, example='US0378331005')
    name = fields.Str(required=True, example='Apple Inc')
    direction = fields.Str(
        required=True, validate=validate.OneOf(['Buy', 'Sell']), example='Buy')
    quantity = fields.Decimal(required=False, example=100)
    price = fields.Decimal(example=364.11)
    currency = fields.Str(
        required=True, validate=validate.Length(equal=3), example='USD',
        description='A three letter long code')
    amount = fields.Decimal(required=False, example=36411)
    date = fields.Date(required=True, validate=validate_not_future_date)
    reporter = fields.Str(dump_only=True, example='john.doe@example.com')
    reported_at = fields.DateTime(dump_only=True, description='UTC')

    # Required to handle Decimal type, see documentation for fields.Decimal()
    class Meta:
        json_module = simplejson


trade_schema = TradeSchema()
trades_schema = TradeSchema(many=True)


class TradePaperTrail(db.Model):
    __tablename__ = 'TradePaperTrail'
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, nullable=False)
    isin = db.Column(db.String(12), nullable=False)
    name = db.Column(db.String, nullable=False)
    direction = db.Column(db.String(4), nullable=False)
    quantity = db.Column(db.Numeric, nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    amount = db.Column(db.Numeric, nullable=False)
    date = db.Column(db.Date, nullable=False)
    reporter = db.Column(db.String(), nullable=False)
    reported_at = db.Column(db.DateTime, nullable=False)
    trailed_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        items = self.__dict__.items()
        return '<TradePaperTrail {}>'.format(', '.join(
            [f'{key}={str(value)}' for (key, value) in items if key[0] != '_']
        ))
