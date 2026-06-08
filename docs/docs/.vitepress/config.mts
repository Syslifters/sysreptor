import { defineConfig } from 'vitepress'
import markdownItAttrs from 'markdown-it-attrs'
import markdownItFootnote from 'markdown-it-footnote'
import { tabsMarkdownPlugin } from 'vitepress-plugin-tabs'
import llmstxt from 'vitepress-plugin-llms'
import { vitepressRedirectsPlugin } from './redirects/viteRedirectsPlugin'
import { pythonAutodocPlugin } from './plugins/pythonAutodoc'

const env = (globalThis as any).process?.env as Record<string, string | undefined> | undefined
const sitemapHostname = env?.VITEPRESS_SITEMAP_HOSTNAME ?? 'https://docs.sysreptor.com'


// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: 'SysReptor',
  description: 'SysReptor hosting and usage documentation',
  lang: 'en-US',
  head: [
    ['link', { rel: 'icon', href: '/images/logo.svg' }],
  ],
  themeConfig: {
    logo: '/images/logo.svg',

    nav: [
      { text: 'Try Playground', link: 'https://sysreptor.com/demo' },
    ],

    editLink: {
      pattern: 'https://github.com/syslifters/sysreptor/edit/main/docs/docs/:path',
      text: 'Edit this page on GitHub',
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/syslifters/sysreptor' },
      { icon: 'linkedin', link: 'https://www.linkedin.com/showcase/sysreptor' },
    ],

    search: {
      provider: 'local',
      options: {
        detailedView: true,
      },
    },

    outline: {
      level: 'deep',
    },

    sidebar: [
      {
        text: 'Setup',
        collapsed: true,
        items: [
          { text: 'Installation', link: '/setup/installation' },
          { text: 'Configuration', link: '/setup/configuration' },
          { text: 'Setup Webserver', link: '/setup/webserver' },
          { text: 'Updates', link: '/setup/updates' },
          { text: 'Backups', link: '/setup/backups' },
          { text: 'Upgrade to PRO', link: '/setup/upgrade-to-professional' },
        ],
      },
      {
        text: 'Writing Reports',
        collapsed: true,
        items: [
          { text: 'Markdown Syntax', link: '/reporting/markdown-features' },
          { text: 'Notes', link: '/reporting/notes' },
          { text: 'Comments and Review', link: '/reporting/comments-and-review' },
          { text: 'Version History', link: '/reporting/version-history' },
          { text: 'Spell Check', link: '/reporting/spell-check' },
          { text: 'References', link: '/reporting/references' },
          { text: 'Finding Templates', link: '/finding-templates/create-finding' },
          { text: 'Collaborative Editing', link: '/reporting/collaborative-editing' },
          { text: 'Image Editor', link: '/reporting/image-editor' },
          { text: 'AI Agent', link: '/reporting/ai-agent' },
          { text: 'Shortcuts', link: '/reporting/shortcuts' },
        ],
      },
      {
        text: 'Designing Reports',
        collapsed: true,
        items: [
          { text: 'Designer', link: '/designer/designer' },
          { text: 'Field Types', link: '/designer/field-types' },
          { text: 'Design Guides', link: '/designer/design-guides' },
          { text: 'Page Layout', link: '/designer/page-layout' },
          { text: 'Headings and ToC', link: '/designer/headings-and-table-of-contents' },
          { text: 'Tables', link: '/designer/tables' },
          { text: 'Figures', link: '/designer/figures' },
          { text: 'Charts', link: '/designer/charts' },
          { text: 'Findings', link: '/designer/findings' },
          { text: 'Formatting Utilities', link: '/designer/formatting-utils' },
          { text: 'Filenames', link: '/designer/filenames' },
          { text: 'Debugging', link: '/designer/debugging' },
          { text: 'FAQs', link: '/designer/faqs' },
        ],
      },
      {
        text: 'Finding Templates',
        collapsed: true,
        items: [
          { text: 'Overview', link: '/finding-templates/overview' },
          { text: 'Create Finding', link: '/finding-templates/create-finding' },
          { text: 'Multilingual', link: '/finding-templates/multilingual' },
        ],
      },
      {
        text: 'Users and Permissions',
        collapsed: true,
        items: [
          { text: 'User Permissions', link: '/users/user-permissions' },
          {
            text: 'Single Sign-On',
            collapsed: true,
            items: [
              { text: 'SSO Setup', link: '/users/oidc-setup' },
              { text: 'Keycloak', link: '/users/oidc-keycloak' },
              { text: 'Microsoft Entra ID', link: '/users/oidc-entra-id' },
              { text: 'Google', link: '/users/oidc-google' },
              { text: 'Microsoft ADFS', link: '/users/oidc-adfs' },
              { text: 'Generic', link: '/users/oidc-generic' },
            ],
          },
          { text: 'Forgot Password', link: '/users/forgot-password' },
          { text: 'Notifications', link: '/users/notifications' },
        ],
      },
      {
        text: 'Python Integration',
        collapsed: true,
        items: [
          { text: 'Getting Started', link: '/python-library/' },
          {
            text: 'Tutorial',
            collapsed: true,
            items: [
              { text: '1. Projects', link: '/python-library/tutorial/part-1/projects' },
              { text: '2. Findings', link: '/python-library/tutorial/part-2/findings' },
              { text: '3. Notes', link: '/python-library/tutorial/part-3/notes' },
            ],
          },
          {
            text: 'API',
            collapsed: true,
            items: [
              { text: 'Projects', link: '/python-library/api/projects' },
              { text: 'Notes', link: '/python-library/api/notes' },
              { text: 'Finding Templates', link: '/python-library/api/templates' },
              { text: 'Project Designs', link: '/python-library/api/project-designs' },
            ],
          },
          {
            text: 'Data Classes',
            collapsed: true,
            items: [
              { text: 'Project', link: '/python-library/dataclasses/project' },
              { text: 'Finding', link: '/python-library/dataclasses/finding' },
              { text: 'Section', link: '/python-library/dataclasses/section' },
              { text: 'Note', link: '/python-library/dataclasses/note' },
              { text: 'Finding Template', link: '/python-library/dataclasses/finding-template' },
              { text: 'Project Design', link: '/python-library/dataclasses/project-design' },
              { text: 'User', link: '/python-library/dataclasses/user' },
            ],
          },
        ],
      },
      {
        text: 'Automize Reporting via CLI',
        collapsed: true,
        items: [
          { text: 'Getting Started', link: '/cli/getting-started' },
          { text: 'Configuration', link: '/cli/configuration' },
          {
            text: 'Tools',
            collapsed: true,
            items: [
              { text: 'Burp', link: '/cli/tools/burp' },
              { text: 'Nessus', link: '/cli/tools/nessus' },
              { text: 'Qualys', link: '/cli/tools/qualys' },
              { text: 'OpenVAS', link: '/cli/tools/openvas' },
              { text: 'Nmap', link: '/cli/tools/nmap' },
              { text: 'SSLyze', link: '/cli/tools/sslyze' },
              { text: 'ZAP', link: '/cli/tools/zap' },
            ],
          },
          {
            text: 'Projects and Templates',
            collapsed: true,
            items: [
              { text: 'Project', link: '/cli/projects-and-templates/project' },
              { text: 'CreateProject', link: '/cli/projects-and-templates/createproject' },
              { text: 'PushProject', link: '/cli/projects-and-templates/pushproject' },
              { text: 'DeleteProjects', link: '/cli/projects-and-templates/deleteprojects' },
              { text: 'Finding', link: '/cli/projects-and-templates/finding' },
              { text: 'FindingFromTemplate', link: '/cli/projects-and-templates/findingfromtemplate' },
              { text: 'ExportFindings', link: '/cli/projects-and-templates/exportfindings' },
              { text: 'DeleteFindings', link: '/cli/projects-and-templates/deletefindings' },
              { text: 'Template', link: '/cli/projects-and-templates/template' },
              { text: 'File', link: '/cli/projects-and-templates/file' },
              { text: 'Note', link: '/cli/projects-and-templates/note' },
              { text: 'Translate', link: '/cli/projects-and-templates/translate' },
            ],
          },
          {
            text: 'Utils',
            collapsed: true,
            items: [
              { text: 'Unpackarchive', link: '/cli/utils/unpackarchive' },
              { text: 'Packarchive', link: '/cli/utils/packarchive' },
            ],
          },
          {
            text: 'Importers',
            collapsed: true,
            items: [
              { text: 'DefectDojo', link: '/cli/importers/defectdojo' },
              { text: 'Ghostwriter', link: '/cli/importers/ghostwriter' },
            ],
          },
          {
            text: 'Writing plugins',
            collapsed: true,
            items: [
              { text: 'Tools', link: '/cli/writing-plugins/tools' },
              { text: 'Importers', link: '/cli/writing-plugins/importers' },
            ],
          },
        ],
      },
      {
        text: 'Tech Insights',
        collapsed: true,
        items: [
          { text: 'Architecture', link: '/insights/architecture' },
          { text: 'Rendering Workflow', link: '/insights/rendering-workflow' },
          { text: 'Archiving', link: '/insights/archiving' },
          { text: 'Project Search', link: '/insights/project-search' },
          { text: 'Security Considerations', link: '/insights/security-considerations' },
          {
            text: 'Vulnerabilities',
            link: 'https://github.com/Syslifters/sysreptor/security/advisories',
          },
        ],
      },
      { text: 'Plugins', link: '/setup/plugins' },
      { text: 'Demo Reports', link: '/demo-reports' },
      { text: 'Features and Pricing', link: 'https://sysreptor.com/pricing' },
      { text: 'Get Involved', link: '/get-involved' },
      { text: 'Contact Us', link: '/contact-us' },
    ],
  },
  lastUpdated: true,
  cleanUrls: true,
  sitemap: {
    hostname: sitemapHostname,
  },
  vite: {
    plugins: [
      llmstxt({
        domain: sitemapHostname,
        description: 'This is the official hosting and usage documentation of the pentest reporting tool SysReptor.',
      }),
      vitepressRedirectsPlugin({
        redirects: {
          '/setup/nginx-server': '/setup/webserver',
          '/reporting/referencing-sections': '/reporting/references',
          '/setup/prerequisites': '/setup/installation',
          '/backups': '/setup/backups',
          '/templates': '/finding-templates/overview',
          '/reporting/archiving': '/insights/archiving',
          '/setup/user-permissions': '/users/user-permissions',
          '/setup/oidc-setup': '/users/oidc-setup',
          '/setup/oidc-keycloak': '/users/oidc-keycloak',
          '/setup/oidc-azure-active-directory': '/users/oidc-entra-id',
          '/users/oidc-azure-active-directory': '/users/oidc-entra-id',
          '/setup/oidc-google': '/users/oidc-google',
          '/setup/oidc-generic': '/users/oidc-generic',
          '/setup/proxy': '/setup/configuration',
          '/setup/network': '/setup/configuration',
          '/security.txt': 'https://docs.syslifters.com/.well-known/security.txt',
          '/.well-known/security.txt': 'https://docs.syslifters.com/.well-known/security.txt',
          '/features-and-pricing': 'https://sysreptor.com/pricing',
          '/assets/ToS_SysReptor_self-hosted.pdf': 'https://sysreptor.com/api/v1/documents/latest?type=order-sh-tos',
          '/assets/ToS_SysReptor_cloud.pdf': 'https://sysreptor.com/api/v1/documents/latest?type=order-cloud-tos',
        },
      }),
    ],
  },
  markdown: {
    breaks: false,
    lineNumbers: true,
    image: {
      lazyLoading: true,
    },
    config: (md) => {
      md.use(pythonAutodocPlugin)
      md.use(markdownItAttrs)
      md.use(markdownItFootnote)
      md.use(tabsMarkdownPlugin)
    }
  },
})
