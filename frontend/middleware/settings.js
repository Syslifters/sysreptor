
export default async function apiSettingsMiddleware(ctx) {
  await ctx.store.dispatch('apisettings/getSettings');
}
