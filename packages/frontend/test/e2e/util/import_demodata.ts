/* eslint-disable no-console */
import fs from 'fs';
import path from 'path';
import type { Page } from '@playwright/test';
import { $fetch } from 'ofetch';

export async function importFile (apiUrl: string, filePath: string, cookies: any) {
  const file = await fs.openAsBlob(filePath);
  const form = new FormData();
  form.append('file', file, filePath.split('/').at(-1));
  if(filePath.match(/designs/)) {
    form.append('scope', 'global');
  }

  return await $fetch(apiUrl, {
    method: 'POST',
    headers: { 
      'Cookie': cookies.map(c => `${c.name}=${c.value}`).join('; ')
    },
    body: form,
  });
};

export async function downloadDemoData() {
  const urls = [
    'https://docs.sysreptor.com/assets/demo-projects.tar.gz',
    'https://docs.sysreptor.com/assets/demo-designs.tar.gz',
    'https://docs.sysreptor.com/assets/demo-templates.tar.gz'
  ];

  const filePaths: string[] = [
    './test/e2e/demodata/demo-projects.tar.gz',
    './test/e2e/demodata/demo-designs.tar.gz',
    './test/e2e/demodata/demo-templates.tar.gz'
  ];

  for (let i = 0; i < urls.length; i++) {
    const filePath = filePaths[i];
    const url = urls[i];

    if (!url || !filePath) {
      throw new Error(`URL or file path is not defined for ${url}`);
    }

    if (fs.existsSync(filePath)) {
      console.log(`File ${filePath} already exists, skipping download`);
      continue;
    }

    const response = await $fetch<ArrayBuffer>(url, { method: 'GET', responseType: 'arrayBuffer' as any });

    // Ensure directory exists
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // Store response to filePath
    fs.writeFileSync(filePath, Buffer.from(response));
  }
};

// Makes requests to import demo data and saves the IDs of the imported items to files
export async function importDemoData(page: Page, baseURL: string) {
  const state = await page.context().storageState();

  const importSpec = [
    {
      url: new URL('/api/v1/pentestprojects/import/', baseURL),
      filePath: './test/e2e/demodata/demo-projects.tar.gz',
      outputFile: './test/e2e/demodata/projects.json',
    },
    {
      url: new URL('/api/v1/findingtemplates/import/', baseURL),
      filePath: './test/e2e/demodata/demo-templates.tar.gz',
      outputFile: './test/e2e/demodata/templates.json',
    },
    {
      url: new URL('/api/v1/projecttypes/import/', baseURL),
      filePath: './test/e2e/demodata/demo-designs.tar.gz',
      outputFile: './test/e2e/demodata/designs.json',
    }
  ];

  async function performImport(spec) {
    const data = await importFile(spec.url.toString(), spec.filePath, state.cookies);
    const ids = data.map((item: { id: string }) => item.id);
    console.log(`Imported ${ids.length} items from ${spec.url}`);
    fs.writeFileSync(spec.outputFile, JSON.stringify(ids, null, 2));

    if (fs.existsSync(spec.filePath)) {
      fs.unlinkSync(spec.filePath);
    }
  }

  await Promise.all(importSpec.map(performImport));
};
