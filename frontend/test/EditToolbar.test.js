import { mount } from '@vue/test-utils';
import { cloneDeep } from 'lodash';
import { nextTick } from 'vue';
import EditToolbar from '@/components/EditToolbar.vue';
import { EditMode } from '~/utils/other';

describe('EditToolbar', () => {
  let data;
  let save;
  let del;
  let lock;
  let unlock;
  let componentsToCleanup;

  beforeEach(() => {
    data = { id: 'asdf', text: 'asfd', obj: { nested: 'asdf' } };
    save = jest.fn().mockResolvedValue({});
    del = jest.fn().mockResolvedValue({});
    lock = jest.fn().mockResolvedValue({ status: 201, data: {} });
    unlock = jest.fn().mockResolvedValue({});
    window.confirm = jest.fn(() => true);

    componentsToCleanup = [];
  })

  afterEach(() => {
    for (const c of componentsToCleanup) {
      c.destroy();
    }
  })

  async function createEditToolbar(props = {}) {
    EditToolbar.methods.performLockRequest = props.lock || lock;
    EditToolbar.methods.performUnlockRequest = props.unlock || unlock;
    const c = mount(EditToolbar, {
      propsData: {
        data: cloneDeep(props.data || data),
        canAutoSave: false,
        save,
        delete: del,
        lockUrl: '/mock/lock/',
        unlockUrl: '/mock/unlock/',
        editMode: EditMode.EDIT,
        ...props,
      },
      stubs: {
        VIcon: true,
        VBadge: true,
        VAlert: true,
      },
      mocks: {
        $store: {
          state: {
            settings: {
              autoSaveEnabled: true,
            }
          }
        }
      },
    });
    componentsToCleanup.push(c);
    // Run async initialization code
    await nextTick();
    return c;
  }

  test('save changes', async () => {
    const c = await createEditToolbar();
    expect(c.vm.hasChanges).toBeFalsy();

    // Changes
    data.text = 'changed';
    await c.setProps({ data });
    expect(c.vm.hasChanges).toBeTruthy();

    // Save
    expect(c.vm.canSave).toBeTruthy();
    expect(save).not.toHaveBeenCalled();
    await c.vm.performSave();
    expect(save).toHaveBeenCalledTimes(1);
    expect(save).toHaveBeenCalledWith(data);

    expect(c.vm.hasChanges).toBeFalsy();
    expect(c.vm.hasLock).toBeTruthy();
  });

  test('save no changes', async () => {
    const c = await createEditToolbar();
    // Save
    expect(c.vm.canSave).toBeTruthy();
    await c.vm.performSave();
    expect(save).not.toHaveBeenCalled();
    expect(c.vm.hasChanges).toBeFalsy();
    expect(c.vm.hasLock).toBeTruthy();
  });

  test('reset component', async () => {
    const c = await createEditToolbar();
    data.text = 'changed';
    await c.setProps({ data });
    expect(c.vm.hasChanges).toBeTruthy();

    await c.vm.resetComponent();
    await c.setProps({ data: { id: 'new' } });
    expect(c.vm.hasChanges).toBeFalsy();
  });

  test('initial locking', async () => {
    const c = await createEditToolbar();
    expect(lock).toHaveBeenCalledTimes(1);
    expect(c.vm.hasLock).toBeTruthy();
    expect(c.emitted('update:lockedData').length).toBe(1);
  });

  test('readonly not locked', async () => {
    const c = await createEditToolbar({ editMode: EditMode.READONLY });
    expect(lock).not.toHaveBeenCalled();
    expect(c.vm.hasLock).toBeFalsy();
  });

  test('locked by another user', async () => {
    const lockInfo = { user: { id: 'other', name: 'Other User', username: 'other' } }
    // eslint-disable-next-line prefer-promise-reject-errors
    const lock = jest.fn().mockRejectedValue({ response: { status: 403, data: { lock_info: lockInfo } } });
    const c = await createEditToolbar({ lock });
    expect(c.vm.hasLock).toBeFalsy();
    expect(c.vm.lockError).toBeTruthy();
    expect(c.vm.lockInfo).toBe(lockInfo);
    expect(c.emitted('update:editMode')[0][0]).toBe(EditMode.READONLY);
    expect(c.emitted('update:lockedData')[0][0].lock_info).toBe(lockInfo);
  });

  test('locked by same user in other tab', async () => {
    const lockInfo = { user: { id: 'user', name: 'Same User', username: 'user' } }
    const lock = jest.fn().mockResolvedValue({ status: 200, data: { lock_info: lockInfo } });
    const c = await createEditToolbar({ lock });
    expect(c.vm.hasLock).toBeFalsy();
    expect(c.vm.lockError).toBeTruthy();
    expect(c.emitted('update:editMode')[0][0]).toBe(EditMode.READONLY);
  })

  test('edit anyway', async () => {
    const lock = jest.fn().mockResolvedValue({ status: 200, data: {} });
    const c = await createEditToolbar({ lock });
    expect(c.vm.hasLock).toBeFalsy();
    expect(c.emitted('update:editMode')[0][0]).toBe(EditMode.READONLY);
    await c.setProps({ editMode: EditMode.READONLY });
    
    await c.vm.selfLockedEditAnyway();
    expect(c.vm.hasLock).toBeTruthy();
    expect(c.emitted('update:editMode')[1][0]).toBe(EditMode.EDIT);
  })

  test('set readonly', async () => {
    const c = await createEditToolbar();
    expect(c.vm.hasLock).toBeTruthy();

    await c.setProps({ editMode: EditMode.READONLY });
    expect(c.vm.hasLock).toBeFalsy();
    expect(unlock).toHaveBeenCalledTimes(1);
    expect(c.emitted('update:lockedData').length).toBe(2);
  });

  test('browser unload', async () => {
    const c = await createEditToolbar({ unlock });
    await c.vm.onUnloadBrowser();

    expect(unlock).toHaveBeenCalledTimes(1);
  });

  test('route leave (no changes)', async () => {
    const c = await createEditToolbar();
    await c.vm.beforeLeave(null, null, () => {});

    expect(c.vm.hasLock).toBeFalsy();
    expect(unlock).toHaveBeenCalledTimes(1);
    expect(window.confirm).not.toHaveBeenCalled();

    // Reuse component (as done by Nuxt on route update)
    await c.setProps({ data: { id: 'asdf', text: 'asdf' } });
    await nextTick();
    expect(c.vm.hasLock).toBeTruthy();
    expect(lock).toHaveBeenCalledTimes(2);
    expect(c.vm.hasChanges).toBeFalsy();
  });

  test('route leave (changes)', async () => {
    const c = await createEditToolbar();

    data.text = 'changed';
    await c.setProps({ data });
    expect(c.vm.hasChanges).toBeTruthy();

    await c.vm.beforeLeave(null, null, () => {});
    expect(window.confirm).toHaveBeenCalled();
    expect(c.vm.hasLock).toBeFalsy();
    expect(unlock).toHaveBeenCalledTimes(1);

    // Reuse component (as done by Nuxt on route update)
    await c.setProps({ data: { id: 'asdf', text: 'asdf' } });
    await nextTick();
    expect(c.vm.hasLock).toBeTruthy();
    expect(lock).toHaveBeenCalledTimes(2);
    expect(c.vm.hasChanges).toBeFalsy();
  });

  test('route leave (changes + autosave)', async () => {
    const c = await createEditToolbar({ canAutoSave: true });

    data.text = 'changed';
    await c.setProps({ data });
    expect(c.vm.hasChanges).toBeTruthy();
    expect(c.vm.hasLock).toBeTruthy();

    await c.vm.beforeLeave(null, null, () => {});
    expect(save).toHaveBeenCalledTimes(1);
    expect(unlock).toHaveBeenCalledTimes(1);
    expect(window.confirm).not.toHaveBeenCalled();
    expect(c.vm.hasLock).toBeFalsy();

    // Reuse component (as done by Nuxt on route update)
    await c.setProps({ data: { id: 'asdf', text: 'asdf' } });
    await nextTick();
    expect(c.vm.hasLock).toBeTruthy();
    expect(lock).toHaveBeenCalledTimes(2);
    expect(c.vm.hasChanges).toBeFalsy();
  });

  test('lock refresh', async () => {
    const lock = jest.fn()
      .mockResolvedValueOnce({ status: 201, data: {} })
      .mockResolvedValue({ status: 200, data: {} });
    const c = await createEditToolbar({ lock });
    jest.advanceTimersByTime(40_000);
    await nextTick();

    expect(c.vm.hasLock).toBeTruthy();
    expect(lock).toHaveBeenCalledTimes(2);
  });

  test('lock refresh unlocked', async () => {
    const lock = jest.fn()
      .mockResolvedValueOnce({ status: 201, data: {} })
      .mockResolvedValue({ status: 200, data: {} });
    const c = await createEditToolbar({ lock });
    await c.vm.performUnlock();
    await jest.advanceTimersByTime(40_000);
    await nextTick();

    expect(c.vm.hasLock).toBeFalsy();
    expect(lock).toHaveBeenCalledTimes(1);
  });

  test('lock refresh error', async () => {
    const lock = jest.fn()
      .mockResolvedValueOnce({ status: 201, data: {} })
      .mockRejectedValueOnce({ response: { status: 403, data: { lock_info: { user: { id: 'other', name: 'Other User', username: 'other' } } } } });
    const c = await createEditToolbar({ lock });
    await jest.advanceTimersByTime(40_000);
    await nextTick();

    expect(lock).toHaveBeenCalledTimes(2);
    expect(c.vm.hasLock).toBeFalsy();
    expect(c.emitted('update:editMode')[0][0]).toBe(EditMode.READONLY);
    expect(c.emitted('update:lockedData').length).toBe(2);
  });

  test('save error', async () => {
    const save = jest.fn().mockRejectedValue({ response: { status: 500 } });
    const c = await createEditToolbar({ save });

    await c.setProps({ data: { text: 'changed' } });
    await c.vm.performSave();
    
    expect(save).toHaveBeenCalled();
    expect(c.vm.hasLock).toBeTruthy();
    expect(c.vm.hasChanges).toBeTruthy();
  })

  test('delete', async () => {
    const c = await createEditToolbar();

    data.text = 'changed';
    await c.setProps({ data });
    await c.vm.performDelete();

    expect(del).toHaveBeenCalled();
    expect(unlock).not.toHaveBeenCalled();
    expect(c.vm.hasLock).toBeFalsy();

    // Route leave
    await c.vm.beforeLeave(null, null, () => {});
    expect(window.confirm).not.toHaveBeenCalled();
    expect(unlock).not.toHaveBeenCalled();
  });

  test('delete error', async () => {
    const del = jest.fn().mockRejectedValue({ response: { status: 500 } });
    const c = await createEditToolbar({ delete: del });

    await c.setProps({ data: { text: 'changed' } });
    try {
      await c.vm.performDelete();
    } catch (err) {}

    expect(del).toHaveBeenCalled();
    expect(c.vm.hasLock).toBeTruthy();
    expect(c.vm.hasChanges).toBeTruthy();
    expect(unlock).not.toHaveBeenCalled();
  });

  test('autosave', async () => {
    const c = await createEditToolbar({ canAutoSave: true });

    // No changes
    await jest.advanceTimersByTime(8_000);
    await nextTick();
    expect(save).not.toHaveBeenCalled();

    // Changes
    await c.setProps({ data: { text: 'changed' } });
    await jest.advanceTimersByTime(8_000);
    await nextTick();
    expect(save).toHaveBeenCalledTimes(1);
    expect(c.vm.hasLock).toBeTruthy();
    expect(c.vm.hasChanges).toBeFalsy();

    // No changes
    await jest.advanceTimersByTime(8_000);
    await nextTick();
    expect(save).toHaveBeenCalledTimes(1);
  });
});
