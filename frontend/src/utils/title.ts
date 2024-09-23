import type { ArchivedProject, Breadcrumbs, FindingTemplate, PentestProject, ProjectType, UserShortInfo } from "#imports";

type RouteType = ReturnType<typeof useRoute>;

export function getTitle(title?: string|null, route?: RouteType): string|null {
  return title || (route?.meta?.title as string|undefined) || null;
}

export function rootTitleTemplate(title?: string|null, route?: RouteType): string {
  const notificationStore = useNotificationStore();
  title = getTitle(title, route);
  return (title ? title + ' | ' : '') + 'SysReptor' + (notificationStore.unreadNotificationCount > 0 ? ` (${notificationStore.unreadNotificationCount})` : '');
}

export function projectTitleTemplate(project?: PentestProject, title?: string|null, route?: RouteType) {
  title = getTitle(title, route);
  return rootTitleTemplate((title ? `${title} | ` : '') + (project?.name || ''));
}

export function designTitleTemplate(projectType?: ProjectType, title?: string|null, route?: RouteType) {
  title = getTitle(title, route);
  return rootTitleTemplate((title ? `${title} | ` : '') + (projectType?.name || ''));
}

export function profileTitleTemplate(title?: string|null, route?: RouteType) {
  title = getTitle(title, route);
  return rootTitleTemplate((title ? title + ' | ' : '') + 'Profile');
}

export function userNotesTitleTemplate(title?: string|null, route?: RouteType) {
  title = getTitle(title, route);
  return rootTitleTemplate((title ? title + ' | ' : '') + 'Notes');
}

export function projectListBreadcrumbs(): Breadcrumbs {
  return [
    { title: 'Projects', to: '/projects/' },
  ];
}

export function projectDetailBreadcrumbs(project?: PentestProject): Breadcrumbs {
  return projectListBreadcrumbs().concat([
    { title: project?.name, to: `/projects/${project?.id}/` },
  ]);
}

export function designListBreadcrumbs(): Breadcrumbs {
  return [
    { title: 'Designs', to: '/designs/' },
  ];
}

export function designDetailBreadcrumbs(projectType?: ProjectType): Breadcrumbs {
  return designListBreadcrumbs().concat([
    { title: formatProjectTypeTitle(projectType), to: `/designs/${projectType?.id}/` },
  ]);
}

export function archivedProjectListBreadcrumbs(): Breadcrumbs {
  return projectListBreadcrumbs().concat([
    { title: 'Archived', to: '/projects/archived/' },
  ]);
}

export function archivedProjectDetailBreadcrumbs(archive?: ArchivedProject): Breadcrumbs {
  return archivedProjectListBreadcrumbs().concat([
    { title: archive?.name, to: `/projects/archived/${archive?.id}/` },
  ]);
}

export function templateListBreadcrumbs(): Breadcrumbs {
  return [
    { title: 'Templates', to: '/templates/' },
  ];
}

export function templateDetailBreadcrumbs(template?: FindingTemplate|null): Breadcrumbs {
  const mainTranslation = template?.translations.find(t => t.is_main);
  return templateListBreadcrumbs().concat([
    { title: mainTranslation?.data.title || '...', to: `/templates/${template?.id}/` },
  ]);
}

export function userListBreadcrumbs(): Breadcrumbs {
  return [
    { title: 'Users', to: '/users/' },
  ];
}

export function userDetailBreadcrumbs(user?: UserShortInfo): Breadcrumbs {
  return userListBreadcrumbs().concat([
    { title: user?.username, to: `/users/${user?.id}/` },
  ]);
}
