# AI Agent

The AI agent assists with pentest report writing and analysis. It can answer questions about your project, suggest and review content, create and edit findings and sections.

To be able to use the agent, enable it in applications settings and configure an LLM provider (see [configuration](/setup/configuration#ai-agent)). Multiple LLM providers and also self-hosted models are supported.

![AI agent](/images/ai-agent.png)

The agent has access to project data through context and tools.

## Project scoping

The SysReptor AI agent is bound to the **current pentest project** only.

It **can**:

* Read that project's structure, report sections, findings, notes, and the project's design field definitions
* See which section, finding, or note you currently have open in the UI
* Search **finding templates** in the instance knowledge base (templates are shared, not limited to one project)

It **cannot**:

* Read or edit **other projects**
* Access other users' private data, instance admin settings, or findings and notes that belong to a different project


## Agent Mode

- **Ask**: Read-only. The agent can view the project and answer questions or suggest text. It does not create or edit any data; you copy and apply suggestions yourself.
- **Agent** (<BadgePro />): Full write access in this project. In addition to everything in Ask mode, the agent can create findings and notes and update section, finding, and note fields.


## Asking clarifying questions

When information is missing or there are multiple valid approaches, the agent can pause and ask you a multiple-choice question. Pick an option (or type your own answer) to continue, or send a new message to skip the question.


## Example Use Cases

- Generate executive summary from findings
- Generate finding recommendation from technical description
- Review texts for grammar and spelling
- Create findings from notes
- Analyze the report and ask questions about it
- and much more


