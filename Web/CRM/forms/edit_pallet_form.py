from django.forms import Form, DecimalField


class EditPalletForm(Form):
    weight = DecimalField(decimal_places=2, max_digits=15, min_value=0.01, label="Новый вес палетта", required=True)
