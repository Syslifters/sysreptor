# Locking of Findings and Sections
When multiple pentesters are working simultanuously on section, one pentester might overwrite changes of the other pentester.  
Therefore, we lock sections while one pentester is working on them.

<figure markdown>
  ![Locked issue while pentester is editing](/images/john-is-editing.png){ width="250" }
  <figcaption>Locked issue while pentester is editing</figcaption>
</figure>

As soon as the pentester closes the tab or switches to another issue, the lock releases. In case of a sudden network interruption, we release the lock after 90 seconds of inactivity. Note that in this case, unsaved data might be overwritten.

We also lock sections if a pentester tries to edit a finding in a second tab. This might also lead to data loss if he overwrites previously written content. In this case, the pentester can claim the lock by hitting "Edit Anyway".

<figure markdown>
  ![Claim the lock](/images/edit-anyway.png){ width="400" }
  <figcaption>Claim the lock</figcaption>
</figure>

