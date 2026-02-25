### Micro Ocr

This ERPNext app is designed to streamline resume data extraction and management. It leverages advanced OCR and NLP techniques to automatically parse resumes, identify key information, and store it in structured formats within ERPNext. The app reduces manual effort, improves accuracy, and ensures that HR teams can quickly access candidate details for recruitment workflows.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app micro_ocr
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/micro_ocr
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
