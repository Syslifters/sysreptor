---
grammarly: false
---
# AD Privileged Access Strategy
## Description

The Privileged Access strategy is part of an overall strategy for access control in an enterprise. The Enterprise Access Model shows how privileged access can be securely managed in an enterprise. 

![Enterprise Access Model](/images/user-app-control-management-data-workload-planes.png)
Source: https://learn.microsoft.com/en-us/security/compass/media/privileged-access-strategy/user-app-control-management-data-workload-planes.png

The applications and data of an organisation usually store a large part of the company's value. This information, which requires special protection, is held in the **Data/Workload Plane** in the Enterprise Access Model. 

The **Management Plane** comprises the infrastructure that provides the applications and data of the Data/Workload Plane. Management is the responsibility of the corporate IT organisation, whether hosted on-premise, in Azure or with a third-party cloud provider.

Providing consistent access control for these systems across the enterprise requires a **Control Plane**. This is based on centralised identity management systems, complemented by network access controls.

For these systems to add operational value, they must be accessible to internal users, suppliers and customers, e.g. via their workstations or other devices (access via **User Access**). Application programming interfaces (APIs) are also often necessary for process automation, creating access paths through applications (**App Access**).

Finally, these systems need to be managed by IT staff, developers or other company employees. This leads to privileged access paths (**Privileged Access**). These access paths are particularly critical and should be strictly protected against compromise.

## Recommendation
We recommend implementing a privileged access strategy as part of an overall access control strategy in an organization based on the enterprise access model.