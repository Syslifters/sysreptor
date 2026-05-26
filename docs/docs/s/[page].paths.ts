import { fileURLToPath } from 'node:url'
import { PageData } from 'vitepress'

type Tool = {
  name: string
  url: string
  price: string
  self?: boolean
  discontinued?: boolean
  customization?: string
  deployment?: string
}

const software = [
  { name: 'vulnrepo', url: 'https://vulnrepo.com/', customization: 'Not provided', deployment: 'OnPrem', price: 'Free and Open Source' },
  { name: 'Vulnreport', url: 'https://github.com/salesforce/vulnreport', discontinued: true, customization: 'Unknown', deployment: 'OnPrem', price: 'Free and Open Source' },
  { name: 'PeTeReport', url: 'https://github.com/1modm/petereport', discontinued: true, customization: 'LaTeX/Eisvogel', deployment: 'OnPrem', price: 'Free and Open Source' },
  { name: 'Security Reporter', url: 'https://securityreporter.app/', customization: 'Theme editor', deployment: 'OnPrem', price: 'From $ 150' },
  { name: 'PenTest.WS', url: 'https://pentest.ws/', customization: 'docx with custom syntax and HTML', deployment: 'Cloud', price: 'From $ 4.95' },
  { name: 'Faraday', url: 'https://faradaysec.com/', customization: 'docx/Jinja2', deployment: 'Cloud/OnPrem', price: 'Free or from $ 120' },
  { name: 'Canopy', url: 'https://www.checksec.com/canopy.html', customization: 'docx with custom Word plugin', deployment: 'Cloud/OnPrem', price: 'Unknown' },
  { name: 'Ghostwriter', url: 'https://github.com/GhostManager/Ghostwriter', customization: 'docx/Jinja2', deployment: 'OnPrem', price: 'Free and Open Source' },
  { name: 'PlexTrac', url: 'https://plextrac.com/', customization: 'docx/Jinja2', deployment: 'Cloud/OnPrem', price: 'Top secret' },
  { name: 'Dradis', url: 'https://dradisframework.com/', customization: 'docx (Dradis optionally customizes for you)', deployment: 'Cloud/OnPrem', price: 'Free or $ 79 or $ 149' },
  { name: 'WriteHat', url: 'https://github.com/blacklanternsecurity/writehat', customization: 'HTML/Django Templating Language', deployment: 'OnPrem', price: 'Free and Open Source' },
  { name: 'AttackForge', url: 'https://attackforge.com/', customization: 'docx with customized template tags', deployment: 'Cloud or OnPrem (Enterprise only)', price: 'Free or $ 30 to $ 50' },
  { name: 'Pwndoc', url: 'https://github.com/pwndoc/pwndoc', customization: 'docx via docxtemplater', deployment: 'OnPrem', price: 'Free and Open Source' },
  { name: 'Hexway Hive', url: 'https://hexway.io/hive/', customization: 'docx with jinja-like syntax (Hexway customizes for you)', deployment: 'Cloud/OnPrem', price: 'Free or $ 78' },
  { name: 'Reconmap', url: 'https://github.com/reconmap/reconmap', customization: 'docx via PHPWord', deployment: 'OnPrem', price: 'Free and Open Source' },
  { name: 'Serpico', url: 'https://github.com/SerpicoProject/Serpico', discontinued: true, customization: 'docx with custom Meta Language', deployment: 'OnPrem', price: 'Free and Open Source' },
  { name: 'SysReptor', self: true, url: 'https://docs.sysreptor.com', customization: 'HTML with VueJS', deployment: 'Cloud/OnPrem', price: 'Free or € 50' },
] as Tool[];


const PREFACE = `SysReptor is a Pentest Reporting Tool written by pentesters, for pentesters. It is built with security in mind, best usability and strongest focus on the needs of pentesters.

However, if it does not fit your needs, here is a list of alternative tools.`

const POSTFACE = `
<br>

<div style="text-align:center">

[🚀 Sign Up to SysReptor](https://sysreptor.com){ .md-button }

</div>

<br>

This overview of penetration testing reporting tools has been compiled to the best of our knowledge and belief. We do not guarantee that the information is correct or up-to-date.

❌ We regard software projects without updates for one year, with missing security patches or major dependencies without support as discontinued.

We welcome tips on other pentest reporting tools.
For inquiries and tips write us a short message to hello@syslifters.com.`

/** Edit this list to update /s/ pages. */



function slug(name: string) {
  return name.toLowerCase()
    .replaceAll('/', '-').replaceAll(' ', '-').replaceAll('.', '')
    .replaceAll('ö', 'oe').replaceAll('ä', 'ae').replaceAll('ü', 'ue').replaceAll('ß', 'ss')
}

function sortTools(tools: Tool[]) {
  return [...tools].sort((a, b) => {
    const bySelf = Number(!!b.self) - Number(!!a.self)
    if (bySelf !== 0) return bySelf
    const byDiscontinued = Number(!!a.discontinued) - Number(!!b.discontinued)
    if (byDiscontinued !== 0) return byDiscontinued
    return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
  })
}

function table(tools: Tool[]) {
  const rows = tools.map((t) => {
    const icon = t.self ? '🔥' : t.discontinued ? '❌' : ''
    return `| ${icon} [${t.name}](${t.url}) | 📄 ${t.customization ?? ''} | 🖥️ ${t.deployment ?? ''} | 🏷️ ${t.price} |`
  })
  return `| Name | Report Customization | Deployment | Costs/User/Month |\n| - | - | - | - |\n${rows.join('\n')}`
}

function alternativePreface(tool: Tool) {
  return `Similar projects and and alternatives to [${tool.name}](${tool.url}) Penetration Test Reporting Tool.`
}

function content(title: string, preface: string, tools: Tool[]) {
  return `# ${title}

${preface}
<br>

${table(tools)}
${POSTFACE}
`
}

const pathsFile = fileURLToPath(import.meta.url)
export default {
  watch: [pathsFile],
  paths() {
    const tools = sortTools(software)
    const paths = [{
      params: { page: 'pentest-reporting-tools' },
      content: content(
        'Pentest Reporting Tools - A List of the most popular tools',
        PREFACE,
        tools,
      ),
    }]

    for (const t of tools) {
      if (t.self) continue
      paths.push({
        params: { page: `alternative-to-${slug(t.name)}-reporting-tool` },
        content: content(
          `Alternatives to ${t.name} Pentesting Reporting Tool`,
          `${alternativePreface(t)}\n\n${PREFACE}`,
          tools,
        ),
      })
    }

    return paths
  },
  transformPageData(pageData: PageData) {
    pageData.frontmatter.search = { exclude: true };
  }
}
