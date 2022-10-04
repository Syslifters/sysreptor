# Writing Findings

## Locking of Findings
When multiple pentesters are working simultanuously on a finding, there is the danger that one pentester overwrites changes of the other pentester.  
Findings are therefore locked while one pentester is working on them.

![Locked issue while pentester is editing](/images/john-is-editing.png)

As soon as the pentester closes the tab or switches to another issue, the lock will be release. In case of a sudden network interruption, the lock will be released after 90 seconds of inactivity. Note that in this case, unsaved data might be overwritten.

Findings are also locked if a pentester tries to edit a finding in a seconds tab. This might also lead to data loss by overwriting previously written content. In this case, the lock can be claimed by hitting "Edit Anyway".