import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { effectScope } from 'vue';
import { useApiTokenForm } from '~/composables/apiTokenForm';

describe('API token creation', () => {
  let scope: ReturnType<typeof effectScope>;
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 0, 31, 12));
    scope = effectScope();
  });
  afterEach(() => {
    scope.stop();
    vi.useRealTimers();
  });

  it('switches defaults without sending admin privileges or read-only for an unrestricted token', () => {
    const setup = scope.run(() => useApiTokenForm(true))!;
    expect(setup.payload.value).toMatchObject({ projects: [], read_only: false, expire_date: '2026-04-30' });
    setup.form.value.admin_permissions_enabled = true;
    setup.selectedProjects.value = [{ id: 'one', name: 'One' }, { id: 'two', name: 'Two' }];
    expect(setup.payload.value).toMatchObject({
      projects: ['one', 'two'], read_only: true, admin_permissions_enabled: false, expire_date: '2026-02-28',
    });
    setup.form.value.read_only = false;
    expect(setup.payload.value.read_only).toBe(false);
    setup.selectedProjects.value = [];
    expect(setup.payload.value).toMatchObject({ projects: [], read_only: false, admin_permissions_enabled: false, expire_date: '2026-04-30' });
  });

  it.each([null, '2027-01-01'])('preserves an explicitly chosen expiry of %s when switching scope', (expiry) => {
    const setup = scope.run(() => useApiTokenForm(true))!;
    setup.form.value.expire_date = expiry;
    setup.expireDateEdited.value = true;
    setup.selectedProjects.value = [{ id: 'one', name: 'One' }];
    expect(setup.payload.value.expire_date).toBe(expiry);
    setup.selectedProjects.value = [];
    expect(setup.payload.value.expire_date).toBe(expiry);
  });

  it('resets the complete form between creation dialogs', () => {
    const setup = scope.run(() => useApiTokenForm(true))!;
    setup.selectedProjects.value = [{ id: 'one', name: 'One' }];
    setup.form.value.expire_date = null;
    setup.expireDateEdited.value = true;
    setup.form.value.name = 'Previous token';
    setup.reset();
    expect(setup.payload.value).toEqual({
      name: 'API Token', projects: [], read_only: false, admin_permissions_enabled: false, expire_date: '2026-04-30',
    });
  });

  it('preserves Community token defaults', () => {
    const setup = scope.run(() => useApiTokenForm(false))!;
    expect(setup.payload.value).toMatchObject({ projects: [], read_only: false, admin_permissions_enabled: true, expire_date: null });
  });
});
