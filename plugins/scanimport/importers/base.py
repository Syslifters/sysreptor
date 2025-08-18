from django.db.models.expressions import RawSQL
from sysreptor.pentests.models import (
    FindingTemplate,
    FindingTemplateTranslation,
    PentestFinding,
    PentestProject,
    ProjectNotebookPage,
)
from sysreptor.utils.language import Language

from ..utils import render_template_string


class BaseImporter:
    id: str = None

    default_note: ProjectNotebookPage = None
    default_template: FindingTemplate = None

    def is_format(self, file):
        return False
    
    def parse_findings(self, file) -> list[dict]:
        pass

    def parse_notes(self, file) -> list[dict]:
        pass

    def get_all_finding_templates(self) -> list[FindingTemplate]:
        prefix = f'scanimport:{self.id}'
        # Use annotate with RawSQL to check if any tag in the array starts with prefix
        results = FindingTemplate.objects \
            .annotate(has_matching_tag=RawSQL("EXISTS (SELECT 1 FROM unnest(tags) AS tag WHERE tag LIKE %s)", [f'{prefix}%'])) \
            .filter(has_matching_tag=True) \
            .prefetch_related('translations')
        return list(results)
    
    def select_template_translation(self, template: FindingTemplate, language: Language|None = None) -> FindingTemplateTranslation:
        if language:
            for tr in getattr(template, '_translations', template.translations.all()):
                if tr.language == language:
                    return tr
        return template.main_translation

    def select_finding_template(self, templates: list[FindingTemplate], fallback: list[FindingTemplate], selector: str|None = None, language: Language|None = None) -> FindingTemplateTranslation:
        # TODO: naming convention for template tags "scanimport:burp" vs "burp"
        selector_base = f'scanimport:{self.id}'
        
        if selector:
            selector = selector_base + ':' + selector
            for t in templates + fallback:
                if selector in t.tags:
                    return self.select_template_translation(t, language)
        for t in templates + fallback:
            if selector_base in t.tags:
                return self.select_template_translation(t, language)
        if fallback:
            return self.select_template_translation(fallback[0], language)
        raise ValueError(f"No suitable template found for importer '{self.id}' with selector '{selector}'.")
    
    def generate_finding_from_template(self, project: PentestProject, tr: FindingTemplateTranslation, data: dict):
        f = PentestFinding(project=project, template_id=tr.template.id if tr.template and not getattr(tr, 'is_fallback', False) else None)
        f.update_data(data)
        
        # Format finding data based on template
        for k, v in tr.data.items():
            if v and isinstance(v, str):
                f.update_data({k: render_template_string(v, context=data)})
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

    def __getitem__(self, key):
        out = self.get(key)
        if not out:
            raise KeyError(f"Importer with name '{key}' not found.")
        return out
    
    def get(self, key, default=None):
        return next((imp for imp in self.importers if imp.id == key), default)
    
    def auto_detect_format(self, file):
        for importer in self.importers:
            try:
                if importer.is_format(file):
                    return importer
            except Exception:
                pass
        return None


registry = ImporterRegistry()

