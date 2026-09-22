import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import ApiTokenScope from '~/components/ApiTokenScope.vue';
import type { ApiToken } from '#imports';

function renderToken(overrides: Partial<ApiToken> = {}) {
  return mount(ApiTokenScope, {
    props: { token: {
      is_project_restricted: true, read_only: true,
      projects: ['one', 'two'], project_details: [{ id: 'one', name: 'Visible project' }],
      ...overrides,
    } as ApiToken },
    global: { stubs: { VChip: { template: '<span><slot /></span>' } } },
  });
}

describe('Token scope in global token lists', () => {
  it('shows access level and visible project names without exposing unavailable projects', () => {
    const wrapper = renderToken();
    expect(wrapper.text()).toContain('Read only');
    expect(wrapper.text()).toContain('Visible project');
    expect(wrapper.text()).toContain('Unavailable project');
  });

  it('continues to label an empty restricted token as restricted', () => {
    const wrapper = renderToken({ projects: [], project_details: [], read_only: false });
    expect(wrapper.text()).toContain('Read/write');
    expect(wrapper.text()).toContain('no projects remaining');
  });

  it('does not label unrestricted tokens as project-restricted', () => {
    expect(renderToken({ is_project_restricted: false }).text()).toBe('');
  });
});
