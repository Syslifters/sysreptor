# Interacting with SysReptor findings

Now let us look at how to add data to projects. Let's create a finding.

```python title="Create finding"
finding = {
    "status": "in-progress",
    "data": {
        "title": "Test Finding",
        "description": "This is a test finding.",
        "affected_components": ["example.com", "example-1.com"],
    },
}
my_finding = reptor.api.projects.create_finding(finding)
my_finding
# Out: FindingRaw(title="Test Finding", id="33ddc5f3-7396-4076-8c17-3eee16465840")
```

The finding dictionary consists of metadata (like `status`, `assignee`, etc.) and the actual finding data (your finding fields). Add the data you want to add to your finding fields into the `data` dictionary. The keys map to the finding IDs from your project designs.

Now let's update the finding that we just created. The FindingRaw object has an ID that we can use for referencing the finding that we want to update.  
We'll just fill out the `summary` field and change the `status` to `finished`.

```python title="Update the finding we just created"
my_finding = reptor.api.projects.update_finding(
    my_finding.id,
    {
        "status": "finished",
        "data": {
            "summary": "My summary",
        }
    }
)
```

The `update_finding` method returns the updated FindingRaw objects.

We can use the FindingRaw object to duplicate our finding...

```python title="Duplicate finding"
duplicated_finding = reptor.api.projects.create_finding(
    my_finding.to_dict()
)
```

...and to delete it.

```python title="Delete finding"
reptor.api.projects.delete_finding(duplicated_finding.id)
```

We can also create new findings from finding templates. For this, we introduce the `template` API.  
Searching for finding templates works the same way as searching for projects.

```python title="Search finding templates"
reptor.api.templates.search()  # Get all finding templates
reptor.api.templates.search(search_term="XSS")  # Search for "XSS"
# Out:
# [FindingTemplate(title="Stored Cross-Site Scripting (XSS)", id="2bfc61fe-7003-4c95-8e2d-322cc3206a7a"),
#  FindingTemplate(title="Insecure HTTP cookies", id="3d7491be-cf81-4d1c-82cd-d71451786f9f"),
#  FindingTemplate(title="Incorrectly configured HTTP security headers", id="e63df410-42f2-49ad-837c-0d6d343a040c")]
```

We now use the finding template ID to create a new finding from the template.

```python title="Create finding from templates"
reptor.api.projects.create_finding_from_template(
    template_id="2bfc61fe-7003-4c95-8e2d-322cc3206a7a"
)
# Out: FindingRaw(title="Stored Cross-Site Scripting (XSS)", id="79d2abd6-74f6-417a-878f-2d46fc78eef0")
```

We might also want to update report fields in our report sections.

![Sections and report fields](/images/sections.png)

We get access to available sections and report fields through the project.

```python title="Get available sections and report fields"
my_project.sections
# Out:
#[Section(id="executive_summary"),
# Section(id="scope"),
# Section(id="customer"),
# Section(id="other"),
# Section(id="appendix")]
my_project.sections[1].fields
# Out:
#['scope', 'start_date', 'end_date', 'duration', 'provided_users']
```

Use this data to update fields in the section `scope`.

```python title="Update report fields"
reptor.api.projects.update_section(
    "scope",
    {
        "start_date": "2025-08-01",
        "end_date": "2025-08-31",
        "duration": "5 person days"
    },
)
# Out: SectionRaw(id="scope")
```

As we now filled in all relevant data, we now want to download our rendered PDF report.

```python title="Render report and save as file"
with open("my_report.pdf", "wb") as f:
    f.write(reptor.api.projects.render())
```

Finally, we can finish, or delete our projects.

```python title="Finish or delete projects"
reptor.api.projects.finish_project()
# Out: True  # Indicates that the project is now finished/read only
reptor.api.projects.delete_project()
```

We can also duplicate projects.

```python title="Duplicate project"
reptor.api.projects.duplicate_project()
# Out: Project(name="Copy of Margherita Report Demo", id="2fe0ab2b-8482-49fa-a3b5-1d0d7bb49c01")
```

The `duplicate_project` method returns the newly created `Project`. If you now want to interact with that project, you need to re-initialize your `reptor` object.

```python title="Switch project after duplicate"
duplicate = reptor.api.projects.duplicate_project()
reptor.api.projects.init_project(duplicate.id)
```

If you want to duplicate a project to interact with it and want to clean it up right away, you can also use the contect manager `duplicate_and_cleanup`.  
The following code snippet duplicates the project, changes the design and renders the PDF. When leaving the context menu, the duplicated project is cleaned up.

```python title="Duplicate project and render with alternative design"
design_id = "9eb56f02-c71b-4c1a-8392-06ab4d633336"

with reptor.api.projects.duplicate_and_cleanup():
    reptor.api.projects.update_project_design(design_id, force=True)
    with open("my_report.pdf", "wb") as f:
        f.write(reptor.api.projects.render())
```

The `force` parameter in `update_project_design` forces the design change, even if there are incompatible field definitions (e.g., a `string` finding field in the original design, which is a `number` in the new design would lead to data loss). This makes duplicating the project useful, because incompatibilities won't affect the original project.

<div style="display: flex; justify-content: space-between;">
  <span><a href="../../part-1/projects">← Previous: Interacting with SysReptor projects</a></span>
  <span><a href="../../part-3/notes">Next: Interacting with SysReptor notes →</a></span>
</div>