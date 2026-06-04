from django import forms


class IndividualCertificateForm(forms.Form):
    student_username = forms.CharField(label="Student Username")
    certificate_file = forms.FileField(label="Certificate File")
    student_photo = forms.FileField(label="Student Photo", required=False)

class BulkCertificateForm(forms.Form):
    bulk_file = forms.FileField(label="Certificate Template")
    selected_students_bulk = forms.ModelMultipleChoiceField(
        queryset=None,  # we'll set it dynamically in view
        required=False,
        widget=forms.SelectMultiple
    )