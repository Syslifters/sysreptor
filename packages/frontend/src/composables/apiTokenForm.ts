import { computed, ref, toValue, watch, type MaybeRefOrGetter } from 'vue';
import { addMonths, formatISO9075 } from 'date-fns';

export function useApiTokenForm(professional: MaybeRefOrGetter<boolean>) {
  const selectedProjects = ref<{ id: string; name: string }[]>([]);
  const isProjectRestricted = computed(() => (selectedProjects.value || []).length > 0);
  const expireDateEdited = ref(false);
  const defaultExpiry = (restricted: boolean) => toValue(professional)
    ? formatISO9075(addMonths(new Date(), restricted ? 1 : 3), { representation: 'date' })
    : null;
  const initialForm = () => ({
    name: 'API Token',
    expire_date: defaultExpiry(false),
    admin_permissions_enabled: !toValue(professional),
    read_only: true,
  });
  const form = ref(initialForm());

  watch(isProjectRestricted, (restricted) => {
    if (restricted) {
      form.value.admin_permissions_enabled = false;
      form.value.read_only = true;
    }
    if (!expireDateEdited.value) {
      form.value.expire_date = defaultExpiry(restricted);
    }
  }, { flush: 'sync' });

  const payload = computed(() => ({
    ...form.value,
    projects: (selectedProjects.value || []).map(p => p.id),
    admin_permissions_enabled: !isProjectRestricted.value && form.value.admin_permissions_enabled,
    read_only: isProjectRestricted.value && form.value.read_only,
  }));

  function reset() {
    selectedProjects.value = [];
    expireDateEdited.value = false;
    form.value = initialForm();
  }

  return { form, selectedProjects, isProjectRestricted, expireDateEdited, payload, reset };
}
