from collections import OrderedDict

# from flask_wtf import Form
from flask_wtf import FlaskForm
from wtforms import DateTimeField, FloatField, IntegerField, SelectField, StringField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, Regexp, NumberRange
# from wtforms_components import Unique
from wtforms_alchemy import Unique

from lib.util_wtforms import ModelForm, choices_from_dict
from lib.locale import Currency
from painel.blueprints.user.models import db, User
from painel.blueprints.billing.models.coupon import Coupon


class SearchForm(FlaskForm):
    q = StringField('Search terms', [Optional(), Length(1, 256)])


class BulkDeleteForm(FlaskForm):
    SCOPE = OrderedDict([
        ('all_selected_items', 'All selected items'),
        ('all_search_results', 'All search results')
    ])

    # Hello. This is Nick from the future (July 2022 to be exact). I modified
    # things by adding this hidden form field to the admin users and coupons
    # pages. This hidden field is now also included in both admin index pages
    # that include the bulk delete form:
    #
    # It's on line 22 in the admin/user/index.html page and line 34 in the
    # admin/coupon/index.html page. No inline comments were added there.
    q = HiddenField('Search term', [Optional(), Length(1, 10)])

    scope = SelectField('Privileges', [DataRequired()],
                        choices=choices_from_dict(SCOPE, prepend_blank=False))


class UserForm(ModelForm):
    username_message = 'Letters, numbers and underscores only please.'

    username = StringField(validators=[
        Unique(
            User.username,
            get_session=lambda: db.session
        ),
        Optional(),
        Length(1, 16),
        # Part of the Python 3.7.x update included updating flake8 which means
        # we need to explicitly define our regex pattern with r'xxx'.
        Regexp(r'^\w+$', message=username_message)
    ])

    role = SelectField('Privileges', [DataRequired()],
                       choices=choices_from_dict(User.ROLE,
                                                 prepend_blank=False))
    active = BooleanField('Yes, allow this user to sign in')

class UserCancelSubscriptionForm(FlaskForm):
    pass

class CouponForm(FlaskForm):
    percent_off = IntegerField('Percent off (%)', [Optional(),
                                                   NumberRange(min=1,
                                                               max=100)])
    amount_off = FloatField('Amount off ($)', [Optional(),
                                               NumberRange(min=0.01,
                                                           max=21474836.47)])
    code = StringField('Code', [DataRequired(), Length(1, 32)])
    currency = SelectField('Currency', [DataRequired()],
                           choices=choices_from_dict(Currency.TYPES,
                                                     prepend_blank=False))
    duration = SelectField('Duration', [DataRequired()],
                           choices=choices_from_dict(Coupon.DURATION,
                                                     prepend_blank=False))
    duration_in_months = IntegerField('Duration in months', [Optional(),
                                                             NumberRange(
                                                                 min=1,
                                                                 max=12)])
    max_redemptions = IntegerField('Max Redemptions',
                                   [Optional(), NumberRange(min=1,
                                                            max=2147483647)])
    redeem_by = DateTimeField('Redeem by', [Optional()],
                              format='%Y-%m-%d %H:%M:%S')

    def validate(self, extra_validators=None):
        if not FlaskForm.validate(self, extra_validators=extra_validators):
            return False

        result = True
        percent_off = self.percent_off.data
        amount_off = self.amount_off.data

        if percent_off is None and amount_off is None:
            empty_error = 'Pick at least one.'
            self.percent_off.errors.append(empty_error)
            self.amount_off.errors.append(empty_error)
            result = False
        elif percent_off and amount_off:
            both_error = 'Cannot pick both.'
            self.percent_off.errors.append(both_error)
            self.amount_off.errors.append(both_error)
            result = False
        else:
            pass

        return result