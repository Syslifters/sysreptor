# Findings

## Findings List

Findings are available in Vue templates via the `findings` variable.
The `findings` list is an ordered list of all findings. 
Each finding is represented as a JSON object containing finding fields (see [Field Types](/designer/field-types.md)).

Iterate over the `findings` list via Vue `v-for` loops:
```html
<section>
  <h1 class="in-toc numbered">Findings</h1>
  <div v-for="finding in findings">
    <h2 :id="finding.id" class="in-toc numbered">{{ finding.title }}</h2>
    ...
    <pagebreak />
  </div>
</section>
```

## Finding Order
Findings can be ordered based on specific finding fields.
Finding fields used for ordering are defined in the design's finding field definition.
The default sort order is to first sort findings by cvss in descending order, followed by title in ascending order.

The `findings` variable provided in Vue templates is already ordered.

![Finding Ordering Definition](/images/finding-order-definition.png)

If no fields are specified for ordering, findings can be manually sorted using drag-and-drop functionality.
The order of findings can be customized in projects by overriding the default sort order via manually sorting findings via drag-and-drop.

![Custom Finding Order](/images/finding-order-manual.png)



## Finding Groups

Findings can be grouped based on a specified field, which divides the list into virtual groups. 
By default, findings are not grouped.
It is recommended to group findings using a field of type `combobox` or `enum` (see [Field Types](/designer/field-types.md)).
`combobox` fields allow users to add custom groups when writing reports, while `enum` fields require all groups to be defined upfront in the design.

![Finding Grouping Definition](/images/finding-group-definition.png)

The order of these groups is determined by sorting the selected grouping field in either ascending or descending order. 
Within each group, findings follow the finding ordering rules. 
The order of both findings and groups can be adjusted at the project level by manually sorting findings and groups via drang-and-drop. 

![Custom Finding Group Order](/images/finding-group-manual.png)

Designs need to support grouping in the Vue template. The grouped finding list is availalbe via the `finding_groups` variable.

```html
<section v-for="group in finding_groups">
  <h1 class="in-toc numbered">{{ group.label }}</h1>
  <div v-for="finding in group.findings">
    <h2 :id="finding.id" class="in-toc numbered">{{ finding.title }}</h2>
    ...
    <pagebreak />
  </div>
</section>
```

