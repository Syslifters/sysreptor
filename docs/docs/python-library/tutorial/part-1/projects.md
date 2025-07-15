# Interacting with SysReptor projects

```python title="Initialize reptor" 
import os

from reptor import Reptor

reptor = Reptor(
    server=os.environ.get("REPTOR_SERVER"),
    token=os.environ.get("REPTOR_TOKEN"),
)
```

Use the [Projects API](/python-library/api/projects.md) to interact with your SysReptor projects and findings.

```python title="Search projects"
reptor.api.projects.search()  # Get all projects
reptor.api.projects.search(search_term="Web")  # Search for "Web"
reptor.api.projects.search(finished=False)  # Include active projects only
# Out: [ProjectOverview(name="Calzone Report Demo", id="41c09e60-44f1-453b-98f3-3f1875fe90fe")]
```

The search endpoint returns a list of [ProjectOverview](/python-library/dataclasses/project.md#reptor.models.Project.ProjectOverview) objects, which don't hold findings or section information (such as report fields).

```python title="Get data from ProjectOverview"
project_overview = reptor.api.projects.search()[0]
project_overview.id
# Out: 41c09e60-44f1-453b-98f3-3f1875fe90fe
project_overview.name
# Out: Calzone Report Demo
project_overview.tags
# Out: ['web', 'important']
project_overview.members
# Out: [User(username="reptor-user-test", name="John Doe", email="", id="ed4196c7-f60a-48bf-8119-dc1642946231")]
project_overview.findings
# Out: https://example.sysre.pt/api/v1/pentestprojects/41c09e60-44f1-453b-98f3-3f1875fe90fe/findings
project_overview.sections
# Out: https://example.sysre.pt/api/v1/pentestprojects/41c09e60-44f1-453b-98f3-3f1875fe90fe/sections
```

You can convert data data classes to Python dictionaries (or check the data class definitions, like [ProjectOverview](/python-library/dataclasses/project.md#reptor.models.Project.ProjectOverview)).

```python title="Convert ProjectOverview to dict"
my_project.to_dict()
# Out:
# {'id': '41c09e60-44f1-453b-98f3-3f1875fe90fe',
#  'copy_of': None,
#  'created': '2023-09-21T00:00:01Z',
#  'details': 'https://example.sysre.pt/api/v1/pentestprojects/41c09e60-44f1-453b-98f3-3f1875fe90fe',
#  'findings': 'https://example.sysre.pt/api/v1/pentestprojects/41c09e60-44f1-453b-98f3-3f1875fe90fe/findings',
#  'images': 'https://example.sysre.pt/api/v1/pentestprojects/41c09e60-44f1-453b-98f3-3f1875fe90fe/images',
#  'imported_members': [],
#  'language': 'en-US',
# <snip>
```

If you want to interact with a specific project, specify the project id when initializing `reptor`.  
(Instead of re-initializing reptor with the project ID, you can also call `reptor.api.projects.init_project("41c09e60-44f1-453b-98f3-3f1875fe90fe")`.)

```python title="Access information from specific project"
reptor = Reptor(
    server=os.environ.get("REPTOR_SERVER"),
    token=os.environ.get("REPTOR_TOKEN"),
    project_id="41c09e60-44f1-453b-98f3-3f1875fe90fe",
)
my_project = reptor.api.projects.fetch_project()
my_project.id
# Out: 41c09e60-44f1-453b-98f3-3f1875fe90fe
my_project.name
# Out: Calzone Report Demo
my_project.findings
# Out:
# [Finding(title="Reflected XSS", id="3014d72f-6edd-48a8-907b-a15a363f4fce"),
#  Finding(title="XML External Entity Injection (XXE)", id="b8917e5b-e087-44fb-8461-e9de511d2117"),
#  Finding(title="Stored Cross-Site Scripting (XSS)", id="5fb537e6-385b-4c15-9f18-4c319c6e625e"),
#  Finding(title="Cross-Site Request Forgery (CSRF)", id="9a5f580f-bfa5-4ab1-b9e4-daee0bf5fff2"),
# <snip>
my_project.sections
# Out:
# [Section(id="executive_summary"),
#  Section(id="scope"),
#  Section(id="customer"),
#  Section(id="other"),
#  Section(id="appendix")]
my_project.sections[1].data.duration
# Out: SectionDataField(name="duration", type="string", value="5 person days")
```

You can, again, convert the data objects ([Project](/python-library/dataclasses/project.md#reptor.models.Project.Project) and [Section](/python-library/dataclasses/section.md#reptor.models.Section.Section)) to Python dictionaries.

```python title="Convert Project and Section to dict"
my_project.to_dict()
# Out:
# {'id': '41c09e60-44f1-453b-98f3-3f1875fe90fe',
#  'created': '2023-09-21T00:00:01Z',
#  'details': 'https://reptortest.sysre.pt/api/v1/pentestprojects/41c09e60-44f1-453b-98f3-3f1875fe90fe',
#  'findings': [{'assignee': None,
#                'created': '2025-07-09T08:02:10.017137Z',
#                'data': {'affected_components': ['https://example.com/alert(1)',
#                                                 'https://example.com/q=alert(1)'],
# <snip>
my_project.sections[1].to_dict()
# Out:
# {'assignee': None,
#  'created': '2022-10-19T16:59:04.488000Z',
#  'data': {'duration': '5 person days',
#           'end_date': '2022-04-22',
#           'provided_users': 'Duis autem vel eum iriure dolor in hendrerit in '
# <snip>
```

Pentesters write their reports in markdown. If you need the data as HTML, you can use the `html` parameter.  
(Note that the method still returns JSON data. Markdown content is, however, converted to HTML.)

```python title="Download fields as HTML instead of Markdown"
my_project = reptor.api.projects.fetch_project(html=True)
my_project.findings[0].data.description.value
# Out: '<p>This was originally written in markdown.</p> \n<ul>\n<li>Now</li> <li>it seems</li> <li>to be</li> <li>HTML</li>\n</ul>\n'
```

<div style="display: flex; justify-content: flex-end;">
  <span><a href="../../part-2/findings">Next: Interacting with SysReptor findings →</a></span>
</div>