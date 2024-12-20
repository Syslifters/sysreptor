import fs from 'fs';

export enum DemoDataType {
  Project = 'project',
  Design = 'design',
  Template = 'template',
}
export class DemoDataState {
  projects: string[];
  designs: string[];
  templates: string[];

  // Add an id to the list of ids for a given type
  addId(type: DemoDataType, id: string | undefined) {
    if (!id) {
      return;
    }
    switch (type) {
      case DemoDataType.Project:
        this.projects.push(id);
        fs.writeFileSync('/app/packages/frontend/test/e2e/demodata/projects.json', JSON.stringify(this.projects), 'utf8');
        break;
      case DemoDataType.Design:
        this.designs.push(id);
        fs.writeFileSync('/app/packages/frontend/test/e2e/demodata/designs.json', JSON.stringify(this.designs), 'utf8');
        break;
      case DemoDataType.Template:
        this.templates.push(id);
        fs.writeFileSync('/app/packages/frontend/test/e2e/demodata/templates.json', JSON.stringify(this.templates), 'utf8');
        break;
    };
  }

  constructor() {
    this.projects = JSON.parse(fs.readFileSync('/app/packages/frontend/test/e2e/demodata/projects.json', 'utf8'));
    this.designs = JSON.parse(fs.readFileSync('/app/packages/frontend/test/e2e/demodata/designs.json', 'utf8'));
    this.templates = JSON.parse(fs.readFileSync('/app/packages/frontend/test/e2e/demodata/templates.json', 'utf8'));
  }
}
