from import_export import resources, fields
from import_export.widgets import DateWidget
from .models import CollegeData


class BaseCollegeResource(resources.ModelResource):
    dob = fields.Field(
        column_name='dob',
        attribute='dob',
        widget=DateWidget(
            format='%d-%m-%Y'  # adjust to your Excel format
        )
    )

    class Meta:
        model = CollegeData
        import_id_fields = ('college_id',)
        skip_unchanged = True
        report_skipped = True

class StudentResource(BaseCollegeResource):
    class Meta:
        model = CollegeData
        import_id_fields = ['college_id']
        fields = ['college_id','gender', 'f_name','l_name', 'email','college', 'phone', 'father_name', 'mother_name', 'address', 'dob', 'role']
    def before_import_row(self, row, **kwargs):
        row['role'] = 'Student'


class TeacherResource(BaseCollegeResource):
    class Meta:
        model = CollegeData
        import_id_fields = ['college_id']
        fields = ['college_id','gender', 'f_name','l_name', 'email', 'phone','college','designation', 'address', 'dob', 'role']
    def before_import_row(self, row, **kwargs):
        row['role'] = 'Teacher'

class AdminResource(BaseCollegeResource):
    class Meta:
        model = CollegeData
        import_id_fields = ['college_id']
        fields = ['college_id','gender','f_name','l_name', 'email', 'phone', 'branch','college', 'address', 'dob', 'role']
    def before_import_row(self, row, **kwargs):
        row['role'] = 'Admin'

