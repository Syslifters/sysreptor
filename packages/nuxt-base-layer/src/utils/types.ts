import type { CvssVersion } from "./cvss/base";
import type { RouteLocationRaw } from '#vue-router';

export type BaseModel = {
  id: string;
  created: string;
  updated: string;
};

export type PaginatedResponse<T> = {
  readonly next: string | null;
  readonly prev: string | null;
  readonly results: T[];
}

export type UserShortInfo = {
  id: string;
  is_active: boolean;

  username: string;
  color: string|null;
  title_before: string | null;
  first_name: string | null;
  middle_name: string | null;
  last_name: string | null;
  title_after: string | null;
  readonly name: string | null;
};

export type User = UserShortInfo & BaseModel & {
  readonly created: string;
  readonly updated: string;
  readonly last_login: string|null;
  readonly is_mfa_enabled: boolean;
  readonly can_login_local: boolean;
  readonly can_login_sso: boolean;

  must_change_password: boolean;

  email: string|null;
  phone: string|null;
  mobile: string|null;

  is_superuser: boolean;
  is_project_admin: boolean;
  is_user_manager: boolean;
  is_designer: boolean;
  is_template_editor: boolean;
  is_guest: boolean;
  is_system_user: boolean;
  is_global_archiver: boolean;
  scope: string[];
};

export type LockInfo = {
  created: string;
  updated: string;
  last_ping: string;
  expires: string;
  user: User;
};

export interface Lockable {
  lock_info: LockInfo|null,
}

export enum LicenseType {
    community = 'community',
    professional = 'professional',
}

export type Language = {
    code: string,
    name: string,
    spellcheck: boolean,
    enabled: boolean,
}

export enum AuthProviderType {
    LOCAL = 'local',
    REMOTEUSER = 'remoteuser',
    OIDC = 'oidc'
}

export type AuthProvider = {
    type: AuthProviderType,
    id: string,
    name: string
}

export type AuthIdentity = BaseModel & {
  provider: string;
  identifier: string;
}

export type PluginConfig = {
  id: string;
  name: string;
  frontend_entry: string|null;
  frontend_settings: Record<string, any>;
}

export enum PluginRouteScope {
  MAIN = 'main',
  PROJECT = 'project',
}

export type PluginMenuEntry = {
  title: string;
  icon?: string;
  attrs?: Record<string, any>;
  scope: PluginRouteScope;
  to: { name: string };
  pluginConfig: PluginConfig;
}

export type ApiSettings = {
    readonly license: {
        readonly type: LicenseType;
        readonly error: string|null;
    };
    readonly languages: Language[];
    readonly project_member_roles: {
        readonly role: string;
        readonly default: boolean;
    }[];
    readonly auth_providers: AuthProvider[];
    readonly default_auth_provider: string|null;
    readonly default_reauth_provider: string|null;
    readonly elastic_apm_rum_config: any|null;
    readonly archiving_threshold: number;
    readonly features: {
        readonly private_designs: boolean;
        readonly spellcheck: boolean;
        readonly archiving: boolean;
        readonly permissions: boolean;
        readonly backup: boolean;
        readonly websockets: boolean;
        readonly sharing: boolean;
    };
    readonly permissions: {
      readonly guest_users_can_import_projects: boolean;
      readonly guest_users_can_create_projects: boolean;
      readonly guest_users_can_delete_projects: boolean;
      readonly guest_users_can_update_project_settings: boolean;
      readonly guest_users_can_edit_projects: boolean;
      readonly guest_users_can_share_notes: boolean;
      readonly guest_users_can_see_all_users: boolean;
      readonly project_members_can_archive_projects: boolean;
    };
    readonly plugins: PluginConfig[];
}

export type LicenseInfoDetails = {
  readonly type: LicenseType;
  readonly error: string | null,
  readonly name?: string;
  readonly valid_from?: string;
  readonly valid_until?: string;
  readonly users: number;
  readonly active_users: number;
  readonly software_version: string;
  readonly plugins: string[];
}

export enum MfaMethodType {
  FIDO2 = 'fido2',
  TOTP = 'totp',
  BACKUP = 'backup',
}

export type MfaMethod = {
  readonly id: string;
  readonly method_type: MfaMethodType;
  name: string;
  is_primary: boolean;
};

export const mfaMethodChoices = Object.freeze([
  { value: MfaMethodType.FIDO2, text: 'Security Key (FIDO2)', icon: 'mdi-key' },
  { value: MfaMethodType.TOTP, text: 'Authenticator App (TOTP)', icon: 'mdi-cellphone-key' },
  { value: MfaMethodType.BACKUP, text: 'Backup Codes', icon: 'mdi-lock-reset' },
]);

export type ApiToken = BaseModel & {
  name: string;
  expire_date: string|null;
  last_used: string|null;
  token?: string;
}

export type UserPublicKey = BaseModel & {
  name: string;
  enabled: boolean;
  public_key: string;
  public_key_info: any;
}

export enum LoginResponseStatus {
  SUCCESS = 'success',
  MFA_REQUIRED = 'mfa-required',
  PASSWORD_CHANGE_REQUIRED = 'password-change-required',
}

export type LoginResponse = {
  status: LoginResponseStatus,
  first_login?: boolean,
  mfa?: MfaMethod[],
  license?: LicenseInfoDetails,
}

export type UserNotification = BaseModel & {
  readonly content: {
    title: string;
    text: string;
    link_url: string | null;
  },
  read: boolean;
}

export type DocumentSelectionPosition = {
  from: number;
  to: number;
}

export enum PdfDesignerTab {
  LAYOUT = 'layout',
  HTML = 'html',
  CSS = 'css',
  ASSETS = 'assets',
  PREVIEW_DATA = 'preview-data',
}

export enum EditMode {
  READONLY = 'READONLY',
  EDIT = 'EDIT',
}

export enum MarkdownEditorMode {
    MARKDOWN = 'markdown',
    PREVIEW = 'preview',
    MARKDOWN_AND_PREVIEW = 'markdown-preview',
}

export enum SourceEnum {
  CREATED = 'created',
  IMPORTED = 'imported',
  IMPORTED_DEPENDENCY = 'imported_dependency',
  CUSTOMIZED = 'customized',
  SNAPSHOT = 'snapshot',
}

export enum ReviewStatus {
  IN_PROGRESS = 'in-progress',
  READY_FOR_REVIEW = 'ready-for-review',
  NEEDS_IMPROVEMENT = 'needs-improvement',
  FINISHED = 'finished',
}

export const ReviewStatusItems = Object.freeze([
  { value: ReviewStatus.IN_PROGRESS, title: 'In progress', icon: 'mdi-pencil' },
  { value: ReviewStatus.READY_FOR_REVIEW, title: 'Ready for review', icon: 'mdi-check' },
  { value: ReviewStatus.NEEDS_IMPROVEMENT, title: 'Needs improvement', icon: 'mdi-exclamation-thick' },
  { value: ReviewStatus.FINISHED, title: 'Finished', icon: 'mdi-check-all' }
]);

export enum ProjectTypeStatus {
  IN_PROGRESS = 'in-progress',
  READY_FOR_REVIEW = 'ready-for-review',
  NEEDS_IMPROVEMENT = 'needs-improvement',
  FINISHED = 'finished',
  DEPRECATED = 'deprecated',
}
export const ProjectTypeStatusItems = Object.freeze((ReviewStatusItems as unknown as {value: ProjectTypeStatus, title: string, icon: string}[]).concat([
  { value: ProjectTypeStatus.DEPRECATED, title: 'Deprecated', icon: 'mdi-close-octagon-outline' },
]))

export enum CommentStatus {
  OPEN = 'open',
  RESOLVED = 'resolved',
};

export type CommentAnswer = BaseModel & {
  text: string;
  user: UserShortInfo|null;
};

export type Comment = BaseModel & {
  text: string;
  user: UserShortInfo|null;
  status: CommentStatus;
  path: string;
  text_range: {from: number, to: number}|null;
  text_original: string|null;
  answers: CommentAnswer[];

  // Internal properties used by frontend
  collabPath?: string;
}

export type ProjectMember = UserShortInfo & {
  roles: string[];
}

export type PentestProject = BaseModel & {
  readonly source: SourceEnum;
  readonly copy_of: string|null;

  name: string;
  project_type: string;
  language: string;
  tags: string[];
  readonly: boolean;
  override_finding_order: boolean;
  members: ProjectMember[];
  imported_members: ProjectMember[];
}

export type ReportSection = BaseModel & {
  readonly label: string;
  readonly fields: string[];
  readonly project: string;
  readonly project_type: string;
  readonly language: string;

  assignee: UserShortInfo|null;
  status: ReviewStatus|null;
  data: Record<string, any>;
}

export type PentestFinding = BaseModel & {
  readonly label: string;
  readonly fields: string[];
  readonly project: string;
  readonly project_type: string;
  readonly language: string;
  readonly template: string|null;

  order: number;
  assignee: UserShortInfo|null;
  status: ReviewStatus|null;
  data: Record<string, any>;
};

export type NoteBase = {
  id: string;
  parent: string|null;
  order: number;
  title: string;
  text: string;
  checked: boolean|null;
  icon_emoji: string|null;
}

export type UserNote = BaseModel & NoteBase;

export type ProjectNote = BaseModel & NoteBase & {
  assignee: UserShortInfo|null;
  is_shared: boolean;
};

export type ArchivedProjectKeyPart = BaseModel & {
  user: UserShortInfo;
  is_decrypted: boolean;
  decrypted_at: string|null;
}

export type ArchivedProject = BaseModel & {
  readonly auto_delete_date: string|null;
  readonly reencrypt_key_parts_after_inactivity_date: string|null;
  name: string;
  tags: string[];
  threshold: number;
  key_parts: ArchivedProjectKeyPart[];
};

export type ArchivedProjectPublicKeyEncryptedKeyPart = BaseModel & {
  public_key: UserPublicKey;
  encrypted_data: string;
}

export type ArchiveCheckResult = {
  users: (UserShortInfo & {
    readonly is_project_member: boolean;
    readonly is_global_archiver: boolean;
    readonly has_public_keys: boolean;
    readonly has_permissions: boolean;
    readonly can_restore: boolean;
    readonly warnings: string[];
  })[];
}

export enum RiskLevel {
  INFO = 'info',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export type FindingTemplateTranslation = BaseModel & {
  readonly risk_score: number;
  readonly risk_level: RiskLevel;

  language: string;
  status: ReviewStatus;
  is_main: boolean;
  data: {
    title: string,
    [key: string]: any
  },
}

export type FindingTemplate = BaseModel & Lockable & {
  readonly usage_count: number;
  readonly source: SourceEnum;
  tags: string[];
  translations: FindingTemplateTranslation[];
}

export enum ProjectTypeScope {
  GLOBAL = 'global',
  PRIVATE = 'private',
  PROJECT = 'project',
}

export enum FieldDataType {
  STRING = 'string',
  MARKDOWN = 'markdown',
  CVSS = 'cvss',
  CWE = 'cwe',
  DATE = 'date',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  ENUM = 'enum',
  COMBOBOX = 'combobox',
  JSON = 'json',
  USER = 'user',
  OBJECT = 'object',
  LIST = 'list',
}

export enum FieldOrigin {
  CORE = 'core',
  PREDEFINED = 'predefined',
  CUSTOM = 'custom',
}

export type EnumFieldChoiceDefinition = {
  value: string|null;
  label: string;
};

export type FieldDefinition = {
  id: string;
  type: FieldDataType;
  label: string;
  origin: FieldOrigin;
  default?: any|null;
  required?: boolean;
  spellcheck?: boolean;
  pattern?: string|null;
  cvss_version?: CvssVersion;
  suggestions?: string[];
  choices?: EnumFieldChoiceDefinition[];
  properties?: FieldDefinition[];
  items?: FieldDefinition;
  minimum?: number|null;
  maximum?: number|null;
}

export type TemplateFieldDefinition = FieldDefinition & { 
  visible: boolean;
  used_in_designs: boolean;
};

export enum SortOrder {
  ASC = 'asc',
  DESC = 'desc'
}

export type FindingOrderingDefinition = {
    field: string;
    order: SortOrder;
};

export type ReportSectionDefinition = {
    id: string;
    label: string;
    fields: FieldDefinition[];
};

export type ProjectType = BaseModel & Lockable & {
  readonly source: SourceEnum;
  readonly scope: ProjectTypeScope;
  readonly usage_count: number;
  readonly copy_of: string|null;

  name: string;
  language: string;
  status: ProjectTypeStatus;
  tags: string[];

  report_template: string;
  report_styles: string;
  report_preview_data: {
    report: Record<string, any>;
    findings: {
      title: string;
      [key: string]: any;
    }[];
  };
  report_sections: ReportSectionDefinition[];
  finding_fields: FieldDefinition[];
  finding_ordering: FindingOrderingDefinition[];
  default_notes: NoteBase[];
}

export type HistoryTimelineRecord = {
  readonly history_type: '+' | '~' | '-';
  readonly history_date: string;
  readonly history_user: UserShortInfo|null;
  readonly history_change_reason: string|null;
  readonly history_model: string;
  readonly history_title: string;
  readonly id: string;
}

export enum MessageLevel {
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info',
  DEBUG = 'debug',
}

export enum MessageLocationType {
  FINDING = 'finding',
  PROJECT = 'project',
  SECTION = 'section',
  DESIGN = 'design',
  OTHER = 'other',
}

export type ErrorMessage = {
  level: MessageLevel;
  message: string;
  details?: string|null;
  location?: {
    type:MessageLocationType;
    id: string|null;
    name: string|null;
    path: string|null;
  };
};

export type PdfResponse = {
  pdf: string|null;
  messages: ErrorMessage[];
  timings: Record<string, number>;
}

export enum UploadedFileType {
  IMAGE = 'image',
  FILE = 'file',
  ASSET = 'asset',
}

export type UploadedFileInfo = BaseModel&{
  name: string;
  resource_type: UploadedFileType;
}

export type StringChange = {from: number, deleteCount: number, add: string};
export type CodeChange = StringChange & {type: string};

export type Breadcrumb = {
  title?: string;
  icon?: string;
  to?: RouteLocationRaw;
};
export type Breadcrumbs = Breadcrumb[];

export type PreviewImage = {
  src: string;
  caption?: string|null;
  markdown?: string|null;
};

export type CWE = {
  id: number;
  name: string;
  description: string;
  parent: number|null;
};

export enum BackupLogType {
  SETUP = 'setup',
  BACKUP = 'backup',
  RESTORE = 'restore',
}

export type BackupLog = BaseModel & {
  type: BackupLogType;
  user: string|null;
}

export type OrderingOption = {
  id: string;
  title: string;
  value: string;
}

export type ShareInfo = BaseModel & {
  readonly shared_by?: UserShortInfo|null;
  expire_date: string;
  is_revoked: boolean;
  permissions_write: boolean;
  password: string|null;
}

export type ShareInfoPublic = BaseModel & {
  readonly expire_date: string;
  readonly permissions_write: boolean;
  readonly password_required: boolean;
  readonly password_verified: boolean;
  readonly note_id: string;
}
