import urlJoin from "url-join";
import { $fetch } from 'ofetch';
import { encode as base64encode, decode as base64decode } from "base64-arraybuffer";

import { 
  CaptureUpdateAction,
  newElementWith,
} from "@excalidraw/excalidraw";
import { BinaryFileData, ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";
import { FileId, InitializedExcalidrawImageElement } from "@excalidraw/excalidraw/element/types";
import { isInitializedImageElement } from "./utils";
import { ElementUpdate } from "@excalidraw/excalidraw/element/mutateElement";


export const IMAGE_MIME_TYPES = {
    svg: "image/svg+xml",
    png: "image/png",
    jpg: "image/jpeg",
    gif: "image/gif",
    webp: "image/webp",
    bmp: "image/bmp",
    ico: "image/x-icon",
    avif: "image/avif",
    jfif: "image/jfif",
};


export class FileManager {
  excalidrawAPI: ExcalidrawImperativeAPI;
  private imageApiBaseUrl: string;

  private fetchingFiles: Set<FileId> = new Set();
  private savingFiles: Set<FileId> = new Set();
  private savedFiles: Set<FileId> = new Set();
  private erroredFiles: Set<FileId> = new Set(); 

  constructor(options: {
    excalidrawAPI: ExcalidrawImperativeAPI
    imageApiBaseUrl: string;
  }) {
    this.excalidrawAPI = options.excalidrawAPI;

    const serverUrl = process.env.NODE_ENV === 'development' ?
      'http://localhost:3000/' : window.location.origin;
    this.imageApiBaseUrl = urlJoin(serverUrl, options.imageApiBaseUrl);
  }

  isFileTracked(fileId: FileId): boolean {
    return this.fetchingFiles.has(fileId) || this.savedFiles.has(fileId) || this.erroredFiles.has(fileId) || this.savingFiles.has(fileId);
  }

  updateImageElements(getUpdateData: (e: InitializedExcalidrawImageElement) => ElementUpdate<InitializedExcalidrawImageElement>|null) {
    this.excalidrawAPI.updateScene({
      elements: this.excalidrawAPI.getSceneElementsIncludingDeleted().map((element) => {
        if (isInitializedImageElement(element)) {
          const update = getUpdateData(element);
          if (update) {
            return newElementWith(element, update);
          }
        }
        return element;
      }),
      captureUpdate: CaptureUpdateAction.NEVER,
    });
  }

  async getFiles() {
    const fileIds = this.excalidrawAPI.getSceneElements()
      .filter((element) => {
        return (
          isInitializedImageElement(element) &&
          !this.isFileTracked(element.fileId) &&
          !element.isDeleted
        );
      })
      .map((element) => (element as InitializedExcalidrawImageElement).fileId);
    
    for (const id of fileIds) {
      this.fetchingFiles.add(id);
    }

    try {
      const loadedFiles = [] as BinaryFileData[];
      const erroredFiles = [] as FileId[];
      await Promise.allSettled(fileIds.map((id) => Promise.resolve((async () => {
        try {
          const fileData = await this.fetchFileFromAPI(id);
          loadedFiles.push(fileData);
        } catch {
          erroredFiles.push(id);
        }
      })())));

      // Add files to scene
      this.excalidrawAPI.addFiles(loadedFiles);
      if (erroredFiles.length > 0) {
        this.updateImageElements(e => 
            loadedFiles.some(f => f.id === e.fileId) ? { status: 'saved' } :
            // erroredFiles.includes(e.fileId) ? { status: 'error' } : 
            null);
      }

      return { loadedFiles, erroredFiles };
    } finally {
      for (const id of fileIds) {
        this.fetchingFiles.delete(id);
      }
    }
  }

  async fetchFileFromAPI(fileId: FileId): Promise<BinaryFileData> {
    try {
      const res = await fetch(urlJoin(this.imageApiBaseUrl, '/name/', fileId), {
        method: 'GET',
      });
      if (!res.ok) {
        throw new Error(`Failed to fetch file ${fileId}: ${res.status} ${res.statusText}`);
      }
      const mimeType = (res.headers.get('Content-Type') || 'application/octet-stream') as BinaryFileData['mimeType']
      const fileData = base64encode(await res.arrayBuffer());
      
      this.savedFiles.add(fileId);
      return {
        id: fileId,
        mimeType,
        dataURL: `data:${mimeType};base64,${fileData}` as BinaryFileData['dataURL'],
        created: Date.now(),
        lastRetrieved: Date.now(),
      };
    } catch (error) {
      this.erroredFiles.add(fileId);
      throw error;
    } finally {
      this.fetchingFiles.delete(fileId);
    }
  }

  async saveFiles() {  
    const files = this.excalidrawAPI.getFiles();

    const newFiles = [];
    for (const e of this.excalidrawAPI.getSceneElements()) {
      if (isInitializedImageElement(e) && files[e.fileId] && !this.isFileTracked(e.fileId)) {
        newFiles.push(files[e.fileId]);
        this.savingFiles.add(e.fileId);
      }
    }
    
    try {
      await Promise.allSettled(newFiles.map(this.uploadFileToAPI.bind(this)));
    } finally {
      for (const file of newFiles) {
        this.savingFiles.delete(file.id);
      }
    }
  }

  async uploadFileToAPI(file: BinaryFileData) {
    try {
      const [prefix, fileDataB64] = file.dataURL.split(',', 2);
      if (!prefix.toLowerCase().includes('base64')) {
        throw new Error('Only base64 data URLs are supported');
      }
      const fileExtension = Object.entries(IMAGE_MIME_TYPES).find(([ext, mime]) => mime === file.mimeType)?.[0] || 'png';
      const form = new FormData();
      form.append('file', new File([base64decode(fileDataB64)], `${file.id}.${fileExtension}`, { type: file.mimeType }));

      const uploadedImage = await $fetch(this.imageApiBaseUrl, {
        method: 'POST',
        body: form,
      });

      // Update file ID to file name from response
      const newFileId = uploadedImage.name as FileId;
      this.savedFiles.delete(file.id);
      this.savedFiles.add(newFileId);
      this.excalidrawAPI.addFiles([{ ...file, id: newFileId }]);
      delete this.excalidrawAPI.getFiles()[file.id];
      this.updateImageElements(e => e.fileId === file.id ? {
        fileId: newFileId,
        status: 'saved',
      } : null);

      return uploadedImage;
    } catch (error) {
      /* eslint-disable-next-line no-console */
      console.error('Failed to upload excalidraw image', { error });
      this.erroredFiles.add(file.id);
      this.updateImageElements(e => e.fileId === file.id ? { status: 'error', isDeleted: true } : null);

      throw error;
    }
  }
}