export class IntegrationAdmin {
  constructor(username: string, password: string) {
    this.username = username;
    this.password = password;
  }
  username: string;
  password: string;

}

export function getIntegrationAdmin() {
  const username = process.env.FRONTEND_ADMIN_USER || 'admin';
  const password = process.env.FRONTEND_ADMIN_PASSWORD || 'admin';
  return new IntegrationAdmin(username, password);
}
