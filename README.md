# EKG Store

`Alpha`

## Running
Setting up the development environment:

### 1. Requirements
> Skip the requirements that you already have.

- Install/Update to `Python 3.5`. To save our souls from Unicode incompatibilities, we use `Python 3`. Use `homebrew` on OSX and your system package manager on Linux. You can use `chocolatey` on Windows as well.
- Install Python packages. Run: `pip install -r requirements.txt` from module's root directory. Make sure `pip` is targetting to `python3`, or use `pip3` instead.
- Install Inkscape and make sure it is in your system `PATH`. On OSX, you can use `brew cask install inkscape`, while on other systems please follow the official documentation.

### 2. Using the commandline arguments to run the demo
There is a demo script, very creatively named `demo.py` in the module root, which you may use to test the environment on your system. To execute, run:

```shell
python3 demo.py

# Specify a file
python3 demo.py <some pdf file>.pdf
```

## Collaboration
### Working on new features
Please ensure you create your new feature branch for any changes you make in code. After you're done, open a pull request to merge to master branch. Please *never* push directly on `master`.

### Coding Standards
We try to closely follow PEP8 coding guidelines with following exceptions:
- Indentation is strictly 2-space. Please do not use `tabs` or 4-space indents.
- Single letter, or nondescriptive variable names are prohibited unless they are used within loops, comprehensions, or lambda functions.
- Lines can be up to 120 characters long. Anything longer than that, you should immediately consider refactoring.
- Long functional chains are allowed, but each atomic call must be in a separate line with double hanging indent. Example:
```python
# Good
text_anchor_els = (self.svg
    .find('path')
    .parent()
    .next('g')
    .find('text'))

# Bad - Single hanging Indent
text_anchor_els = (self.svg
  .find('path')
  .parent()
  .next('g')
  .find('text'))

# Worse - Long chain
text_anchor_els = self.svg.find('path').parent().next('g').find('text')
```
- Do not use _obvious_ variable names that derive from their type. Example:
```python
# No!
element_list = [...]
# Instead use
elements = [...]
```

### Resources
- PEP 8 reference: https://www.python.org/dev/peps/pep-0008/
- Python 3 docs: https://docs.python.org/3/
- Python 2 and Python 3 differences: https://wiki.python.org/moin/Python2orPython3
- Inkscape commandline reference: https://inkscape.org/en/doc/inkscape-man.html
- Python 3 tutorials: http://docs.python-guide.org/en/latest/
