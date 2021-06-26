from django import forms
from .models import Server, ServerGroup, Upgrade, UpgradeResult


class CreateServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = [
            "name",
            "address",
        ]


class CreateGroupForm(forms.ModelForm):
    servers = forms.ModelMultipleChoiceField(
        queryset=Server.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = ServerGroup
        fields = [
            "name",
            "servers",
        ]


class PatchForm(forms.Form):
    # nodes = forms.ChoiceField(initial='All Nodes')
    patches = forms.ModelMultipleChoiceField(
        queryset=Upgrade.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class NodeGroupForm(forms.Form):
    servers = forms.ModelMultipleChoiceField(
        queryset=ServerGroup.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
    )


class PatchNameForm(forms.Form):
    name = forms.CharField(
        label="name",
        max_length=100,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Please enter Name",
                "cols": 50,
                "rows": 2,
            }
        ),
    )
