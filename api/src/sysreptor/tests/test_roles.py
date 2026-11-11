import pytest
from django.urls import reverse

from sysreptor.pentests.models import FindingTemplate, PentestProject, ProjectType, SourceEnum
from sysreptor.tests.mock import (
    api_client,
    create_project,
    create_project_type,
    create_template,
    create_user,
    override_configuration,
)
from sysreptor.users.models import PentestUser
from sysreptor.users.roles import (
    PREDEFINED_USER_ROLES,
    Permission,
    expand_permissions,
    get_role_permissions,
    get_roles_with_permission,
    validate_custom_roles,
)

CUSTOM_USER_ROLES = [
    {'id': 'template_reader', 'name': 'Template Reader', 'permissions': ['template.read']},
    {'id': 'project_all', 'name': 'Project All', 'permissions': ['project.*']},
    {'id': 'project_reader', 'name': 'Project Reader', 'permissions': ['project.read']},
    {'id': 'project_editor_without_read', 'name': 'Project Editor without read', 'permissions': ['project.edit_content', 'project.update_settings']},
    {'id': 'unnamed_role', 'permissions': ['template.read']},
]


@pytest.mark.django_db()
class TestRolePermissions:
    def test_expand_wildcards(self):
        assert expand_permissions(['template.*']) == {p for p in Permission if p.startswith('template.')}
        assert expand_permissions(['design.*']) == {p for p in Permission if p.startswith('design.global.')}
        assert expand_permissions(['unknown.permission', 'unknown.*']) == set()

    def test_project_wildcard_excludes_access_all_projects(self):
        perms = expand_permissions(['project.*'])
        assert Permission.ADMIN_ACCESS_ALL_PROJECTS not in perms
        assert Permission.ARCHIVE_ALWAYS_ADD_ARCHIVING_KEY_TO_PROJECT not in perms
        assert Permission.PROJECT_RESTORE in perms

    @pytest.mark.parametrize(('user_kwargs', 'expected'), [
        ({'roles': []}, []),
        ({'roles': ['template_reader', 'designer']}, ['template.read', 'design.global.*']),
        ({'roles': ['project_all']}, ['project.*']),
        ({'roles': ['unknown_role', 'template_editor']}, ['template.*']),
        ({'roles': [], 'is_superuser': True, 'admin_permissions_enabled': True}, list(Permission)),
        ({'roles': [], 'is_superuser': True}, []),
        ({'roles': ['regular_user', 'project_admin'], 'is_system_user': True}, []),
        ({'roles': ['regular_user'], 'is_active': False}, []),
    ])
    @override_configuration(CUSTOM_USER_ROLES=CUSTOM_USER_ROLES)
    def test_effective_permissions(self, user_kwargs, expected):
        user = create_user(**user_kwargs)
        expected = expand_permissions(expected)
        assert set(user.effective_permissions) == expected
        for p in Permission:
            assert user.has_permission(p) == (p in expected)

    @override_configuration(CUSTOM_USER_ROLES=CUSTOM_USER_ROLES)
    def test_get_roles_with_permission(self):
        roles = get_roles_with_permission(Permission.TEMPLATE_READ)
        assert {'regular_user', 'template_editor', 'template_reader'}.issubset(set(roles))
        assert 'designer' not in roles
        assert get_role_permissions(['template_reader']) == {Permission.TEMPLATE_READ}

    @pytest.mark.parametrize(('custom_roles', 'valid'), [
        ([], True),
        (CUSTOM_USER_ROLES, True),
        ([{'id': 'regular_user', 'name': 'Override', 'permissions': []}], False),
        ([{'id': 'dup', 'name': 'A', 'permissions': []}, {'id': 'dup', 'name': 'B', 'permissions': []}], False),
    ])
    def test_validate_custom_roles(self, custom_roles, valid):
        try:
            validate_custom_roles(custom_roles)
            assert valid
        except Exception:
            assert not valid


@pytest.mark.django_db()
class TestRoleAssignment:
    @override_configuration(DEFAULT_USER_ROLES=['template_editor'])
    def test_default_roles_on_create(self):
        user = PentestUser.objects.create_user(username='new-default')
        assert user.roles == ['template_editor']

        manager = create_user(roles=['user_manager'])
        res = api_client(manager).post(reverse('pentestuser-list'), data={'username': 'new-api', 'email': 'new-api@example.com', 'password': 'Sup3rS3cret!Password'})
        assert res.status_code == 201, res.data
        assert res.data['roles'] == ['template_editor']

    def test_assign_unknown_role(self):
        manager = create_user(roles=['user_manager'])
        target = create_user()
        res = api_client(manager).patch(reverse('pentestuser-detail', kwargs={'pk': target.pk}), data={'roles': ['unknown_role']})
        assert res.status_code == 400
        target.refresh_from_db()
        assert target.roles == ['regular_user']

    @override_configuration(CUSTOM_USER_ROLES=CUSTOM_USER_ROLES)
    def test_assign_custom_role(self):
        manager = create_user(roles=['user_manager'])
        target = create_user()
        res = api_client(manager).patch(reverse('pentestuser-detail', kwargs={'pk': target.pk}), data={'roles': ['template_reader', 'template_reader']})
        assert res.status_code == 200
        assert res.data['roles'] == ['template_reader']
        assert res.data['effective_permissions'] == ['template.read']

    def test_regular_user_cannot_assign_roles(self):
        user = create_user()
        res = api_client(user).patch(reverse('pentestuser-detail', kwargs={'pk': 'self'}), data={'roles': ['regular_user', 'project_admin']})
        assert res.status_code in [200, 403]
        user.refresh_from_db()
        assert user.roles == ['regular_user']

    def test_settings_roles(self):
        res = api_client(create_user()).get(reverse('publicutils-settings'))
        role_ids = [r['id'] for r in res.data['permissions']['roles']]
        assert set(PREDEFINED_USER_ROLES.keys()).issubset(role_ids)
        assert all(r['description'] for r in res.data['permissions']['roles'] if r['is_predefined'])
        assert res.data['permissions']['default_user_roles'] == ['regular_user']

        # Public API returns expanded permissions (not wildcards)
        by_id = {r['id']: r for r in res.data['permissions']['roles']}
        assert 'template.*' not in by_id['template_editor']['permissions']
        assert set(by_id['template_editor']['permissions']) == {p.value for p in expand_permissions(['template.*'])}
        assert 'project.*' not in by_id['regular_user']['permissions']
        assert Permission.PROJECT_READ.value in by_id['regular_user']['permissions']


@pytest.mark.django_db()
class TestOnlyPermitted:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.user_other = create_user()
        self.project_other = create_project(members=[self.user_other])
        self.template = create_template()
        self.design_global = create_project_type()
        self.design_private_other = create_project_type(linked_user=self.user_other)

    def test_projects(self):
        user = create_user(roles=['regular_user'])
        project_own = create_project(members=[user])
        assert set(PentestProject.objects.only_permitted(user)) == {project_own}

        project_admin = create_user(roles=['project_admin'])
        assert {self.project_other, project_own}.issubset(set(PentestProject.objects.only_permitted(project_admin)))

    @override_configuration(CUSTOM_USER_ROLES=CUSTOM_USER_ROLES)
    def test_project_wildcard_does_not_grant_access_to_all_projects(self):
        user = create_user(roles=['project_all'])
        assert self.project_other not in PentestProject.objects.only_permitted(user)
        res = api_client(user).get(reverse('pentestproject-detail', kwargs={'pk': self.project_other.pk}))
        assert res.status_code == 404

    def test_templates(self):
        assert self.template in FindingTemplate.objects.only_permitted(create_user(roles=['regular_user']))
        assert not FindingTemplate.objects.only_permitted(create_user(roles=[])).exists()

    @override_configuration(CUSTOM_USER_ROLES=CUSTOM_USER_ROLES)
    def test_project_read_required(self):
        user = create_user(roles=['project_editor_without_read'])
        project = create_project(members=[user])
        design_project = create_project_type(source=SourceEnum.CUSTOMIZED, linked_project=project)
        assert not PentestProject.objects.only_permitted(user).exists()
        assert design_project not in ProjectType.objects.only_permitted(user)
        client = api_client(user)
        assert client.get(reverse('pentestproject-detail', kwargs={'pk': project.pk})).status_code == 403
        assert client.get(reverse('section-list', kwargs={'project_pk': project.pk})).status_code in [403, 404]
        assert client.post(reverse('pentestproject-list'), data={'name': 'New', 'project_type': self.design_global.pk}).status_code == 403

    @override_configuration(CUSTOM_USER_ROLES=CUSTOM_USER_ROLES)
    def test_access_all_projects_requires_project_read(self):
        user = create_user(roles=['project_editor_without_read', 'project_admin'])
        assert self.project_other in PentestProject.objects.only_permitted(user)

    @override_configuration(ENABLE_PRIVATE_DESIGNS=True, CUSTOM_USER_ROLES=CUSTOM_USER_ROLES)
    def test_designs(self):
        user = create_user(roles=['project_reader'])
        design_private = create_project_type(linked_user=user)
        project = create_project(members=[user])
        design_project = create_project_type(source=SourceEnum.CUSTOMIZED, linked_project=project)
        design_project_other = create_project_type(source=SourceEnum.CUSTOMIZED, linked_project=self.project_other)
        designs = set(ProjectType.objects.only_permitted(user))
        assert design_private in designs
        assert design_project in designs
        assert design_project_other not in designs
        assert self.design_global not in designs
        assert self.design_private_other not in designs

        user_reader = create_user(roles=['regular_user'])
        assert self.design_global in ProjectType.objects.only_permitted(user_reader)

    @override_configuration(ENABLE_PRIVATE_DESIGNS=False)
    def test_private_designs_disabled(self):
        user = create_user(roles=['designer'])
        design_private = create_project_type(linked_user=user)
        assert design_private not in ProjectType.objects.only_permitted(user)

    @override_configuration(ENABLE_PRIVATE_DESIGNS=True)
    def test_private_design_without_permissions(self):
        user = create_user(roles=[])
        res = api_client(user).post(reverse('projecttype-list'), data={'name': 'Private', 'scope': 'private'})
        assert res.status_code == 201
        res = api_client(user).post(reverse('projecttype-list'), data={'name': 'Global', 'scope': 'global'})
        assert res.status_code == 403

    @override_configuration(CUSTOM_USER_ROLES=CUSTOM_USER_ROLES)
    def test_users(self):
        user = create_user(roles=['template_reader'])
        member = create_user()
        create_project(members=[user, member])
        visible_users = set(PentestUser.objects.only_permitted(user))
        assert {user, member}.issubset(visible_users)
        assert self.user_other not in visible_users
        assert self.user_other in PentestUser.objects.only_permitted(create_user(roles=['regular_user']))
