declare module 'virtual:vitepress-redirects' {
  const rules: import('./redirectRules').RedirectRule[]
  export default rules
  export { rules }
}

