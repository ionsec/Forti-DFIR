.. _contributing:

Contributing Guide
==================

We welcome contributions to Forti-DFIR!

Getting Started
---------------

1. Fork the repository on GitHub
2. Clone your fork locally

   .. code-block:: bash

      git clone https://github.com/YOUR_USERNAME/Forti-DFIR.git
      cd Forti-DFIR

3. Create a virtual environment

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate
      pip install -r requirements.txt

4. Create a feature branch

   .. code-block:: bash

      git checkout -b feature/my-new-feature

Development Setup
-----------------

Backend Development
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd web_app/backend
   pip install -r requirements-dev.txt
   pip install -e .

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/ -v --cov=web_app/backend

Code Style
~~~~~~~~~~

We use the following tools:

- **ruff** for linting
- **black** for formatting
- **mypy** for type checking

.. code-block:: bash

   pip install ruff black mypy
   ruff check .
   black .
   mypy web_app/backend

Frontend Development
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd web_app/frontend
   npm install
   npm test
   npm run build

Pull Request Process
--------------------

1. **Create an issue** first for major changes
2. **Write tests** for new functionality
3. **Update documentation** for changed behavior
4. **Follow the PR template** when submitting

Code Review Checklist
~~~~~~~~~~~~~~~~~~~~~

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

Reporting Bugs
--------------

When reporting bugs, please include:

1. **Operating system** and version
2. **Python version** (``python --version``)
3. **Steps to reproduce** the issue
4. **Expected behavior**
5. **Actual behavior**
6. **Log output** (if applicable)
7. **Screenshots** (if applicable)

Feature Requests
----------------

For feature requests, please provide:

1. **Use case**: Why is this feature needed?
2. **Proposed solution**: How should it work?
3. **Alternatives**: Other solutions considered
4. **Priority**: How important is this feature?

Security Issues
---------------

For security vulnerabilities, please:

- **DO NOT** open a public issue
- Email: security@ionsec.com
- Include: Description, steps to reproduce, potential impact
- Allow 90 days for fix before disclosure

Code of Conduct
---------------

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards other community members

License
-------

By contributing, you agree that your contributions will be licensed under the project's license.
