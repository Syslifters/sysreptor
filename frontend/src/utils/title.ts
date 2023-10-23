import { PentestProject } from "~/utils/types";

export function getTitle(title?: string|null, route?: ReturnType<typeof useRoute>): string|null {
  return title || (route?.meta?.title as string|undefined) || null;
}

export function rootTitleTemplate(title?: string|null, route?: ReturnType<typeof useRoute>): string {
  const notificationStore = useNotificationStore();
  title = getTitle(title, route);
  return (title ? title + ' | ' : '') + 'SysReptor' + (notificationStore.unreadNotificationCount > 0 ? ` (${notificationStore.unreadNotificationCount})` : '');
}

export function projectTitleTemplate(project?: PentestProject, title?: string|null, route?: ReturnType<typeof useRoute>) {
  title = getTitle(title, route);
  return rootTitleTemplate((title ? `${title} | ` : '') + (project?.name || ''));
}

export function profileTitleTemplate(title?: string|null, route?: ReturnType<typeof useRoute>) {
  title = getTitle(title, route);
  return rootTitleTemplate((title ? title + ' | ' : '') + 'Profile');
}

export function userNotesTitleTemplate(title?: string|null, route?: ReturnType<typeof useRoute>) {
  title = getTitle(title, route);
  return rootTitleTemplate((title ? title + ' | ' : '') + 'Notes');
}
