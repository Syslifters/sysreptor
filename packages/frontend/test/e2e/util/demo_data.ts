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

  // Add an Id to the correct array
  // and save json file
  addId(type: DemoDataType, id: string | undefined) {
    if (!id) {
      return;
    }
    switch (type) {
      case DemoDataType.Project:
        this.projects.push(id);
        break;
      case DemoDataType.Design:
        this.designs.push(id);
        break;
      case DemoDataType.Template:
        this.templates.push(id);
        break;
    };
    fs.writeFileSync('/app/packages/frontend/test/e2e/demodata/projects.json', JSON.stringify(this.projects), 'utf8');
    fs.writeFileSync('/app/packages/frontend/test/e2e/demodata/designs.json', JSON.stringify(this.designs), 'utf8');
    fs.writeFileSync('/app/packages/frontend/test/e2e/demodata/templates.json', JSON.stringify(this.templates), 'utf8');
  }

  constructor() {
    this.projects = JSON.parse(fs.readFileSync('/app/packages/frontend/test/e2e/demodata/projects.json', 'utf8'));
    this.designs = JSON.parse(fs.readFileSync('/app/packages/frontend/test/e2e/demodata/designs.json', 'utf8'));
    this.templates = JSON.parse(fs.readFileSync('/app/packages/frontend/test/e2e/demodata/templates.json', 'utf8'));
  }
}
