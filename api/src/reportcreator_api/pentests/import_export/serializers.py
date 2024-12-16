from typing import Iterable
from uuid import uuid4

from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from rest_framework import serializers

from reportcreator_api import signals as sysreptor_signals
from reportcreator_api.pentests.customfields.types import (
    FieldDefinition,
    parse_field_definition_legacy,
    serialize_field_definition,
)
from reportcreator_api.pentests.customfields.utils import (
    HandleUndefinedFieldsOptions,
    ensure_defined_structure,
    get_field_value_and_definition,
)
from reportcreator_api.pentests.models import (
    FindingTemplate,
    FindingTemplateTranslation,
    Language,
    PentestFinding,
    PentestProject,
    ProjectMemberInfo,
    ProjectNotebookPage,
    ProjectType,
    ProjectTypeStatus,
    ReportSection,
    ReviewStatus,
    SourceEnum,
    UploadedAsset,
    UploadedFileBase,
    UploadedImage,
    UploadedProjectFile,
    UploadedTemplateImage,
    UploadedUserNotebookFile,
    UploadedUserNotebookImage,
    UserNotebookPage,
)
from reportcreator_api.pentests.models.project import Comment, CommentAnswer
from reportcreator_api.pentests.serializers.project import ProjectMemberInfoSerializer, TextRangeSerializer
from reportcreator_api.users.models import PentestUser
from reportcreator_api.users.serializers import RelatedUserSerializer
from reportcreator_api.utils.history import bulk_create_with_history, merge_with_previous_history
from reportcreator_api.utils.utils import omit_keys


class ExportImportSerializer(serializers.ModelSerializer):
    def perform_import(self):
        return self.create(self.validated_data.copy())

    def export(self):
        return self.data

    def export_files(self) -> Iterable[tuple[str, File]]:
        return []


class FormatField(serializers.Field):
    def __init__(self, format):
        self.format = format
        self.default_validators = [self._validate_format]
        super().__init__()

    def _validate_format(self, v):
        if v != self.format:
            raise serializers.ValidationError(f'Invalid format: expected "{self.format}" got "{v}"')
        else:
            raise serializers.SkipField()

    def get_attribute(self, instance):
        return self.format

    def to_representation(self, value):
        return value

    def to_internal_value(self, value):
        return value


class UserIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = PentestUser
        fields = ['id']


class RelatedUserIdExportImportSerializer(RelatedUserSerializer):
    def __init__(self, **kwargs):
        super().__init__(user_serializer=UserIdSerializer, **{'required': False, 'allow_null': True, 'default': None} | kwargs)

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as ex:
            if isinstance(ex.__cause__, ObjectDoesNotExist):
                # If user does not exit: ignore
                raise serializers.SkipField() from ex
            else:
                raise


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PentestUser
        fields = [
            'id', 'email', 'phone', 'mobile',
            'username', 'name', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after',
        ]
        extra_kwargs = {'id': {'read_only': False}}


class RelatedUserDataExportImportSerializer(ProjectMemberInfoSerializer):
    def __init__(self, **kwargs):
        super().__init__(user_serializer=UserDataSerializer, **kwargs)

    def to_internal_value(self, data):
        try:
            return ProjectMemberInfo(**super().to_internal_value(data))
        except serializers.ValidationError as ex:
            if isinstance(ex.__cause__, ObjectDoesNotExist):
                return data
            else:
                raise


class ProjectMemberListExportImportSerializer(serializers.ListSerializer):
    child = RelatedUserDataExportImportSerializer()

    def to_representation(self, project):
        return super().to_representation(project.members.all()) + project.imported_members

    def to_internal_value(self, data):
        return {self.field_name: super().to_internal_value(data)}


class OptionalPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        super().__init__(**{'required': False, 'allow_null': True, 'default': None} | kwargs)

    def to_internal_value(self, data):
        if data is None:
            raise serializers.SkipField()
        try:
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist as ex:
            raise serializers.SkipField() from ex


class FileListExportImportSerializer(serializers.ListSerializer):
    def export_files(self):
        for f in self.instance:
            if self.child.is_file_referenced(f):
                self.child.instance = f
                yield from self.child.export_files()

    def to_representation(self, data):
        return super().to_representation([f for f in data.all() if self.child.is_file_referenced(f)])

    def extract_file(self, name):
        return self.context['archive'].extractfile(self.child.get_path_in_archive(name))

    def create(self, validated_data):
        child_model_class = self.child.get_model_class()
        objs = [
            child_model_class(**attrs | {
                'name_hash': UploadedFileBase.hash_name(attrs['name']),
                'file': File(
                    file=self.extract_file(attrs.pop('name_internal', None) or attrs['name']),
                    name=attrs['name']),
                'linked_object': self.child.get_linked_object(),
        }) for attrs in validated_data]

        bulk_create_with_history(child_model_class, objs)
        self.context['storage_files'].extend(map(lambda o: o.file, objs))
        return objs


class FileExportImportSerializer(ExportImportSerializer):
    class Meta:
        fields = ['id', 'created', 'updated', 'name']
        extra_kwargs = {
            'id': {'read_only': True},
            'created': {'read_only': False, 'required': False},
        }
        list_serializer_class = FileListExportImportSerializer

    def get_model_class(self):
        return self.Meta.model

    def validate_name(self, name):
        if '/' in name or '\\' in name or '\x00' in name:
            raise serializers.ValidationError(f'Invalid filename: {name}')
        return name

    def get_linked_object(self):
        pass

    def get_path_in_archive(self, name):
        pass

    def is_file_referenced(self, f):
        return self.get_linked_object().is_file_referenced(f)

    def export_files(self) -> Iterable[tuple[str, File]]:
        yield self.get_path_in_archive(self.instance.name), self.instance.file


class FindingTemplateImportSerializerV1(ExportImportSerializer):
    format = FormatField('templates/v1')

    language = serializers.ChoiceField(choices=Language.choices, source='main_translation__language')
    status = serializers.ChoiceField(choices=ReviewStatus.choices, source='main_translation__status', default=ReviewStatus.IN_PROGRESS)
    data = serializers.DictField(source='main_translation__data')

    class Meta:
        model = FindingTemplate
        fields = ['format', 'id', 'created', 'updated', 'tags', 'language', 'status', 'data']
        extra_kwargs = {'id': {'read_only': True}, 'created': {'read_only': False, 'required': False}}

    def create(self, validated_data):
        main_translation_data = {k[len('main_translation__'):]: validated_data.pop(k) for k in validated_data.copy().keys() if k.startswith('main_translation__')}
        template = FindingTemplate.objects.create(**{
            'source': SourceEnum.IMPORTED,
            'skip_post_create_signal': True,
        } | validated_data)
        data = main_translation_data.pop('data', {})
        main_translation = FindingTemplateTranslation(template=template, **main_translation_data)
        main_translation.update_data(data)
        main_translation.save()
        template.main_translation = main_translation
        template.save(update_fields=['main_translation'])
        sysreptor_signals.post_create.send(sender=template.__class__, instance=template)
        return template


class FindingTemplateTranslationExportImportSerializer(ExportImportSerializer):
    data = serializers.DictField(source='data_all')
    is_main = serializers.BooleanField()

    class Meta:
        model = FindingTemplateTranslation
        fields = ['id', 'created', 'updated', 'is_main', 'language', 'status', 'data']
        extra_kwargs = {'id': {'read_only': True}, 'created': {'read_only': False, 'required': False}}

    def create(self, validated_data):
        data = validated_data.pop('data_all', {})
        instance = FindingTemplateTranslation(**validated_data)
        instance.update_data(data)
        instance.save()
        return instance


class UploadedTemplateImageExportImportSerializer(FileExportImportSerializer):
    class Meta(FileExportImportSerializer.Meta):
        model = UploadedTemplateImage

    def get_linked_object(self):
        return self.context['template']

    def get_path_in_archive(self, name):
        # Get ID of old project_type from archive
        return str(self.context.get('template_id') or self.get_linked_object().id) + '-images/' + name


class FindingTemplateExportImportSerializerV2(ExportImportSerializer):
    format = FormatField('templates/v2')
    translations = FindingTemplateTranslationExportImportSerializer(many=True, allow_empty=False)
    images = UploadedTemplateImageExportImportSerializer(many=True, required=False)

    class Meta:
        model = FindingTemplate
        fields = ['format', 'id', 'created', 'updated', 'tags', 'translations', 'images']
        extra_kwargs = {'id': {'read_only': False}, 'created': {'read_only': False, 'required': False}}

    def validate_translations(self, value):
        if len(list(filter(lambda t: t.get('is_main'), value))) != 1:
            raise serializers.ValidationError('No main translation given')
        if len(set(map(lambda t: t.get('language'), value))) != len(value):
            raise serializers.ValidationError('Duplicate template language detected')
        return value

    def to_representation(self, instance):
        self.context.update({'template': instance})
        return super().to_representation(instance)

    def export_files(self) -> Iterable[tuple[str, File]]:
        self.context.update({'template': self.instance})
        imgf = self.fields['images']
        imgf.instance = list(imgf.get_attribute(self.instance).all())
        yield from imgf.export_files()

    def create(self, validated_data):
        old_id = validated_data.pop('id')
        images_data = validated_data.pop('images', [])
        translations_data = validated_data.pop('translations')
        instance = FindingTemplate(**{
            'source': SourceEnum.IMPORTED,
            'skip_post_create_signal': True,
        } | validated_data)
        instance.save_without_historical_record()
        self.context['template'] = instance
        for t in translations_data:
            is_main = t.pop('is_main', False)
            translation_instance = self.fields['translations'].child.create(t | {'template': instance})
            if is_main:
                instance.main_translation = translation_instance
        instance._history_type = '+'
        instance.save()
        del instance._history_type

        self.context.update({'template': instance, 'template_id': old_id})
        self.fields['images'].create(images_data)

        sysreptor_signals.post_create.send(sender=instance.__class__, instance=instance)
        return instance


class UploadedImageExportImportSerializer(FileExportImportSerializer):
    class Meta(FileExportImportSerializer.Meta):
        model = UploadedImage

    def get_linked_object(self):
        return self.context['project']

    def is_file_referenced(self, f):
        return self.get_linked_object().is_file_referenced(f, findings=True, sections=True, notes=self.context.get('export_all', True))

    def get_path_in_archive(self, name):
        # Get ID of old project_type from archive
        return str(self.context.get('project_id') or self.get_linked_object().id) + '-images/' + name


class UploadedProjectFileExportImportSerializer(FileExportImportSerializer):
    class Meta(FileExportImportSerializer.Meta):
        model = UploadedProjectFile

    def get_linked_object(self):
        return self.context['project']

    def get_path_in_archive(self, name):
        # Get ID of old project_type from archive
        return str(self.context.get('project_id') or self.get_linked_object().id) + '-files/' + name


class UploadedAssetExportImportSerializer(FileExportImportSerializer):
    class Meta(FileExportImportSerializer.Meta):
        model = UploadedAsset

    def get_linked_object(self):
        return self.context['project_type']

    def get_path_in_archive(self, name):
        # Get ID of old project_type from archive
        return str(self.context.get('project_type_id') or self.get_linked_object().id) + '-assets/' + name


class ProjectTypeExportImportSerializerV1(ExportImportSerializer):
    format = FormatField('projecttypes/v1')
    assets = UploadedAssetExportImportSerializer(many=True)
    finding_fields = serializers.DictField()
    finding_field_order = serializers.ListField(child=serializers.CharField())
    report_fields = serializers.DictField()
    report_sections = serializers.ListField(child=serializers.DictField())

    class Meta:
        model = ProjectType
        fields = [
            'format', 'id', 'created', 'updated',
            'name', 'language', 'status', 'tags',
            'report_fields', 'report_sections',
            'finding_fields', 'finding_field_order', 'finding_ordering',
            'default_notes',
            'report_template', 'report_styles', 'report_preview_data',
            'assets',
        ]
        extra_kwargs = {
            'id': {'read_only': False},
            'created': {'read_only': False, 'required': False},
            'status': {'required': False, 'default': ProjectTypeStatus.FINISHED},
        }

    def create(self, validated_data):
        old_id = validated_data.pop('id')
        assets = validated_data.pop('assets', [])

        # Load old field definition format
        try:
            finding_fields = serialize_field_definition(parse_field_definition_legacy(
                field_dict=validated_data.pop('finding_fields', {}),
                field_order=validated_data.pop('finding_field_order', []),
            ))
            report_fields = parse_field_definition_legacy(field_dict=validated_data.pop('report_fields', {}))
            report_sections = validated_data.pop('report_sections', [])
            for section_data in report_sections:
                section_data['fields'] = serialize_field_definition(FieldDefinition(fields=[report_fields[f_id] for f_id in section_data['fields']]))
        except Exception as ex:
            raise serializers.ValidationError('Invalid field definition') from ex

        project_type = super().create({
            'source': SourceEnum.IMPORTED,
            'finding_fields': finding_fields,
            'report_sections': report_sections,
            'skip_post_create_signal': True,
        } | validated_data)
        project_type.full_clean()

        self.context.update({'project_type': project_type, 'project_type_id': old_id})
        self.fields['assets'].create(assets)

        sysreptor_signals.post_create.send(sender=project_type.__class__, instance=project_type)
        return project_type


class ProjectTypeExportImportSerializerV2(ExportImportSerializer):
    format = FormatField('projecttypes/v2')
    assets = UploadedAssetExportImportSerializer(many=True)

    class Meta:
        model = ProjectType
        fields = [
            'format', 'id', 'created', 'updated',
            'name', 'language', 'status', 'tags',
            'report_sections', 'finding_fields', 'finding_ordering',
            'default_notes',
            'report_template', 'report_styles', 'report_preview_data',
            'assets',
        ]
        extra_kwargs = {
            'id': {'read_only': False},
            'created': {'read_only': False, 'required': False},
            'status': {'required': False, 'default': ProjectTypeStatus.FINISHED},
        }

    def to_representation(self, instance):
        self.context.update({'project_type': instance})
        return super().to_representation(instance)

    def export_files(self) -> Iterable[tuple[str, File]]:
        af = self.fields['assets']
        self.context.update({'project_type': self.instance})
        af.instance = list(af.get_attribute(self.instance).all())
        yield from af.export_files()

    def create(self, validated_data):
        old_id = validated_data.pop('id')
        assets = validated_data.pop('assets', [])
        project_type = super().create({
            'source': SourceEnum.IMPORTED,
            'skip_post_create_signal': True,
        } | validated_data)
        self.context.update({'project_type': project_type, 'project_type_id': old_id})
        self.fields['assets'].create(assets)
        sysreptor_signals.post_create.send(sender=project_type.__class__, instance=project_type)
        return project_type


class CommentAnswerExportImportSerializer(ExportImportSerializer):
    user = RelatedUserIdExportImportSerializer()

    class Meta:
        model = CommentAnswer
        fields = ['id', 'created', 'updated', 'user', 'text']
        extra_kwargs = {'created': {'read_only': False, 'required': False}}


class CommentExportImportSerializer(ExportImportSerializer):
    user = RelatedUserIdExportImportSerializer()
    answers = CommentAnswerExportImportSerializer(many=True)
    text_range = TextRangeSerializer(allow_null=True)
    path = serializers.CharField(source='path_absolute')

    class Meta:
        model = Comment
        fields = [
            'id', 'created', 'updated', 'user', 'path',
            'text_range', 'text_original', 'text', 'answers',
        ]
        extra_kwargs = {'created': {'read_only': False, 'required': False}}

    def get_obj_and_path(self, path_absolute):
        path_parts = path_absolute.split('.')
        if len(path_parts) < 4 or path_parts[0] not in ['findings', 'sections'] or path_parts[2] != 'data':
            raise serializers.ValidationError('Invalid path')

        obj = None
        if path_parts[0] == 'findings':
            obj = next(filter(lambda f: str(f.finding_id) == path_parts[1], self.context['project'].findings.all()), None)
        elif path_parts[0] == 'sections':
            obj = next(filter(lambda s: str(s.section_id) == path_parts[1], self.context['project'].sections.all()), None)
        if not obj:
            raise serializers.ValidationError('Invalid path')

        try:
            get_field_value_and_definition(data=obj.data, definition=obj.field_definition, path=path_parts[3:])
        except KeyError as ex:
            raise serializers.ValidationError('Invalid path') from ex

        return obj, '.'.join(path_parts[2:])

    def create(self, validated_data):
        obj, path = self.get_obj_and_path(validated_data.pop('path_absolute'))

        answers = validated_data.pop('answers', [])
        comment = super().create(validated_data | {
            'path': path,
            'finding': obj if isinstance(obj, PentestFinding) else None,
            'section': obj if isinstance(obj, ReportSection) else None,
        })
        CommentAnswer.objects.bulk_create([CommentAnswer(comment=comment, **a) for a in answers])
        return comment


class PentestFindingExportImportSerializer(ExportImportSerializer):
    id = serializers.UUIDField(source='finding_id')
    assignee = RelatedUserIdExportImportSerializer()
    template = OptionalPrimaryKeyRelatedField(queryset=FindingTemplate.objects.all(), source='template_id')
    data = serializers.DictField()

    class Meta:
        model = PentestFinding
        fields = [
            'id', 'created', 'updated', 'assignee', 'status', 'template', 'order', 'data',
        ]
        extra_kwargs = {'created': {'read_only': False, 'required': False}}

    def create(self, validated_data):
        project = self.context['project']
        data = validated_data.pop('data', {})
        template = validated_data.pop('template_id', None)

        return PentestFinding.objects.create(**{
            'project': project,
            'template_id': template.id if template else None,
            'data': ensure_defined_structure(
                value=data,
                definition=project.project_type.finding_fields_obj,
                handle_undefined=HandleUndefinedFieldsOptions.FILL_NONE,
                include_unknown=True),
        } | validated_data)


class ReportSectionExportImportSerializer(ExportImportSerializer):
    id = serializers.CharField(source='section_id')
    assignee = RelatedUserIdExportImportSerializer()

    class Meta:
        model = ReportSection
        fields = [
            'id', 'created', 'updated', 'assignee', 'status',
        ]
        extra_kwargs = {'created': {'read_only': False, 'required': False}}

    def update(self, instance, validated_data):
        instance.skip_history_when_saving = True
        out = super().update(instance, validated_data)
        del instance.skip_history_when_saving

        # Add changes to previous history record to have a clean history timeline (just one entry for import)
        merge_with_previous_history(instance)

        return out


class NotebookPageExportImportSerializer(ExportImportSerializer):
    id = serializers.UUIDField(source='note_id')
    parent = serializers.UUIDField(source='parent.note_id', allow_null=True, required=False)

    class Meta:
        model = ProjectNotebookPage
        fields = [
            'id', 'created', 'updated',
            'title', 'text', 'checked', 'icon_emoji',
            'order', 'parent',
        ]
        extra_kwargs = {
            'created': {'read_only': False, 'required': False},
            'icon_emoji': {'required': False},
        }


class ProjectNotebookPageExportImportSerializer(NotebookPageExportImportSerializer):
    assignee = RelatedUserIdExportImportSerializer()

    class Meta(NotebookPageExportImportSerializer.Meta):
        fields = NotebookPageExportImportSerializer.Meta.fields + ['assignee']
        extra_kwargs = NotebookPageExportImportSerializer.Meta.extra_kwargs | {
            'assignee': {'required': False},
        }


class NotebookPageListExportImportSerializer(serializers.ListSerializer):
    @property
    def linked_object(self):
        if project := self.context.get('project'):
            return project
        elif user := self.context.get('user'):
            return user
        else:
            raise serializers.ValidationError('Missing project or user reference')

    def create_instance(self, validated_data):
        note_data = omit_keys(validated_data, ['parent'])
        if isinstance(self.linked_object, PentestProject):
            return ProjectNotebookPage(project=self.linked_object, **note_data)
        else:
            return UserNotebookPage(user=self.linked_object, **note_data)

    def create(self, validated_data):
        # Check for note ID collisions and update note_id on collision
        existing_instances = list(self.linked_object.notes.all())
        existing_ids = set(map(lambda n: n.note_id, existing_instances))
        for n in validated_data:
            if n['note_id'] in existing_ids:
                old_id = n['note_id']
                new_id = uuid4()
                n['note_id'] = new_id
                for cn in validated_data:
                    if cn.get('parent', {}).get('note_id') == old_id:
                        cn['parent']['note_id'] = new_id

        # Create instances
        instances = [self.create_instance(d) for d in validated_data]
        for i, d in zip(instances, validated_data):
            if d.get('parent'):
                i.parent = next(filter(lambda e: e.note_id == d.get('parent', {}).get('note_id'), instances), None)
        ProjectNotebookPage.objects.check_parent_and_order(instances)

        # Update order to new top-level notes: append to end after existing notes
        existing_toplevel_count = len([n for n in existing_instances if not n.parent])
        for n in instances:
            if not n.parent_id:
                n.order += existing_toplevel_count

        bulk_create_with_history(ProjectNotebookPage if isinstance(self.linked_object, PentestProject) else UserNotebookPage, instances)
        return instances


class PentestProjectExportImportSerializerV1(ExportImportSerializer):
    format = FormatField('projects/v1')
    members = ProjectMemberListExportImportSerializer(source='*', required=False)
    pentesters = ProjectMemberListExportImportSerializer(required=False, write_only=True)
    project_type = ProjectTypeExportImportSerializerV1()
    report_data = serializers.DictField(source='data')
    sections = ReportSectionExportImportSerializer(many=True)
    findings = PentestFindingExportImportSerializer(many=True)
    notes = NotebookPageListExportImportSerializer(child=ProjectNotebookPageExportImportSerializer(), required=False)
    images = UploadedImageExportImportSerializer(many=True)
    files = UploadedProjectFileExportImportSerializer(many=True, required=False)
    comments = CommentExportImportSerializer(many=True, required=False)

    class Meta:
        model = PentestProject
        fields = [
            'format', 'id', 'created', 'updated',
            'name', 'language', 'tags', 'override_finding_order', 'report_data',
            'members', 'pentesters', 'project_type',
            'sections', 'findings', 'notes', 'images', 'files', 'comments',
        ]
        extra_kwargs = {
            'id': {'read_only': False},
            'created': {'read_only': False, 'required': False},
            'tags': {'required': False},
        }

    def get_fields(self):
        fields = super().get_fields()
        if not self.context.get('export_all', True):
            del fields['notes']
            del fields['files']
        return fields

    def to_representation(self, instance):
        self.context.update({'project': instance})
        return super().to_representation(instance)

    def export_files(self) -> Iterable[tuple[str, File]]:
        self.fields['project_type'].instance = self.instance.project_type
        yield from self.fields['project_type'].export_files()

        self.context.update({'project': self.instance})

        imgf = self.fields['images']
        imgf.instance = list(imgf.get_attribute(self.instance).all())
        yield from imgf.export_files()

        if ff := self.fields.get('files'):
            ff.instance = list(ff.get_attribute(self.instance).all())
            yield from ff.export_files()

    def create(self, validated_data):
        old_id = validated_data.pop('id')
        members = validated_data.pop('members', validated_data.pop('pentesters', []))
        project_type_data = validated_data.pop('project_type', {})
        sections = validated_data.pop('sections', [])
        findings = validated_data.pop('findings', [])
        notes = validated_data.pop('notes', [])
        report_data = validated_data.pop('data', {})
        images_data = validated_data.pop('images', [])
        files_data = validated_data.pop('files', [])
        comments_data = validated_data.pop('comments', [])

        project_type = self.fields['project_type'].create(project_type_data | {
            'source': SourceEnum.IMPORTED_DEPENDENCY,
        })
        project = super().create(validated_data | {
            'project_type': project_type,
            'imported_members': list(filter(lambda u: isinstance(u, dict), members)),
            'source': SourceEnum.IMPORTED,
            'unknown_custom_fields': ensure_defined_structure(
                value=report_data,
                definition=project_type.all_report_fields_obj,
                handle_undefined=HandleUndefinedFieldsOptions.FILL_NONE,
                include_unknown=True,
            ),
            'skip_post_create_signal': True,
        })
        project_type.linked_project = project
        project_type.save()

        member_infos = list(filter(lambda u: isinstance(u, ProjectMemberInfo), members))
        for mi in member_infos:
            mi.project = project
        bulk_create_with_history(ProjectMemberInfo, member_infos)

        self.context.update({'project': project, 'project_id': old_id})

        for section in project.sections.all():
            if section_data := next(filter(lambda s: s.get('section_id') == section.section_id, sections), None):
                self.fields['sections'].child.update(section, section_data)

        self.fields['findings'].create(findings)
        self.fields['notes'].create(notes)
        self.fields['images'].create(images_data)
        self.fields['files'].create(files_data)
        self.fields['comments'].create(comments_data)

        sysreptor_signals.post_create.send(sender=project.__class__, instance=project)

        return project


class PentestProjectExportImportSerializerV2(PentestProjectExportImportSerializerV1):
    format = FormatField('projects/v2')
    project_type = ProjectTypeExportImportSerializerV2()


class NotesImageExportImportSerializer(FileExportImportSerializer):
    class Meta(FileExportImportSerializer.Meta):
        model = UploadedImage

    def get_model_class(self):
        return UploadedImage if isinstance(self.get_linked_object(), PentestProject) else UploadedUserNotebookImage

    def get_linked_object(self):
        if project := self.context.get('project'):
            return project
        elif user := self.context.get('user'):
            return user
        else:
            raise serializers.ValidationError('Missing project or user reference')

    def get_path_in_archive(self, name):
        return str(self.context.get('import_id') or self.get_linked_object().id) + '-images/' + name

    def is_file_referenced(self, f):
        if isinstance(self.get_linked_object(), PentestProject):
            return self.get_linked_object().is_file_referenced(f, findings=False, sections=False, notes=True)
        else:
            return self.get_linked_object().is_file_referenced(f)


class NotesFileExportImportSerializer(FileExportImportSerializer):
    class Meta(FileExportImportSerializer.Meta):
        model = UploadedProjectFile

    def get_model_class(self):
        return UploadedProjectFile if isinstance(self.get_linked_object(), PentestProject) else UploadedUserNotebookFile

    def get_linked_object(self):
        if project := self.context.get('project'):
            return project
        elif user := self.context.get('user'):
            return user
        else:
            raise serializers.ValidationError('Missing project or user reference')

    def get_path_in_archive(self, name):
        return str(self.context.get('import_id') or self.get_linked_object().id) + '-files/' + name


class NotesExportImportSerializer(ExportImportSerializer):
    format = FormatField('notes/v1')
    id = serializers.UUIDField()
    notes = NotebookPageListExportImportSerializer(child=NotebookPageExportImportSerializer())
    images = FileListExportImportSerializer(child=NotesImageExportImportSerializer(), required=False)
    files = FileListExportImportSerializer(child=NotesFileExportImportSerializer(), required=False)

    class Meta:
        fields = ['format', 'id', 'notes', 'images', 'files']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.instance, PentestProject):
            self.context['project'] = self.instance
        elif isinstance(self.instance, PentestUser):
            self.context['user'] = self.instance
        self.Meta.model = PentestProject if self.context.get('project') else PentestUser

    def export(self):
        out = super().export()
        # Set parent_id = None for exported child-notes
        exported_ids = set(map(lambda n: n['id'], out['notes']))
        for n in out['notes']:
            if n['parent'] and n['parent'] not in exported_ids:
                n['parent'] = None
        return out

    def export_files(self) -> Iterable[tuple[str, File]]:
        imgf = self.fields['images']
        imgf.instance = list(imgf.get_attribute(self.instance).all())
        yield from imgf.export_files()

        ff = self.fields['files']
        ff.instance = list(ff.get_attribute(self.instance).all())
        yield from ff.export_files()

    def create(self, validated_data):
        # Check for file name collisions and rename files and update references
        linked_object = self.context.get('project') or self.context.get('user')
        existing_images = set(map(lambda i: i.name, linked_object.images.all()))
        for ii in validated_data['images']:
            i_name = ii['name']
            while ii['name'] in existing_images:
                ii['name'] = UploadedImage.objects.randomize_name(i_name)
                ii['name_internal'] = i_name
            if i_name != ii['name']:
                for n in validated_data['notes']:
                    n['text'] = n['text'].replace(f'/images/name/{i_name}', f'/images/name/{ii["name"]}')

        existing_files = set(map(lambda f: f.name, linked_object.files.all()))
        for fi in validated_data['files']:
            f_name = fi['name']
            while fi['name'] in existing_files:
                fi['name'] = UploadedProjectFile.objects.randomize_name(f_name)
                fi['name_internal'] = f_name
            if f_name != fi['name']:
                for n in validated_data['notes']:
                    n['text'] = n['text'].replace(f'/files/name/{f_name}', f'/files/name/{fi["name"]}')

        # Import notes
        notes = self.fields['notes'].create(validated_data['notes'])

        # Import images and files
        self.context.update({'import_id': validated_data['id']})
        self.fields['images'].create(validated_data.get('images', []))
        self.fields['files'].create(validated_data.get('files', []))

        return notes
