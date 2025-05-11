# NBA CO-PO Template Components

This directory contains reusable components for the NBA CO-PO mapping application templates.

## Structure

- `_components/`: Directory containing all reusable components
  - `head.html`: Common head content including CSS variables and styles
  - `navbar.html`: Navigation component with active page highlighting
  - `footer.html`: Common footer component
  - `scripts.html`: Common JavaScript functionality
- `layout.html`: Base layout template that includes all components

## How to Use

To use these components in a new page:

1. Create a new template file that extends the layout:

```html
{% extends "layout.html" %} {% set active_page = 'page_name' %} {% block title
%}Page Title | NBA CO-PO{% endblock %} {% block content %}
<!-- Page-specific content goes here -->
{% endblock %} {% block additional_head %}
<!-- Additional page-specific styles -->
{% endblock %} {% block additional_scripts %}
<!-- Additional page-specific scripts -->
{% endblock %}
```

2. The `active_page` variable is used to highlight the current page in the navbar.

3. You can add page-specific content in the respective blocks.

## Benefits

- Consistent styling across all pages
- Centralized component management
- Easier maintenance and updates
- Reduced code duplication
