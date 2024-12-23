/* eslint-disable no-console */
import type { Page } from '@playwright/test';
import FormData from 'form-data';
import fs from 'fs';
import fetch from 'node-fetch';

const importFile = async (url: string, filePath: string, headers: any) => {
  const file = fs.readFileSync(filePath);
  const body = new FormData();
  body.append('file', file, {
    filename: filePath.split('/').pop(),
    contentType: 'application/gzip'
  });
  console.log(filePath);
  if(filePath.match(/designs/)) {
    body.append('scope', 'global');
  }


  const formHeaders = body.getHeaders();
  const combinedHeaders = { ...headers, ...formHeaders };

  const response = await fetch(url, {
    method: 'POST',
    headers: combinedHeaders,
    body: body
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to import file: ${response.status} ${response.statusText}\n${errorText}`);
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  } else {
    const errorText = await response.text();
    throw new Error(`Unexpected response content type: ${contentType}\n${errorText}`);
  }
};

export const downloadDemoData = async () => {
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

  try {
    for (let i = 0; i < urls.length; i++) {
      const filePath = filePaths[i];
      const url = urls[i];

      if (url === undefined || filePath === undefined) {
        throw new Error(`URL or file path is not defined for ${url}`);
      }

      if (fs.existsSync(filePath)) {
        console.log(`File ${filePath} already exists, skipping download`);
        continue;
      }

      console.log(`Downloading ${url}...`);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to download ${url}: ${response.statusText}`);
      }

      // Chekc if directory exists
      const dir = './test/e2e/demodata/';
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, {
          recursive: true
        });
      }


      const fileStream = fs.createWriteStream(filePath);
      response.body?.pipe(fileStream);

      await new Promise((resolve, reject) => {
        fileStream.on('finish', resolve);
        fileStream.on('error', reject);
      });

      console.log(`Downloaded ${filePath}`);
    }
  } catch (error) {
    console.error('Error downloading files:', error);
  }
};

// Makes requests to import demo data and saves the IDs of the imported items to files
export const importDemoData = async (page: Page) => {
  const state = await page.context().storageState();
  const headers = {
    'Cookie': `csrftoken=${state.cookies.find(e => e.name == 'csrftoken')?.value}; sessionid=${state.cookies.find(e => e.name == 'sessionid')?.value}`
  };

  const urls = [
    'http://localhost:3000/api/v1/pentestprojects/import/',
    'http://localhost:3000/api/v1/findingtemplates/import/',
    'http://localhost:3000/api/v1/projecttypes/import/'
  ];

  const filePaths: string[] = [
    './test/e2e/demodata/demo-projects.tar.gz',
    './test/e2e/demodata/demo-templates.tar.gz',
    './test/e2e/demodata/demo-designs.tar.gz'
  ];

  const outputFiles = [
    './test/e2e/demodata/projects.json',
    './test/e2e/demodata/templates.json',
    './test/e2e/demodata/designs.json'
  ];

  try {
    const results = await Promise.all(urls.map((url, index) => importFile(url, filePaths[index]!, headers)));

    results.forEach((result: any, index) => {
      const ids = result.map((item: { id: string }) => item.id);
      console.log(`Imported ${ids.length} items from ${filePaths[index]}`);
      fs.writeFileSync(outputFiles[index]!, JSON.stringify(ids, null, 2));
    });

    // Delete the downloaded files
    filePaths.forEach((filePath) => {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        console.log(`Deleted ${filePath}`);
      }
    });
  } catch (error) {
    console.error('Error importing files:', error);
  }
};
