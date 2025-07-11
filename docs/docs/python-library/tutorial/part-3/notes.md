# Interacting with SysReptor notes

The `reptor` library also allows you to interact with your notes structures.

Use the notes API to get the full project notes structure.

```python title="Get project notes"
notes = reptor.api.notes.get_notes()
# Out:
# [Note(title="Scoping", id="c90dbe1b-3ea7-4054-925d-c4c55b8d7404", parent="None"),
#  Note(title="Findings", id="38779b8f-a910-4191-8e0d-066f6b79cd95", parent="None")
#  Note(title="Web Security Checklist", id="c052da53-0b2e-401e-973d-3c1c92255b77", parent="None"),
#  Note(title="Session management", id="3e0cb97f-23a9-470d-a885-68cd9dbb5ada", parent="c052da53-0b2e-401e-973d-3c1c92255b77"),
#  <snip>
notes[0].title
# Out: 'Scoping'
notes[0].text
# Out: 'Those are our scoping notes.'
notes[0].icon_emoji
# Out: '🧐'
```

We can also create notes. Let's add a new item to our "Web Security Checklist".

```python title="Add a new note"
reptor.api.notes.create_note(
    title="Authorizations",
    parent_id="c052da53-0b2e-401e-973d-3c1c92255b77",
    checked=False,
    text="Check for authorization issues."
)
# Out: Note(title="Authorizations", id="dda820d2-57d7-4ff8-b4ac-99d102a5c8bf", parent="c052da53-0b2e-401e-973d-3c1c92255b77")
```

![A new note was added to the project notes](/images/created_note.png)

Use the `write_note` method to append text to your note, or to update properties like the `title`, `checked` or `icon_emoji`.

```python title="Update the note"
reptor.api.notes.write_note(
    id="dda820d2-57d7-4ff8-b4ac-99d102a5c8bf",
    title="Authorizations (Done)",
    text="Done by John Doe.",
    checked=True,
)
```

We can also use the library to upload files or images.

```python title="Upload files and images"
reptor.api.notes.upload_file(
    note_id="dda820d2-57d7-4ff8-b4ac-99d102a5c8bf",
    file=open("evidence.tar.gz", "rb"),
    filename="evidence.tar.gz",
    caption="Evidence for authorization testing.",
)
reptor.api.notes.upload_file(
    note_id="dda820d2-57d7-4ff8-b4ac-99d102a5c8bf",
    file=open("reptor.png", "rb"),
    filename="reptor.png",
    caption="Self Portrait.",
)
```

![The note was updated with additional text and files](/images/updated_note.png)

Let's download the note as PDF and save it to a file.

```python title="Download note as PDF and save to file"
with open("note.pdf", "wb") as f:
    f.write(
        reptor.api.notes.render(id="dda820d2-57d7-4ff8-b4ac-99d102a5c8bf")
    )
```

We can also duplicate or delete our notes.

```python title="Duplicate and delete note"
reptor.api.notes.duplicate(id="dda820d2-57d7-4ff8-b4ac-99d102a5c8bf")
# Out: Note(title="Authorizations (Done)", id="a1a1fd38-0c8e-4b42-b491-74cb61ed2d7f", parent="c052da53-0b2e-401e-973d-3c1c92255b77")
reptor.api.notes.delete_note(id="a1a1fd38-0c8e-4b42-b491-74cb61ed2d7f")
```

<div style="display: flex; justify-content: flex-start;">
  <span><a href="../../part-2/findings">← Previous: Interacting with SysReptor findings</a></span>
</div>