from django.db.models.expressions import RawSQL
from django.template import TemplateSyntaxError
from rest_framework import serializers
from sysreptor.pentests.cvss import CVSSLevel
from sysreptor.pentests.models import (
    FindingTemplate,
    FindingTemplateTranslation,
    PentestFinding,
    PentestProject,
)
from sysreptor.utils.language import Language

from ..utils import render_template_string


class BaseImporter:
    id: str = None

    severity_mapping = {
        CVSSLevel.INFO: "🟢",
        CVSSLevel.LOW: "🔵",
        CVSSLevel.MEDIUM: "🟡",
        CVSSLevel.HIGH: "🟠",
        CVSSLevel.CRITICAL: "🔴",
    }

    def is_format(self, file):
        return False
    
    def parse_findings(self, files, project) -> list[dict]:
        return []

    def parse_notes(self, files) -> list[dict]:
        return []

    def get_all_finding_templates(self) -> list[FindingTemplate]:
        prefix = f'scanimport:{self.id}'
        # Use annotate with RawSQL to check if any tag in the array starts with prefix
        results = FindingTemplate.objects \
            .annotate(has_matching_tag=RawSQL("EXISTS (SELECT 1 FROM unnest(tags) AS tag WHERE tag LIKE %s)", [f'{prefix}%'])) \
            .filter(has_matching_tag=True) \
            .prefetch_related('translations')
        return list(results)
    
    def select_template_translation(self, template: FindingTemplate, language: Language|None = None, additional_info: dict|None = None) -> FindingTemplateTranslation:
        template.additional_info = additional_info or {}
        if language:
            for tr in getattr(template, '_translations', template.translations.all()):
                if tr.language == language:
                    return tr
        return template.main_translation

    def select_finding_template(self, templates: list[FindingTemplate], fallback: list[FindingTemplate], selector: str|None = None, language: Language|None = None) -> FindingTemplateTranslation:
        selector_base = f'scanimport:{self.id}'
        additional_info = {'search_path': [selector_base]}
        
        if selector:
            selector = selector_base + ':' + selector
            additional_info['search_path'].insert(0, selector)
        
        for tag in additional_info['search_path']:
            for t in templates + fallback:
                if tag in t.tags:
                    return self.select_template_translation(t, language, additional_info=additional_info)
        if fallback:
            return self.select_template_translation(fallback[0], language, additional_info=additional_info)
        raise ValueError(f"No suitable template found for importer '{self.id}' with selector '{selector}'.")
    
    def generate_finding_from_template(self, project: PentestProject, tr: FindingTemplateTranslation, data: dict):
        is_fallback = getattr(tr, 'is_fallback', False)
        f = PentestFinding(project=project, template_id=tr.template.id if tr.template and not is_fallback else None)
        f.template_info = getattr(tr.template, 'additional_info', {}) | {
            'is_fallback': is_fallback,
            'language': tr.language,
        }

        # Format finding data based on template
        f.update_data(data)
        for k, v in tr.data.items():
            if v and isinstance(v, str):
                try:
                    f.update_data({k: render_template_string(v, context=data)})
                except TemplateSyntaxError as ex:
                    template_identifier = (f'{self.id} fallback template' if getattr(tr, 'is_fallback', False) else f'template id="{self.id}"')
                    raise serializers.ValidationError(f'Template error in {template_identifier} with language="{tr.language}" field="{k}": {ex}') from ex
            elif v:
                f.update_data({k: v})
        
        return f
    

def fallback_template(tags: list[str], translations: list[FindingTemplateTranslation]) -> FindingTemplate:
    template = FindingTemplate(tags=tags)
    template.is_fallback = True
    template.main_translation = translations[0] if translations else None
    template._translations = translations

    for tr in translations:
        tr.is_fallback = True
        tr.template = template

    return template
        

class ImporterRegistry:
    importers = []

    def register(self, importer: BaseImporter):
        if self.get(importer.id):
            raise ValueError(f"Importer with name '{importer.id}' is already registered.")
        self.importers.append(importer)

    def unregister(self, importer: BaseImporter|str):
        if isinstance(importer, str):
            importer = self.get(importer)
        self.importers.remove(importer)

    def __getitem__(self, key):
        out = self.get(key)
        if not out:
            raise KeyError(f"Importer with name '{key}' not found.")
        return out
    
    def get(self, key, default=None):
        return next((imp for imp in self.importers if imp.id == key), default)
    
    def auto_detect_format(self, file) -> BaseImporter|None:
        for importer in self.importers:
            try:
                if importer.is_format(file):
                    return importer
            except Exception:
                pass
        return None


registry = ImporterRegistry()

