export class IntegrationAdmin {
  static username: string = process.env.FRONTEND_ADMIN_USER || 'admin';
  static password: string = process.env.FRONTEND_ADMIN_PASSWORD || 'admin';
}