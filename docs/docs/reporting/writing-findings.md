# Writing Findings

## Locking of Findings
When multiple pentesters are working simultanuously on a finding, there is the danger that one pentester overwrites changes of the other pentester.  
Findings are therefore locked while one pentester is working on them.

![Locked issue while pentester is editing](/images/john-is-editing.png)

As soon as the pentester closes the tab or switches to another issue, the lock will be release. In case of a sudden network interruption, the lock will be released after five minutes of inactivity. Note that in this case, unsaved data might be overwritten.