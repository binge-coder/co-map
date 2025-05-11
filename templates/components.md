# Common Components for NBA CO-PO Mapping Application

This document provides guidance on common components that should be reused across templates for consistent UI.

## CSS Variables

```css
:root {
  --primary: #4361ee;
  --secondary: #3ccfcf;
  --dark: #121212;
  --darker: #0a0a0a;
  --light: #f8f9fa;
  --accent: #f72585;
  --gradient-start: #4361ee;
  --gradient-end: #3ccfcf;
  --text-primary: #e1e1e1;
  --text-secondary: #b0b0b0;
  --card-bg: rgba(255, 255, 255, 0.04);
  --card-border: rgba(255, 255, 255, 0.08);
}
```

## Common Font Imports

```html
<link
  href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap"
  rel="stylesheet"
/>
```

## Navbar Component

```html
<nav class="navbar navbar-expand-lg navbar-dark">
  <div class="container">
    <a class="navbar-brand" href="/">
      <i class="fas fa-chart-line me-2"></i>NBA CO-PO
    </a>
    <button
      class="navbar-toggler"
      type="button"
      data-bs-toggle="collapse"
      data-bs-target="#navbarNav"
    >
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <a
            class="nav-link {% if active_page == 'home' %}active{% endif %}"
            href="/"
          >
            <i class="fas fa-home me-1"></i> Home
          </a>
        </li>
        <li class="nav-item">
          <a
            class="nav-link {% if active_page == 'downloads' %}active{% endif %}"
            href="/downloads"
          >
            <i class="fas fa-download me-1"></i> Downloads
          </a>
        </li>
        <!-- Add other navigation items as needed -->
      </ul>
    </div>
  </div>
</nav>
```

## Footer Component

```html
<footer class="footer">
  <div class="container">
    <div class="row align-items-center">
      <div class="col-md-6 text-center text-md-start mb-3 mb-md-0">
        <p class="mb-0">© 2025 NBA CO-PO Mapping Automation Tool</p>
      </div>
      <div class="col-md-6 text-center text-md-end">
        <div>
          <a href="/" class="footer-link me-3">Home</a>
          <a href="/downloads" class="footer-link me-3">Downloads</a>
          <a href="/co-po-pso-mapping" class="footer-link">Mapping</a>
        </div>
      </div>
    </div>
  </div>
</footer>
```

## Common JavaScript

```javascript
// Navbar scroll effect
window.addEventListener("scroll", function () {
  const navbar = document.querySelector(".navbar");
  if (window.scrollY > 30) {
    navbar.classList.add("scrolled");
  } else {
    navbar.classList.remove("scrolled");
  }
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    document.querySelector(this.getAttribute("href")).scrollIntoView({
      behavior: "smooth",
    });
  });
});
```

## Implementation with Jinja2

To implement the reuse of components in a Flask/Jinja2 application, you could create the following structure:

1. Create a `layout.html` that includes all common elements
2. Create separate files for components in a `_components` directory
3. Use Jinja2 includes and blocks for templating

Example layout.html:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{% block title %}NBA CO-PO Mapping{% endblock %}</title>
    <!-- Common CSS and JS imports -->
    {% include '_components/head.html' %} {% block additional_head %}{% endblock
    %}
  </head>
  <body>
    {% include '_components/navbar.html' %} {% block content %}{% endblock %} {%
    include '_components/footer.html' %}

    <!-- Common scripts -->
    {% include '_components/scripts.html' %} {% block additional_scripts %}{%
    endblock %}
  </body>
</html>
```

Then each page would simply extend the layout:

```html
{% extends "layout.html" %} {% block title %}Downloads | NBA CO-PO{% endblock %}
{% block content %}
<!-- Page-specific content -->
{% endblock %}
```
