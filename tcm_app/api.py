from datetime import datetime

from flasgger import SwaggerView
from flask import (
    Blueprint, abort, current_app, jsonify, make_response, request)
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from tcm_app.auth import require_token
from tcm_app.models import (
  Trade, TradePaperTrail, db, trade_schema, trades_schema)
import pandas as pd

bp = Blueprint('api', __name__, url_prefix='/api')


class TradesView(SwaggerView):
    tags = ['trades']

    @require_token('get:trades')
    def get(self):
        """
        Fetch all trades reported by authenticated user
        ---
        responses:
          200:
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Trade'
          204:
            description: When no trades exist.
        """
        # Query DB for trades filtered by email (from userinfo via JWT)
        trades = Trade.query.filter_by(reporter=self.email).all()
        if len(trades) == 0:
            return make_response_204()
        result = trades_schema.dump(trades)
        return jsonify(result)

    @require_token('post:trades')
    def post(self):
        """
        Report a trade (for the authenticated user)
        ---
        requestBody:
          description: Trade information to be reported
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Trade'
          required: true
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Trade'
        """
        # Validate and deserialize input
        json_data = request.get_json()
        if not json_data:
            abort(400, 'No input data provided.')
        try:
            data = trade_schema.load(json_data)
        except ValidationError as err:
            abort(422, err.messages)

        # Create new trade object
        trade = Trade(
            isin=data['isin'],
            name=data['name'],
            direction=data['direction'],
            date=data['date'],
            price=data['price'],
            currency=data['currency'],
            quantity=data['quantity'],
            amount=data['amount'],
            reporter=self.email,  # From userinfo for current access token
            reported_at=datetime.utcnow()
        )

        # Persist in db and serialise
        serialised_trade = trade.create()

        return jsonify(serialised_trade)


bp.add_url_rule(
    '/trades',
    view_func=TradesView.as_view('trades_endpoint'),
    methods=['GET', 'POST']
)


class TradeView(SwaggerView):
    tags = ['trades']

    @require_token('get:trades')
    def get(self, id):
        """
        Fetch trade with specified id reported by authenticated user
        ---
        parameters:
        - name: id
          in: path
          description: Trade Identifier
          required: true
          schema:
            type: integer
            format: int64
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Trade'
        """
        trade = Trade.query.filter_by(id=id, reporter=self.email).all()
        if len(trade) == 0:  # Not a valid id for logged-in user
            abort(404)

        # Serialize
        result = trade_schema.dump(trade[0])
        return jsonify(result)

    @require_token('patch:trades')
    def patch(self, id):
        """
        Update a trade (for the authenticated user)
        ---
        parameters:
        - name: id
          in: path
          description: Trade Identifier
          required: true
          schema:
            type: integer
            format: int64
        requestBody:
          description: Trade information to be reported
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Trade'
          required: true
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Trade'
          204:
            description: When patched info is identical to what already exist.
        """
        # Validate and deserialize input (marshmallow)
        body = request.get_json()
        if not body:
            abort(400, 'No input data provided.')
        try:
            trade_updated_info = trade_schema.load(body)
        except ValidationError as err:
            abort(422, err.messages)

        # Query for existing trade
        trade = Trade.query.filter_by(id=id, reporter=self.email).one_or_none()
        if trade is None:  # Not a valid id for logged-in user
            abort(404)

        # Keep paper trail of previous trade record
        trail = TradePaperTrail()
        changed = False
        for key, value in trade_updated_info.items():
            current_value = getattr(trade, key)
            setattr(trail, key, current_value)
            if current_value != value:
                setattr(trade, key, value)
                changed = True

        if changed:
            trail.trade_id = id
            trail.reporter = self.email
            trail.reported_at = trade.reported_at
            trade.reported_at = datetime.utcnow()
            trail.trailed_at = trade.reported_at

            # Persist in db and serialise
            serialised_trade = trade.update()

            return jsonify(serialised_trade)
        else:
            return make_response_204()

    @require_token('delete:trades')
    def delete(self, id):
        """
        Delete a trade (for the authenticated user)
        ---
        parameters:
        - name: id
          in: path
          description: Trade Identifier
          required: true
          schema:
            type: integer
            format: int64
        responses:
          204:
            description: When deletion successful.
        """
        # Query for existing trade
        trade = Trade.query.filter_by(id=id, reporter=self.email).one_or_none()
        if trade is None:  # Not a valid id for logged-in user
            abort(404)

        # Keep paper trail of deleted trade
        trail = TradePaperTrail()
        attributes = (
            'isin', 'name', 'direction', 'quantity', 'price', 'currency',
            'amount', 'date', 'reporter', 'reported_at')
        for attribute in attributes:
            setattr(trail, attribute, getattr(trade, attribute))
        trail.trade_id = id
        trail.trailed_at = datetime.utcnow()

        # Persist data in database
        db.session.add(trail)
        trade.delete()

        return make_response_204()


bp.add_url_rule(
    '/trades/<int:id>',
    view_func=TradeView.as_view('trade_endpoint'),
    methods=['GET', 'PATCH', 'DELETE']
)


class ViolationsView(SwaggerView):
    tags = ['violations']

    @require_token('get:violations')
    def get(self):
        """
        Fetch all trades (for authenticated user) violating holding period
        regulation
        ---
        responses:
          200:
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    violations:
                      type: integer
                      description: Number of violations.
                      example: 1
                    data:
                      type: array
                      items:
                        type: array
                        items:
                          type: object
                          properties:
                            duration:
                              type: integer
                              description: Number of days.
                              example: 1
                            data:
                              type: array
                              items:
                                type: array
                                items:
                                  $ref: '#/components/schemas/Trade'
                                minItems: 2
                                maxItems: 2
          204:
            description: When there are no trade violations.
        """
        # Query DB for trades filtered by email (from userinfo via JWT) and
        # store in a Pandas dataframe.
        trades = pd.read_sql(
            Trade.query.filter_by(reporter=self.email).order_by(
                Trade.date.asc()).statement,
            db.session.bind
        )

        violations = find_violations(trades)
        if violations is None:
            return make_response_204()

        return jsonify(violations)


bp.add_url_rule(
    '/violations',
    view_func=ViolationsView.as_view('violations_endpoint'),
    methods=['GET']
)


class AllTradesView(SwaggerView):
    tags = ['all-trades']

    @require_token('get:all-trades')
    def get(self):
        """
        Fetch all trades reported by any reporter
        ---
        responses:
          200:
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Trade'
          204:
            description: When no trades exist.
        """
        # Query DB for all trades
        trades = Trade.query.all()
        if len(trades) == 0:
            return make_response_204()
        result = trades_schema.dump(trades)
        return jsonify(result)


bp.add_url_rule(
    '/all-trades',
    view_func=AllTradesView.as_view('all_trades_endpoint'),
    methods=['GET']
)


class AllViolationsView(SwaggerView):
    tags = ['all-violations']

    @require_token('get:all-violations')
    def get(self):
        """
        Fetch all trades (for all users) violating holding period regulation
        ---
        responses:
          200:
            content:
              application/json:
                schema:
                  type: array
                  items:
                    type: object
                    properties:
                      reporter:
                        type: string
                        example: john.doe@example.com
                      data:
                        type: object
                        properties:
                          violations:
                            type: integer
                            description: Number of violations.
                            example: 1
                          data:
                            type: array
                            items:
                              type: array
                              items:
                                type: object
                                properties:
                                  duration:
                                    type: integer
                                    description: Number of days.
                                    example: 1
                                  data:
                                    type: array
                                    items:
                                      type: array
                                      items:
                                        $ref: '#/components/schemas/Trade'
                                      minItems: 2
                                      maxItems: 2
          204:
            description: When there are no trade violations.
        """
        # Query DB for all trades and store in a Pandas dataframe.
        trades = pd.read_sql(
            Trade.query.order_by(Trade.date.asc()).statement, db.session.bind)

        # # One list item per ISIN.
        violations_by_reporter = []
        by_reporter = trades.groupby('reporter')
        for reporter, trades_ in by_reporter:
            violations = find_violations(trades_)
            if violations is not None:
                violations_by_reporter.append({
                    'reporter': reporter,
                    'data': violations
                })

        if len(violations_by_reporter) == 0:
            return make_response_204()

        return jsonify(violations_by_reporter)


bp.add_url_rule(
    '/all-violations',
    view_func=AllViolationsView.as_view('all-violations_endpoint'),
    methods=['GET']
)


@bp.errorhandler(Exception)
def errorhandler(ex):
    if not isinstance(ex, HTTPException):
        return abort(500)
    response = jsonify(message=str(ex))
    response.status_code = ex.code
    return response


def find_violations(trades):
    """Searches for trade violations by matching buy and sell trades on a
    First In, First Out (FIFO) basis.
    """

    if len(trades) == 0:
        return None
    # Check uniqueness
    if len(trades['reporter'].unique()) != 1:
        raise Exception('DataFrame "trades" must include only one reporter.')

    violations_by_isin = []
    ctr_violations = 0
    grouped_by_isin = trades.groupby('isin')
    for isin, trades in grouped_by_isin:
        # Create separate DataFrames for buy and sell.
        by_direction = trades.groupby('direction')
        if len(by_direction) == 1:
            continue

        buy = by_direction.get_group('Buy').copy(deep=False)
        buy.reset_index(drop=True, inplace=True)
        sell = by_direction.get_group('Sell').copy(deep=False)
        sell.reset_index(drop=True, inplace=True)

        closed_positions = pd.DataFrame(
            columns=['buy_id', 'sell_id', 'qty', 'duration'])

        while len(buy) and len(sell):
            tmp = pd.DataFrame(data={
                'buy_id': [buy.loc[0, 'id']],
                'sell_id': [sell.loc[0, 'id']],
                'buy_price': [buy.loc[0, 'price']],
                'sell_price': [sell.loc[0, 'price']],
                'qty': [buy.loc[0, 'quantity'] - sell.loc[0, 'quantity']],
                'duration': [
                    abs(buy.loc[0, 'date'] - sell.loc[0, 'date']).days]
            })
            if tmp.loc[0, 'qty'] == 0:
                tmp.loc[0, 'qty'] = buy.loc[0, 'quantity']
                buy.drop(0, inplace=True)
                buy.reset_index(drop=True, inplace=True)
                sell.drop(0, inplace=True)
                sell.reset_index(drop=True, inplace=True)
            elif tmp.loc[0, 'qty'] < 0:
                sell.loc[0, 'quantity'] = abs(tmp.loc[0, 'qty'])
                tmp.loc[0, 'qty'] = buy.loc[0, 'quantity']
                buy.drop(0, inplace=True)
                buy.reset_index(drop=True, inplace=True)
            else:
                buy.loc[0, 'quantity'] = abs(tmp.loc[0, 'qty'])
                tmp.loc[0, 'qty'] = sell.loc[0, 'quantity']
                sell.drop(0, inplace=True)
                sell.reset_index(drop=True, inplace=True)

            closed_positions = closed_positions.append(tmp)

        # Only interested in profitable trades violating holding period
        too_quick = closed_positions.duration < 32
        with_profit = closed_positions.buy_price < closed_positions.sell_price
        violating = closed_positions[too_quick & with_profit]

        if len(violating) != 0:
            violating_by_duration = []
            by_duration = violating.groupby('duration')
            for duration, position_df in by_duration:
                buy_sell_pairs = []
                for i in range(len(position_df)):
                    # ---------------------------------------------------------
                    # Use buy_id and sell_id from position table to query db
                    # for the corresponding trades (again even though we
                    # already have them in a dataframe).
                    # WHY not using Pandas to_dict method?
                    # When importing using read_sql() certain types are
                    # converted to something we don't want (e.g. decimal to
                    # numeric), and when exporting using
                    # to_dict(orient='records') datetime turns into Timespan.
                    # However, with few expected violating trades querying the
                    # database again should be fine.
                    # ---------------------------------------------------------
                    trade_data = Trade.query.filter(
                        Trade.id.in_(
                            (position_df.iloc[i, 0], position_df.iloc[i, 1])
                        )
                    ).all()
                    buy_sell_pairs.append(trades_schema.dump(trade_data))
                    ctr_violations += 1

                violating_by_duration.append({
                    'duration': duration,
                    'data': buy_sell_pairs
                })

            violations_by_isin.append(violating_by_duration)

    if ctr_violations == 0:
        return None

    return {'violations': ctr_violations, 'data': violations_by_isin}


def make_response_204():
    """Returns a 204 No Content response.
    """
    response = make_response('', 204)
    response.mimetype = current_app.config['JSONIFY_MIMETYPE']
    return response
