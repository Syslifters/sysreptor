# Charts
Charts can be embedded into reports with a `<chart>` component.
The `<chart>` component uses [ChartJS](https://www.chartjs.org/docs/latest/){ target=_blank } for rendering charts.
The resulting chart is embedded as an image in the PDF.

How the chart looks like is specified by the `:config` argument. This argument accepts a [ChartJS config object](https://www.chartjs.org/docs/latest/configuration/){ target=_blank }.
You can configure different chart types (e.g. pie chart, bar chart, line chart, etc.), chart styling, labels.
The `config` also takes the datasets to be rendered in the `data` property.

You can use all available ChartJS configuration options (except animations, since they are not possible in PDFs) to customize charts for your needs.

Other options:

* `width`: Width of the chart in centimeter
* `height`: Height of the chart in centimeter

## Example: Bar Chart of vulnerability risks
The following charts shows the number of vulnerabilities for each risk level (none, low, medium, high, critical) in a bar chart.
Each risk level bar has a different color.

```html
<figure>
  <chart :width="15" :height="10" :config="{
    type: 'bar', 
    data: {
       labels: ['Critical', 'High', 'Medium', 'Low', 'None'],
       datasets: [{
         data: [
           finding_stats.count_critical,
           finding_stats.count_high,
           finding_stats.count_medium,
           finding_stats.count_low,
           finding_stats.count_info
         ],
         backgroundColor: ['#e21212', '#eb6020', '#cf8e2b', '#4d82a8', '#2d5f2e'],
       }]
    },
    options: {scales: {y: {beginAtZero: true, ticks: {precision: 0}}}, plugins: {legend: {display: false}}}
  }" />
  <figcaption>Distribution of vulnerabilities</figcaption>
</figure>
```


## Plugins
ChartJS supports plugins to extend the functionality of charts. 
We provide following plugins:
* [chartjs-plugin-datalabels](https://chartjs-plugin-datalabels.netlify.app/guide/getting-started.html#configuration){ target=_blank }: Show labels on top of bars, lines, etc.

Plugins are disabled by default. You can enable them using the `plugins` option in the `config` object of charts.

```html
<chart :config="{
  plugins: [ chartjsPlugins.DataLabels ]
}" />
```