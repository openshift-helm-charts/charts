# Pull Request

## Content of PR

When users submit pull requests, the PR content should be either chart related
or non-chart related.  Combining changes related to both chart and non-chart in
the same PR is not allowed.  (TBD: Need clarity about OWNERS file) A PR making
changes to a chart may contain a chart and/or report.  The chart could be either
a tarball or extracted form.

## Authorized Pull Request

When a pull request passes all checks, the PR will get `authorized-request` as a
label.  Along with this, the bot will add a comment with a few generic
information.  The comment also includes a particular metadata line with the
vendor label and chart name.  The metadata line will start with `/metadata` as a
prefix to avoid ambiguity when parsing the comment. Here is an example metadata
line:

```
/metadata {"vendor_label": "label", "chart_name": "name"}
```

The metadata line should meet the following requirements:

1. The whole metadata content will be in a single line
2. The line starts with `/metadata` (space character is allowed before `/metadata`)
3. After the JSON content, only space is allowed before the line end
4. There will take at least one space immediately after `/metadata`
