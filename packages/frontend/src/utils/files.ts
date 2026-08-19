import { last } from 'lodash-es';
import { urlJoin } from '@base/utils/helpers';
import { absoluteApiUrl } from '@base/utils/urls';
import {
  type PentestProject,
  type UploadedFileInfo,
  type User,
  UploadedFileType,
} from '#imports';

export type FileApiBaseUrls = {
  imagesBase: string;
  filesBase: string;
};

export function getFileApiBaseUrls(options: { project?: PentestProject | null, user?: User | null }): FileApiBaseUrls | null {
  const { project, user } = options;
  if (project) {
    return {
      imagesBase: `/api/v1/pentestprojects/${project.id}/images/`,
      filesBase: `/api/v1/pentestprojects/${project.id}/files/`,
    };
  } else if (user) {
    return {
      imagesBase: `/api/v1/pentestusers/${user.id}/notes/images/`,
      filesBase: `/api/v1/pentestusers/${user.id}/notes/files/`,
    };
  }
  return null;
}

export async function fetchUploadedFileById(imagesBase: string, filesBase: string, fileId: string): Promise<UploadedFileInfo> {
  try {
    return await $fetch<UploadedFileInfo>(urlJoin(imagesBase, `${fileId}/`), { method: 'GET' });
  } catch (error: any) {
    if (error?.status === 404 || error?.statusCode === 404) {
      return await $fetch<UploadedFileInfo>(urlJoin(filesBase, `${fileId}/`), { method: 'GET' });
    }
    throw error;
  }
}

export function isImageFile(file: UploadedFileInfo): boolean {
  if (file.resource_type === UploadedFileType.IMAGE) {
    return true;
  }
  return ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(last(file.name.split('.'))?.toLowerCase() || '');
}

export function filePreviewUrl(file: UploadedFileInfo, bases: FileApiBaseUrls): string {
  const base = isImageFile(file) ? bases.imagesBase : bases.filesBase;
  return absoluteApiUrl(urlJoin(base, `name/${encodeURIComponent(file.name)}/`));
}
