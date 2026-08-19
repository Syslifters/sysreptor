import { urlJoin } from "@base/utils/helpers";
import type { ShareInfo } from "#imports";

export type NoteShareInfoContext = {
  noteId: string;
  projectId?: string;
  userId?: string;
};

type NoteShareInfosCacheEntry = {
  shareInfos: ShareInfo[];
  isLoading: boolean;
};

const fetchInProgress = new Map<string, Promise<ShareInfo[]>>();

function getCacheKey(options: NoteShareInfoContext): string | null {
  if (options.projectId) {
    return `project:${options.projectId}:note:${options.noteId}`;
  }
  if (options.userId) {
    return `user:${options.userId}:note:${options.noteId}`;
  }
  return null;
}

function getShareInfosBaseUrl(options: NoteShareInfoContext): string | null {
  if (options.projectId) {
    return `/api/v1/pentestprojects/${options.projectId}/notes/${options.noteId}/shareinfos/`;
  }
  if (options.userId) {
    return `/api/v1/pentestusers/${options.userId}/notes/${options.noteId}/shareinfos/`;
  }
  return null;
}

export const useNoteShareInfoStore = defineStore('noteshareinfos', {
  state: () => ({
    entries: {} as Record<string, NoteShareInfosCacheEntry>,
  }),
  actions: {
    shareInfosFor(ctx: NoteShareInfoContext): ShareInfo[] {
      const key = getCacheKey(ctx);
      return key ? (this.entries[key]?.shareInfos ?? []) : [];
    },
    isLoadingFor(ctx: NoteShareInfoContext): boolean {
      const key = getCacheKey(ctx);
      return key ? (this.entries[key]?.isLoading ?? false) : false;
    },
    ensureEntry(key: string): NoteShareInfosCacheEntry {
      if (!this.entries[key]) {
        this.entries[key] = { shareInfos: [], isLoading: false };
      }
      return this.entries[key]!;
    },
    replaceShareInfo(key: string, shareInfo: ShareInfo) {
      const entry = this.entries[key];
      if (!entry) {
        return;
      }
      entry.shareInfos = entry.shareInfos.map(si => si.id === shareInfo.id ? shareInfo : si);
    },
    addShareInfo(key: string, shareInfo: ShareInfo) {
      const entry = this.ensureEntry(key);
      entry.shareInfos = [shareInfo, ...entry.shareInfos];
    },
    async fetchShareInfos(ctx: NoteShareInfoContext): Promise<ShareInfo[]> {
      const key = getCacheKey(ctx);
      const baseUrl = getShareInfosBaseUrl(ctx);
      if (!key || !baseUrl) {
        return [];
      }

      const existing = fetchInProgress.get(key);
      if (existing) {
        return await existing;
      }

      const entry = this.ensureEntry(key);
      entry.isLoading = true;
      const promise = $fetch<ShareInfo[]>(baseUrl, { method: 'GET' }).then((shareInfos) => {
        const current = this.entries[key];
        if (current) {
          current.shareInfos = shareInfos;
        }
        return shareInfos;
      }).finally(() => {
        fetchInProgress.delete(key);
        const current = this.entries[key];
        if (current) {
          current.isLoading = false;
        }
      });
      fetchInProgress.set(key, promise);
      return await promise;
    },
    async updateShareInfo(ctx: NoteShareInfoContext, shareInfo: ShareInfo): Promise<ShareInfo> {
      const key = getCacheKey(ctx);
      const baseUrl = getShareInfosBaseUrl(ctx);
      if (!key || !baseUrl) {
        return shareInfo;
      }
      const updated = await $fetch<ShareInfo>(urlJoin(baseUrl, `${shareInfo.id}/`), {
        method: 'PATCH',
        body: shareInfo,
      });
      this.replaceShareInfo(key, updated);
      return updated;
    },
    async createShareInfo(ctx: NoteShareInfoContext, data: ShareInfo): Promise<ShareInfo> {
      const key = getCacheKey(ctx);
      const baseUrl = getShareInfosBaseUrl(ctx);
      if (!key || !baseUrl) {
        throw new Error('Cannot create share info without project or user context');
      }
      const created = await $fetch<ShareInfo>(baseUrl, {
        method: 'POST',
        body: data,
      });
      this.addShareInfo(key, created);
      return created;
    },
    async approvePendingFiles(ctx: NoteShareInfoContext, shareInfo: ShareInfo, fileIds: string[]): Promise<ShareInfo> {
      const key = getCacheKey(ctx);
      const baseUrl = getShareInfosBaseUrl(ctx);
      if (!key || !baseUrl) {
        throw new Error('Cannot approve pending files without project or user context');
      }
      const updated = await $fetch<ShareInfo>(urlJoin(baseUrl, `${shareInfo.id}/approve-pending-files/`), {
        method: 'POST',
        body: { file_ids: fileIds },
      });
      this.replaceShareInfo(key, updated);
      return updated;
    },
  },
});
